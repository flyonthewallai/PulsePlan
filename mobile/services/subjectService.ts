import { supabase } from '../lib/supabase';
import { Subject } from '../contexts/SubjectContext';

interface CreateSubjectData {
  name: string;
  color: string;
  icon?: string;
}

interface SubjectService {
  getSubjects(): Promise<Subject[]>;
  createSubject(data: CreateSubjectData): Promise<Subject>;
  updateSubject(id: string, updates: Partial<Subject>): Promise<Subject>;
  deleteSubject(id: string): Promise<void>;
}

export const createSubjectService = (): SubjectService => {
  return {
    async getSubjects(): Promise<Subject[]> {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('Not authenticated');

      const { data, error } = await supabase
        .from('subjects')
        .select('*')
        .eq('user_id', user.id)
        .eq('is_active', true)
        .order('name');

      if (error) throw error;
      return data || [];
    },

    async createSubject(subjectData: CreateSubjectData): Promise<Subject> {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('Not authenticated');

      const { data, error } = await supabase
        .from('subjects')
        .insert({
          user_id: user.id,
          name: subjectData.name,
          color: subjectData.color,
          icon: subjectData.icon,
          is_active: true
        })
        .select()
        .single();

      if (error) throw error;
      return data;
    },

    async updateSubject(id: string, updates: Partial<Subject>): Promise<Subject> {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('Not authenticated');

      const { data, error } = await supabase
        .from('subjects')
        .update({
          ...updates,
          updated_at: new Date().toISOString()
        })
        .eq('id', id)
        .eq('user_id', user.id)
        .select()
        .single();

      if (error) throw error;
      return data;
    },

    async deleteSubject(id: string): Promise<void> {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('Not authenticated');

      // Soft delete by setting is_active to false
      const { error } = await supabase
        .from('subjects')
        .update({ 
          is_active: false,
          updated_at: new Date().toISOString()
        })
        .eq('id', id)
        .eq('user_id', user.id);

      if (error) throw error;
    }
  };
}; 