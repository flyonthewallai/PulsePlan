export const config = {
  supabase: {
    url: import.meta.env.VITE_SUPABASE_URL || '',
    anonKey: import.meta.env.VITE_SUPABASE_ANON_KEY || '',
  },
  api: {
    baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  },
  app: {
    name: 'PulsePlan',
    version: '1.0.0',
    isDev: import.meta.env.DEV,
    isProd: import.meta.env.PROD,
  },
} as const;

export function validateConfig() {
  const required = [
    { key: 'VITE_SUPABASE_URL', value: config.supabase.url },
    { key: 'VITE_SUPABASE_ANON_KEY', value: config.supabase.anonKey },
  ];

  const missing = required.filter(({ value }) => !value);

  if (missing.length > 0) {
    console.error('Missing required environment variables:', missing.map(({ key }) => key));
    throw new Error(`Missing environment variables: ${missing.map(({ key }) => key).join(', ')}`);
  }
}