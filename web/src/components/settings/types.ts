export type SettingsSection = 
  | 'profile' 
  | 'appearance' 
  | 'briefings' 
  | 'hobbies' 
  | 'reminders' 
  | 'study' 
  | 'courses' 
  | 'tags' 
  | 'weekly-pulse' 
  | 'personalization' 
  | 'premium'
  | 'duration-preferences'

export interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
  initialSection?: SettingsSection
}

