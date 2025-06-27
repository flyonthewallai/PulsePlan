import { supabase } from '../lib/supabase';

export interface Subject {
  id: string;
  user_id: string;
  name: string;
  color: string;
  icon?: string;
  created_at?: string;
}

export interface CreateSubjectData {
  name: string;
  color: string;
  icon?: string;
}

export interface UpdateSubjectData {
  name?: string;
  color?: string;
  icon?: string;
}

class SubjectsService {
  async getUserSubjects(userId: string): Promise<Subject[]> {
    try {
      const { data, error } = await supabase
        .from('subjects')
        .select('*')
        .eq('user_id', userId)
        .order('created_at', { ascending: true });

      if (error) {
        console.error('Error fetching subjects:', error);
        throw error;
      }

      return data || [];
    } catch (error) {
      console.error('Error in getUserSubjects:', error);
      throw error;
    }
  }

  async createSubject(userId: string, subjectData: CreateSubjectData): Promise<Subject> {
    try {
      const { data, error } = await supabase
        .from('subjects')
        .insert([
          {
            user_id: userId,
            name: subjectData.name,
            color: subjectData.color,
            icon: subjectData.icon,
          },
        ])
        .select()
        .single();

      if (error) {
        console.error('Error creating subject:', error);
        throw error;
      }

      return data;
    } catch (error) {
      console.error('Error in createSubject:', error);
      throw error;
    }
  }

  async updateSubject(subjectId: string, updateData: UpdateSubjectData): Promise<Subject> {
    try {
      const { data, error } = await supabase
        .from('subjects')
        .update(updateData)
        .eq('id', subjectId)
        .select()
        .single();

      if (error) {
        console.error('Error updating subject:', error);
        throw error;
      }

      return data;
    } catch (error) {
      console.error('Error in updateSubject:', error);
      throw error;
    }
  }

  async deleteSubject(subjectId: string): Promise<void> {
    try {
      const { error } = await supabase
        .from('subjects')
        .delete()
        .eq('id', subjectId);

      if (error) {
        console.error('Error deleting subject:', error);
        throw error;
      }
    } catch (error) {
      console.error('Error in deleteSubject:', error);
      throw error;
    }
  }

  async createDefaultSubjects(userId: string): Promise<Subject[]> {
    const defaultSubjects: CreateSubjectData[] = [
      { name: 'Mathematics', color: '#6366F1' },
      { name: 'Science', color: '#06B6D4' },
      { name: 'History', color: '#F59E0B' },
      { name: 'Literature', color: '#10B981' },
    ];

    try {
      const { data, error } = await supabase
        .from('subjects')
        .insert(
          defaultSubjects.map(subject => ({
            user_id: userId,
            name: subject.name,
            color: subject.color,
            icon: subject.icon,
          }))
        )
        .select();

      if (error) {
        console.error('Error creating default subjects:', error);
        throw error;
      }

      return data || [];
    } catch (error) {
      console.error('Error in createDefaultSubjects:', error);
      throw error;
    }
  }
}

export const subjectsService = new SubjectsService(); 