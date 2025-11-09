import { z } from 'zod'

/**
 * Settings form validation schemas using Zod
 * These schemas enforce input validation and prevent XSS/injection attacks
 */

// Profile settings schema
export const profileSettingsSchema = z.object({
  fullName: z
    .string()
    .min(1, 'Name is required')
    .min(2, 'Name must be at least 2 characters')
    .max(100, 'Name must be less than 100 characters')
    .regex(/^[a-zA-Z\s'-]+$/, 'Name can only contain letters, spaces, hyphens, and apostrophes')
    .trim(),
  
  school: z
    .string()
    .max(200, 'School name must be less than 200 characters')
    .trim()
    .optional()
    .or(z.literal('')),
  
  academicYear: z
    .string()
    .max(50, 'Academic year must be less than 50 characters')
    .regex(/^[a-zA-Z0-9\s-]*$/, 'Academic year can only contain letters, numbers, spaces, and hyphens')
    .trim()
    .optional()
    .or(z.literal('')),
})

export type ProfileSettingsInput = z.infer<typeof profileSettingsSchema>

// Tag creation schema
export const tagCreationSchema = z.object({
  name: z
    .string()
    .min(1, 'Tag name is required')
    .min(2, 'Tag name must be at least 2 characters')
    .max(50, 'Tag name must be less than 50 characters')
    .regex(/^[a-zA-Z0-9\s-]+$/, 'Tag name can only contain letters, numbers, spaces, and hyphens')
    .trim(),
})

export type TagCreationInput = z.infer<typeof tagCreationSchema>

// Hobby settings schema
export const hobbySettingsSchema = z.object({
  name: z
    .string()
    .min(1, 'Hobby name is required')
    .min(2, 'Hobby name must be at least 2 characters')
    .max(100, 'Hobby name must be less than 100 characters')
    .regex(/^[a-zA-Z0-9\s-]+$/, 'Hobby name can only contain letters, numbers, spaces, and hyphens')
    .trim(),
  
  duration_min: z
    .number()
    .int('Duration must be a whole number')
    .min(5, 'Minimum duration must be at least 5 minutes')
    .max(480, 'Minimum duration cannot exceed 8 hours (480 minutes)'),
  
  duration_max: z
    .number()
    .int('Duration must be a whole number')
    .min(5, 'Maximum duration must be at least 5 minutes')
    .max(480, 'Maximum duration cannot exceed 8 hours (480 minutes)'),
}).refine((data) => data.duration_max >= data.duration_min, {
  message: 'Maximum duration must be greater than or equal to minimum duration',
  path: ['duration_max'],
})

export type HobbySettingsInput = z.infer<typeof hobbySettingsSchema>

// Helper function to safely parse and validate input
export function validateInput<T>(
  schema: z.ZodSchema<T>,
  data: unknown
): { success: true; data: T } | { success: false; error: string } {
  try {
    const validated = schema.parse(data)
    return { success: true, data: validated }
  } catch (error) {
    if (error instanceof z.ZodError) {
      const firstError = error.errors[0]
      return {
        success: false,
        error: firstError?.message || 'Validation failed',
      }
    }
    return { success: false, error: 'Validation failed' }
  }
}

// Helper function for safe parsing without throwing
export function safeValidate<T>(
  schema: z.ZodSchema<T>,
  data: unknown
): { success: true; data: T } | { success: false; errors: z.ZodError } {
  const result = schema.safeParse(data)
  if (result.success) {
    return { success: true, data: result.data }
  }
  return { success: false, errors: result.error }
}


