import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: true,
    // Security: Restrict file system access to prevent unauthorized file reads
    fs: {
      // Deny access to sensitive files and directories
      deny: [
        // Environment files
        '.env',
        '.env.local',
        '.env.*.local',
        // Private keys and certificates
        '**/*.key',
        '**/*.pem',
        '**/*.p12',
        '**/*.pfx',
        // System files (Unix)
        '/etc/passwd',
        '/etc/shadow',
        '/etc/hosts',
        // System files (Windows)
        'C:\\Windows\\System32',
        // Git files
        '.git',
        '.gitignore',
        // Node modules (shouldn't be accessed directly)
        'node_modules',
        // Build artifacts
        'dist',
        '.next',
        // Config files with secrets
        '**/config/secrets.*',
        '**/secrets.*',
      ],
      // Only allow serving files from project root and node_modules
      strict: true,
    },
  },
  build: {
    outDir: 'dist',
  },
})
