import React from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { User, Mail, Calendar, MapPin, Save } from 'lucide-react'
import { userAPI } from '@/lib/api/sdk'
import { getCurrentUser } from '@/lib/supabase'
import { cn } from '@/lib/utils'
import { toast } from '@/lib/toast'

const profileSchema = z.object({
  full_name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
  timezone: z.string().min(1, 'Timezone is required'),
  working_hours_start: z.number().min(0).max(23),
  working_hours_end: z.number().min(1).max(24),
  daily_goal: z.number().min(1).max(20),
})

type ProfileFormData = z.infer<typeof profileSchema>

export function ProfileSettings() {
  const queryClient = useQueryClient()

  // Get current user
  const { data: user } = useQuery({
    queryKey: ['current-user'],
    queryFn: getCurrentUser,
  })

  // Get user preferences
  const { data: preferences, isLoading } = useQuery({
    queryKey: ['user-preferences'],
    queryFn: async () => {
      const result = await userAPI.getUserPreferences()
      if (result.error) throw new Error(result.error)
      return result.data
    },
  })

  const form = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: '',
      email: '',
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      working_hours_start: 9,
      working_hours_end: 17,
      daily_goal: 5,
    },
  })

  // Update user preferences mutation
  const updatePreferencesMutation = useMutation({
    mutationFn: async (data: ProfileFormData) => {
      const result = await userAPI.updateUserPreferences({
        full_name: data.full_name,
        timezone: data.timezone,
        working_hours: {
          start: data.working_hours_start,
          end: data.working_hours_end,
        },
        daily_goal: data.daily_goal,
      })
      if (result.error) throw new Error(result.error)
      return result.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-preferences'] })
      toast.success('Profile updated successfully')
    },
    onError: (error) => {
      toast.error('Failed to update profile', error instanceof Error ? error.message : 'Please try again')
      console.error('Failed to update preferences:', error)
    },
  })

  // Set form values when data loads
  React.useEffect(() => {
    if (user?.user && preferences) {
      form.reset({
        full_name: user.user.user_metadata?.full_name || '',
        email: user.user.email || '',
        timezone: preferences.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
        working_hours_start: preferences.working_hours?.start || 9,
        working_hours_end: preferences.working_hours?.end || 17,
        daily_goal: preferences.daily_goal || 5,
      })
    }
  }, [user, preferences, form])

  const onSubmit = (data: ProfileFormData) => {
    updatePreferencesMutation.mutate(data)
  }

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-gray-700 rounded w-1/3"></div>
        <div className="space-y-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-12 bg-gray-700 rounded"></div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-textPrimary mb-2">Profile Settings</h2>
        <p className="text-textSecondary">
          Manage your personal information and preferences
        </p>
      </div>

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        {/* Personal Information */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-textPrimary mb-4 flex items-center gap-2">
            <User className="w-5 h-5 text-primary" />
            Personal Information
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-textPrimary mb-2">
                Full Name
              </label>
              <input
                {...form.register('full_name')}
                className="input w-full"
                placeholder="Enter your full name"
              />
              {form.formState.errors.full_name && (
                <p className="bg-error text-white text-sm mt-1 px-2 py-1 rounded">{form.formState.errors.full_name.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-textPrimary mb-2">
                <Mail className="w-4 h-4 inline mr-1" />
                Email Address
              </label>
              <input
                {...form.register('email')}
                type="email"
                disabled
                className="input w-full opacity-60 cursor-not-allowed"
                placeholder="Enter your email"
              />
              <p className="text-textSecondary text-xs mt-1">
                Email cannot be changed here. Contact support if needed.
              </p>
            </div>
          </div>
        </div>

        {/* Work Preferences */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-textPrimary mb-4 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-primary" />
            Work Preferences
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-textPrimary mb-2">
                <MapPin className="w-4 h-4 inline mr-1" />
                Timezone
              </label>
              <select
                {...form.register('timezone')}
                className="input w-full"
              >
                <option value="America/New_York">Eastern Time (ET)</option>
                <option value="America/Chicago">Central Time (CT)</option>
                <option value="America/Denver">Mountain Time (MT)</option>
                <option value="America/Los_Angeles">Pacific Time (PT)</option>
                <option value="Europe/London">Greenwich Mean Time (GMT)</option>
                <option value="Europe/Paris">Central European Time (CET)</option>
                <option value="Asia/Tokyo">Japan Standard Time (JST)</option>
                <option value="Australia/Sydney">Australian Eastern Time (AET)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-textPrimary mb-2">
                Daily Task Goal
              </label>
              <input
                {...form.register('daily_goal', { valueAsNumber: true })}
                type="number"
                min="1"
                max="20"
                className="input w-full"
                placeholder="5"
              />
              <p className="text-textSecondary text-xs mt-1">
                Target number of tasks to complete per day
              </p>
            </div>
          </div>

          <div className="mt-4">
            <label className="block text-sm font-medium text-textPrimary mb-2">
              Working Hours
            </label>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-textSecondary mb-1">Start Time</label>
                <select
                  {...form.register('working_hours_start', { valueAsNumber: true })}
                  className="input w-full"
                >
                  {Array.from({ length: 24 }, (_, i) => (
                    <option key={i} value={i}>
                      {i === 0 ? '12:00 AM' : i < 12 ? `${i}:00 AM` : i === 12 ? '12:00 PM' : `${i - 12}:00 PM`}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-textSecondary mb-1">End Time</label>
                <select
                  {...form.register('working_hours_end', { valueAsNumber: true })}
                  className="input w-full"
                >
                  {Array.from({ length: 24 }, (_, i) => {
                    const hour = i + 1
                    return (
                      <option key={hour} value={hour}>
                        {hour === 24 ? '12:00 AM' : hour < 12 ? `${hour}:00 AM` : hour === 12 ? '12:00 PM' : `${hour - 12}:00 PM`}
                      </option>
                    )
                  })}
                </select>
              </div>
            </div>
            <p className="text-textSecondary text-xs mt-1">
              Used for scheduling tasks and calendar events
            </p>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={updatePreferencesMutation.isPending || !form.formState.isDirty}
            className={cn(
              'btn-primary flex items-center gap-2',
              (updatePreferencesMutation.isPending || !form.formState.isDirty) && 'opacity-50 cursor-not-allowed'
            )}
          >
            <Save className="w-4 h-4" />
            {updatePreferencesMutation.isPending ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>
    </div>
  )
}