import { supabase } from '@/lib/supabase-rn';

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

import { API_BASE_URL } from '../config/api';

class UserService {
  private apiUrl = API_BASE_URL;

  /**
   * Get comprehensive user profile from server
   */
  async getUserProfile(userId: string): Promise<UserProfile | null> {
    try {
      const response = await fetch(`${this.apiUrl}/auth/user/${userId}/profile`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to get profile');
      }

      const profile = await response.json();
      console.log('✅ Profile retrieved successfully:', profile);
      return profile;
    } catch (error) {
      console.error('❌ Error getting profile:', error);
      throw error;
    }
  }

  /**
   * Update user profile information
   */
  async updateProfile(userId: string, profileData: Partial<UserProfile>): Promise<UserProfile | null> {
    try {
      const response = await fetch(`${this.apiUrl}/auth/user/${userId}/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(profileData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to update profile');
      }

      const updatedProfile = await response.json();
      console.log('✅ Profile updated successfully:', updatedProfile);
      return updatedProfile;
    } catch (error) {
      console.error('❌ Error updating profile:', error);
      throw error;
    }
  }

  /**
   * Update user location (city and timezone)
   */
  async updateLocation(userId: string, city: string, timezone: string): Promise<UserProfile | null> {
    try {
      const updatedProfile = await this.updateProfile(userId, { city, timezone });
      console.log('📍 Location updated:', { city, timezone });
      return updatedProfile;
    } catch (error) {
      console.error('❌ Error updating location:', error);
      throw error;
    }
  }

  /**
   * Update user preferences
   */
  async updatePreferences(userId: string, preferences: any): Promise<UserProfile | null> {
    try {
      const updatedProfile = await this.updateProfile(userId, { preferences });
      console.log('⚙️ Preferences updated:', preferences);
      return updatedProfile;
    } catch (error) {
      console.error('❌ Error updating preferences:', error);
      throw error;
    }
  }

  /**
   * Update working hours
   */
  async updateWorkingHours(userId: string, workingHours: any): Promise<UserProfile | null> {
    try {
      const updatedProfile = await this.updateProfile(userId, { workingHours });
      console.log('🕐 Working hours updated:', workingHours);
      return updatedProfile;
    } catch (error) {
      console.error('❌ Error updating working hours:', error);
      throw error;
    }
  }

  /**
   * Update study preferences
   */
  async updateStudyPreferences(userId: string, studyPreferences: any): Promise<UserProfile | null> {
    try {
      const updatedProfile = await this.updateProfile(userId, { studyPreferences });
      console.log('📚 Study preferences updated:', studyPreferences);
      return updatedProfile;
    } catch (error) {
      console.error('❌ Error updating study preferences:', error);
      throw error;
    }
  }

  /**
   * Update onboarding status
   */
  async updateOnboardingStatus(userId: string, onboardingComplete: boolean, onboardingStep?: number): Promise<UserProfile | null> {
    try {
      const updates: Partial<UserProfile> = { onboardingComplete };
      if (onboardingStep !== undefined) {
        updates.onboardingStep = onboardingStep;
      }

      const updatedProfile = await this.updateProfile(userId, updates);
      console.log('🎯 Onboarding status updated:', { onboardingComplete, onboardingStep });
      return updatedProfile;
    } catch (error) {
      console.error('❌ Error updating onboarding status:', error);
      throw error;
    }
  }

  /**
   * Get user profile from Supabase (fallback method)
   */
  async getUserProfileFromSupabase(userId: string): Promise<Partial<UserProfile> | null> {
    try {
      const { data, error } = await supabase
        .from('users')
        .select('name, city, timezone, school, academic_year, user_type, preferences, working_hours, study_preferences, onboarding_complete, onboarding_step')
        .eq('id', userId)
        .single();

      if (error) {
        console.error('Error fetching user profile from Supabase:', error);
        return null;
      }

      return {
        name: data.name,
        city: data.city,
        timezone: data.timezone,
        school: data.school,
        academicYear: data.academic_year,
        userType: data.user_type as 'student' | 'professional' | 'educator',
        preferences: data.preferences,
        workingHours: data.working_hours,
        studyPreferences: data.study_preferences,
        onboardingComplete: data.onboarding_complete,
        onboardingStep: data.onboarding_step
      };
    } catch (error) {
      console.error('Error in getUserProfileFromSupabase:', error);
      return null;
    }
  }
}

export const userService = new UserService(); 