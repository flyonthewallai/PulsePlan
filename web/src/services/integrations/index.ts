// Integration services - Canvas, OAuth, and other external integrations
export { canvasService, formatLastSync } from './canvasService'
export type { CanvasIntegrationStatus } from './canvasService'

export { oauthService } from './oauthService'
export type {
  OAuthConnection,
  OAuthInitiateResponse,
  OAuthProvider,
  OAuthService,
} from './oauthService'

