import { supabase } from '../lib/supabase';
import { Streak, DailyAnalytics } from '../contexts/StreakContext';

interface StreakService {
  getCurrentStreak(): Promise<Streak>;
  updateStreak(): Promise<Streak>;
  getDailyAnalytics(startDate: string, endDate: string): Promise<DailyAnalytics[]>;
  calculateDailyAnalytics(date: string): Promise<DailyAnalytics>;
}

export const createStreakService = (): StreakService => {
  return {
    async getCurrentStreak(): Promise<Streak> {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('Not authenticated');

      // Try to get existing streak
      const { data: existingStreak, error: fetchError } = await supabase
        .from('streaks')
        .select('*')
        .eq('user_id', user.id)
        .eq('streak_type', 'daily')
        .single();

      if (fetchError && fetchError.code !== 'PGRST116') {
        throw fetchError;
      }

      // If no streak exists, create one
      if (!existingStreak) {
        const { data: newStreak, error: createError } = await supabase
          .from('streaks')
          .insert({
            user_id: user.id,
            current_streak: 0,
            longest_streak: 0,
            last_activity_date: new Date().toISOString().split('T')[0],
            total_days_active: 0,
            streak_type: 'daily'
          })
          .select()
          .single();

        if (createError) throw createError;
        return newStreak;
      }

      return existingStreak;
    },

    async updateStreak(): Promise<Streak> {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('Not authenticated');

      const today = new Date().toISOString().split('T')[0];
      
      // Get current streak
      const currentStreak = await this.getCurrentStreak();
      
      // Check if user completed tasks today
      const { data: completedToday, error: tasksError } = await supabase
        .from('tasks')
        .select('id')
        .eq('user_id', user.id)
        .eq('status', 'completed')
        .gte('completed_at', today + 'T00:00:00.000Z')
        .lt('completed_at', today + 'T23:59:59.999Z');

      if (tasksError) throw tasksError;

      const hasActivityToday = (completedToday?.length || 0) > 0;
      const lastActivityDate = new Date(currentStreak.last_activity_date);
      const todayDate = new Date(today);
      const daysDiff = Math.floor((todayDate.getTime() - lastActivityDate.getTime()) / (1000 * 60 * 60 * 24));

      let newCurrentStreak = currentStreak.current_streak;
      let newTotalDaysActive = currentStreak.total_days_active;

      if (hasActivityToday && currentStreak.last_activity_date !== today) {
        // User has activity today and hasn't been counted yet
        if (daysDiff === 1) {
          // Consecutive day - increment streak
          newCurrentStreak += 1;
        } else if (daysDiff > 1) {
          // Gap in activity - reset streak to 1
          newCurrentStreak = 1;
        }
        // If daysDiff === 0, already counted today

        newTotalDaysActive += 1;
      } else if (!hasActivityToday && daysDiff > 1) {
        // No activity today and gap from last activity - reset streak
        newCurrentStreak = 0;
      }

      const newLongestStreak = Math.max(currentStreak.longest_streak, newCurrentStreak);

      // Update streak in database
      const { data: updatedStreak, error: updateError } = await supabase
        .from('streaks')
        .update({
          current_streak: newCurrentStreak,
          longest_streak: newLongestStreak,
          last_activity_date: hasActivityToday ? today : currentStreak.last_activity_date,
          total_days_active: newTotalDaysActive,
          updated_at: new Date().toISOString()
        })
        .eq('id', currentStreak.id)
        .select()
        .single();

      if (updateError) throw updateError;
      return updatedStreak;
    },

    async getDailyAnalytics(startDate: string, endDate: string): Promise<DailyAnalytics[]> {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('Not authenticated');

      const { data, error } = await supabase
        .from('daily_analytics')
        .select('*')
        .eq('user_id', user.id)
        .gte('date', startDate)
        .lte('date', endDate)
        .order('date', { ascending: false });

      if (error) throw error;
      return data || [];
    },

    async calculateDailyAnalytics(date: string): Promise<DailyAnalytics> {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('Not authenticated');

      // Get all tasks for the date
      const { data: tasks, error: tasksError } = await supabase
        .from('tasks')
        .select('*')
        .eq('user_id', user.id)
        .eq('due_date', date);

      if (tasksError) throw tasksError;

      const totalPlannedMinutes = tasks?.reduce((sum, task) => sum + (task.estimated_minutes || 0), 0) || 0;
      const completedTasks = tasks?.filter(task => task.status === 'completed') || [];
      const totalCompletedMinutes = completedTasks.reduce((sum, task) => sum + (task.actual_minutes || task.estimated_minutes || 0), 0);
      
      const completionRate = tasks?.length ? (completedTasks.length / tasks.length) * 100 : 0;
      
      // Find most focused subject
      const subjectMinutes: { [key: string]: number } = {};
      completedTasks.forEach(task => {
        if (task.subject) {
          subjectMinutes[task.subject] = (subjectMinutes[task.subject] || 0) + (task.actual_minutes || task.estimated_minutes || 0);
        }
      });
      
      const mostFocusedSubject = Object.keys(subjectMinutes).length > 0 
        ? Object.keys(subjectMinutes).reduce((a, b) => subjectMinutes[a] > subjectMinutes[b] ? a : b)
        : undefined;

      // Check if analytics already exist for this date
      const { data: existingAnalytics } = await supabase
        .from('daily_analytics')
        .select('id')
        .eq('user_id', user.id)
        .eq('date', date)
        .single();

      const analyticsData = {
        user_id: user.id,
        date,
        total_planned_minutes: totalPlannedMinutes,
        total_completed_minutes: totalCompletedMinutes,
        total_tasks_planned: tasks?.length || 0,
        total_tasks_completed: completedTasks.length,
        completion_rate: completionRate,
        most_focused_subject: mostFocusedSubject
      };

      if (existingAnalytics) {
        // Update existing analytics
        const { data, error } = await supabase
          .from('daily_analytics')
          .update(analyticsData)
          .eq('id', existingAnalytics.id)
          .select()
          .single();

        if (error) throw error;
        return data;
      } else {
        // Create new analytics
        const { data, error } = await supabase
          .from('daily_analytics')
          .insert(analyticsData)
          .select()
          .single();

        if (error) throw error;
        return data;
      }
    }
  };
}; 