import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { supabase } from '../lib/supabase'

export interface UserProfile {
  id: string
  email: string
  full_name: string
  school: string
  academic_year: string
  role?: string
  subscription_status?: 'free' | 'premium'
}

const PROFILE_CACHE_KEY = ['user', 'profile']

export const useProfile = () => {
  return useQuery({
    queryKey: PROFILE_CACHE_KEY,
    queryFn: async (): Promise<UserProfile> => {
      // Get current user from auth
      const { data: { user }, error: authError } = await supabase.auth.getUser()

      if (authError || !user) {
        throw new Error('Not authenticated')
      }

      // Try to get profile from users table
      const { data, error } = await supabase
        .from('users')
        .select('id, full_name, school, academic_year, role, subscription_status')
        .eq('id', user.id)
        .maybeSingle()

      // If user doesn't exist in users table, create it
      if (!data && !error) {
        const newUser = {
          id: user.id,
          email: user.email!,
          full_name: user.user_metadata?.name || user.email?.split('@')[0] || '',
          school: '',
          academic_year: '',
          role: 'user',
          subscription_status: 'free' as const,
        }

        const { error: insertError } = await supabase
          .from('users')
          .insert(newUser)

        if (insertError) {
          console.error('Error creating user profile:', insertError)
        }

        return newUser
      }

      if (error) {
        throw error
      }

      return {
        id: user.id,
        email: user.email!,
        full_name: data?.full_name || '',
        school: data?.school || '',
        academic_year: data?.academic_year || '',
        role: data?.role || 'user',
        subscription_status: data?.subscription_status || 'free',
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}

export const useUpdateProfile = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (updates: Partial<Omit<UserProfile, 'id' | 'email'>>) => {
      const { data: { user } } = await supabase.auth.getUser()

      if (!user) {
        throw new Error('Not authenticated')
      }

      const { error } = await supabase
        .from('users')
        .update(updates)
        .eq('id', user.id)

      if (error) {
        throw error
      }

      return updates
    },
    onSuccess: () => {
      // Invalidate and refetch profile
      queryClient.invalidateQueries({ queryKey: PROFILE_CACHE_KEY })
    },
  })
}
