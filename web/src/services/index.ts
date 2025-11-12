/**
 * Services - Domain-organized API clients
 * 
 * This is the main entry point for all services. Services are organized by domain:
 * - integrations/ - External integrations (Canvas, OAuth)
 * - focus/ - Focus sessions and Pomodoro
 * - tasks/ - Tasks and todos
 * - user/ - User-related data (courses, tags)
 * - core/ - Base API service
 * 
 * Import from domain folders for better organization:
 *   import { canvasService } from '@/services/integrations'
 *   import { todosService } from '@/services/tasks'
 * 
 * Or use backward-compatible imports from root:
 *   import { canvasService } from '@/services'
 */

// Core API service
export { apiService } from './core'

// Integration services
export {
  canvasService,
  formatLastSync,
  oauthService,
} from './integrations'
export type {
  CanvasIntegrationStatus,
  OAuthConnection,
  OAuthInitiateResponse,
  OAuthProvider,
  OAuthService,
} from './integrations'

// Focus services
export {
  startFocusSession,
  endFocusSession,
  getActiveSession,
  getSessionHistory,
  getFocusProfile,
  getSessionInsights,
  deleteSession,
  matchEntity,
  getEntitySuggestions,
  startPhase,
  endPhase,
  getPomodoroSettings,
  putPomodoroSettings,
} from './focus'
export type {
  FocusSession,
  FocusProfile,
  StartSessionRequest,
  EndSessionRequest,
  MatchedEntity,
  EntityMatchResult,
  EntitySuggestion,
  PhaseType,
  PomodoroSettings,
} from './focus'

// Task services
export { todosService } from './tasks'
export type {
  Todo,
  CreateTodoData,
  UpdateTodoData,
  TodoFilters,
} from './tasks'

// User services
export { coursesApi, tagsApi } from './user'
export type { Course, Tag, UserTag } from './user'

