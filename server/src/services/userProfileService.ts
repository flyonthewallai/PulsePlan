import { cacheService, CACHE_CONFIG } from './cacheService';
import supabase from '../config/supabase';

export interface UserProfile {
  id: string;
  email: string;
  name?: string;
  avatarUrl?: string;
  timezone?: string;
  city?: string;
  school?: string;
  academicYear?: string;
  userType?: 'student' | 'professional' | 'educator';
  subscriptionStatus: 'free' | 'premium';
  isPremium: boolean;
  preferences?: any;
  workingHours?: any;
  studyPreferences?: any;
  workPreferences?: any;
  integrationPreferences?: any;
  notificationPreferences?: any;
  onboardingComplete?: boolean;
  onboardingStep?: number;
  lastLoginAt?: string;
  createdAt: string;
  updatedAt?: string;
}

export class UserProfileService {
  /**
   * Get comprehensive user profile with caching
   */
  async getUserProfile(userId: string): Promise<UserProfile | null> {
    // Try cache first
    const cachedProfile = await cacheService.get<UserProfile>(
      CACHE_CONFIG.KEYS.USER_INFO, 
      userId
    );
    
    if (cachedProfile) {
      console.log(`📝 User profile cache hit for user ${userId}`);
      return cachedProfile;
    }

    // Cache miss - fetch from database
    if (!supabase) {
      console.warn('Supabase not configured, skipping user profile fetch');
      return null;
    }

    try {
      console.log(`📊 Fetching user profile from DB for user ${userId}`);

      const { data: userData, error } = await supabase
        .from('users')
        .select(`
          id,
          email,
          name, 
          avatar_url,
          subscription_status, 
          timezone, 
          city,
          school,
          academic_year,
          user_type,
          preferences,
          working_hours,
          study_preferences,
          work_preferences,
          integration_preferences,
          notification_preferences,
          onboarding_complete,
          onboarding_step,
          last_login_at,
          created_at,
          updated_at
        `)
        .eq('id', userId)
        .single();

      if (error) {
        console.error('Error fetching user profile:', error);
        return null;
      }

      if (!userData) {
        console.log('No user profile found for user:', userId);
        return null;
      }

      const userProfile: UserProfile = {
        id: userData.id,
        email: userData.email,
        name: userData.name || undefined,
        avatarUrl: userData.avatar_url || undefined,
        timezone: userData.timezone || 'UTC',
        city: userData.city || undefined,
        school: userData.school || undefined,
        academicYear: userData.academic_year || undefined,
        userType: userData.user_type as 'student' | 'professional' | 'educator' || undefined,
        subscriptionStatus: userData.subscription_status as 'free' | 'premium',
        isPremium: userData.subscription_status === 'premium',
        preferences: userData.preferences || {},
        workingHours: userData.working_hours || { endHour: 17, startHour: 9 },
        studyPreferences: userData.study_preferences || {},
        workPreferences: userData.work_preferences || {},
        integrationPreferences: userData.integration_preferences || {},
        notificationPreferences: userData.notification_preferences || {},
        onboardingComplete: userData.onboarding_complete || false,
        onboardingStep: userData.onboarding_step || 0,
        lastLoginAt: userData.last_login_at || undefined,
        createdAt: userData.created_at,
        updatedAt: userData.updated_at || undefined
      };

      // Cache the result
      await cacheService.set(
        CACHE_CONFIG.KEYS.USER_INFO,
        userId,
        userProfile,
        CACHE_CONFIG.TTL.USER_INFO
      );

      console.log(`📊 Found and cached user profile for user ${userId}:`, { 
        hasName: !!userProfile.name, 
        isPremium: userProfile.isPremium,
        timezone: userProfile.timezone,
        hasCity: !!userProfile.city,
        hasSchool: !!userProfile.school,
        userType: userProfile.userType,
        onboardingComplete: userProfile.onboardingComplete
      });
      
      return userProfile;
    } catch (error) {
      console.error('Error in getUserProfile:', error);
      return null;
    }
  }

  /**
   * Update user profile and invalidate cache
   */
  async updateUserProfile(userId: string, updates: Partial<UserProfile>): Promise<UserProfile | null> {
    if (!supabase) {
      console.warn('Supabase not configured, skipping user profile update');
      return null;
    }

    try {
      // Prepare update data (only include fields that can be updated)
      const updateData: any = {
        updated_at: new Date().toISOString()
      };

      if (updates.name !== undefined) updateData.name = updates.name;
      if (updates.avatarUrl !== undefined) updateData.avatar_url = updates.avatarUrl;
      if (updates.timezone !== undefined) updateData.timezone = updates.timezone;
      if (updates.city !== undefined) updateData.city = updates.city;
      if (updates.school !== undefined) updateData.school = updates.school;
      if (updates.academicYear !== undefined) updateData.academic_year = updates.academicYear;
      if (updates.userType !== undefined) updateData.user_type = updates.userType;
      if (updates.preferences !== undefined) updateData.preferences = updates.preferences;
      if (updates.workingHours !== undefined) updateData.working_hours = updates.workingHours;
      if (updates.studyPreferences !== undefined) updateData.study_preferences = updates.studyPreferences;
      if (updates.workPreferences !== undefined) updateData.work_preferences = updates.workPreferences;
      if (updates.integrationPreferences !== undefined) updateData.integration_preferences = updates.integrationPreferences;
      if (updates.notificationPreferences !== undefined) updateData.notification_preferences = updates.notificationPreferences;
      if (updates.onboardingComplete !== undefined) updateData.onboarding_complete = updates.onboardingComplete;
      if (updates.onboardingStep !== undefined) updateData.onboarding_step = updates.onboardingStep;

      // Update in database
      const { data: updatedUser, error } = await supabase
        .from('users')
        .update(updateData)
        .eq('id', userId)
        .select()
        .single();

      if (error) {
        console.error('Error updating user profile:', error);
        return null;
      }

      // Invalidate cache to ensure fresh data
      await cacheService.delete(CACHE_CONFIG.KEYS.USER_INFO, userId);

      console.log(`✅ User profile updated for user ${userId}:`, Object.keys(updates));
      
      // Return the updated profile (will be fetched fresh from cache next time)
      return this.getUserProfile(userId);
    } catch (error) {
      console.error('Error in updateUserProfile:', error);
      return null;
    }
  }

  /**
   * Get user profile by email (useful for auth flows)
   */
  async getUserProfileByEmail(email: string): Promise<UserProfile | null> {
    if (!supabase) {
      console.warn('Supabase not configured, skipping user profile fetch');
      return null;
    }

    try {
      const { data: userData, error } = await supabase
        .from('users')
        .select('id')
        .eq('email', email)
        .single();

      if (error || !userData) {
        console.log('No user found with email:', email);
        return null;
      }

      // Use the main getUserProfile method which includes caching
      return this.getUserProfile(userData.id);
    } catch (error) {
      console.error('Error in getUserProfileByEmail:', error);
      return null;
    }
  }

  /**
   * Invalidate user profile cache
   */
  async invalidateUserCache(userId: string): Promise<void> {
    await cacheService.delete(CACHE_CONFIG.KEYS.USER_INFO, userId);
    console.log(`🗑️ User profile cache invalidated for user ${userId}`);
  }
}

export const userProfileService = new UserProfileService(); 