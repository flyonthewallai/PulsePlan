// User-related services - courses, tags, profile
export { coursesApi } from './coursesService'
export type { Course } from './coursesService'

export { tagsApi } from './tagsService'
export type { Tag, UserTag } from './tagsService'

export { durationPreferencesApi } from './durationPreferencesService'
export type { 
  DurationPreference, 
  CourseDurationPreference,
  DurationPreferenceCreate,
  CourseDurationPreferenceCreate 
} from './durationPreferencesService'

