import { User, Mail, School, Calendar } from 'lucide-react'
import { cn } from '../../lib/utils'
import { components } from '../../lib/design-tokens'
import { useProfile, useUpdateProfile } from '@/hooks/profile'
import { profileSettingsSchema, validateInput } from '../../lib/validation/settings'
import { useState, useEffect } from 'react'

export function ProfileSection() {
  const { data: profile, isLoading: profileLoading } = useProfile()
  const updateProfileMutation = useUpdateProfile()

  const [fullName, setFullName] = useState('')
  const [school, setSchool] = useState('')
  const [academicYear, setAcademicYear] = useState('')

  useEffect(() => {
    if (profile) {
      setFullName(profile.full_name || '')
      setSchool(profile.school || '')
      setAcademicYear(profile.academic_year || '')
    }
  }, [profile])

  const saveProfile = async () => {
    try {
      const validation = validateInput(profileSettingsSchema, {
        fullName,
        school,
        academicYear,
      })
      
      if (!validation.success) {
        alert(validation.error)
        return
      }
      
      await updateProfileMutation.mutateAsync({
        full_name: validation.data.fullName,
        school: validation.data.school,
        academic_year: validation.data.academicYear,
      })
      console.log('Profile updated successfully')
    } catch (error) {
      console.error('Error updating profile:', error)
      alert('Failed to update profile. Please try again.')
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Personal Information</h3>
        <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-gray-700/30">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <User size={14} className="text-gray-400" />
                <p className="text-xs text-gray-400">Full Name</p>
              </div>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Enter full name"
                className={cn(components.input.base, "w-full")}
              />
            </div>
          </div>
          <div className="p-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <Mail size={14} className="text-gray-400" />
                <p className="text-xs text-gray-400">Email</p>
              </div>
              <input
                type="email"
                value={profile?.email || ''}
                className={cn(components.input.base, "w-full opacity-50")}
                disabled
              />
            </div>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Academic Information</h3>
        <div className="bg-neutral-800/40 border border-gray-700/50 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-gray-700/30">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <School size={14} className="text-gray-400" />
                <p className="text-xs text-gray-400">School</p>
              </div>
              <input
                type="text"
                value={school}
                onChange={(e) => setSchool(e.target.value)}
                placeholder="Enter school"
                className={cn(components.input.base, "w-full")}
              />
            </div>
          </div>
          <div className="p-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <Calendar size={14} className="text-gray-400" />
                <p className="text-xs text-gray-400">Academic Year</p>
              </div>
              <input
                type="text"
                value={academicYear}
                onChange={(e) => setAcademicYear(e.target.value)}
                placeholder="Enter academic year"
                className={cn(components.input.base, "w-full")}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="flex">
        <button
          onClick={saveProfile}
          disabled={updateProfileMutation.isPending || profileLoading}
          className={cn(
            components.button.base,
            components.button.primary,
            "disabled:bg-gray-200 disabled:cursor-not-allowed"
          )}
        >
          {updateProfileMutation.isPending ? 'Saving...' : 'Save Profile'}
        </button>
      </div>
    </div>
  )
}

