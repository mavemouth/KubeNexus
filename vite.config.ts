import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load env files from both root and src directory so either location works seamlessly
  const envSrc = loadEnv(mode, path.resolve(__dirname, 'src'), '');
  const envRoot = loadEnv(mode, process.cwd(), '');
  const apiBaseUrl = process.env.VITE_API_BASE_URL || envRoot.VITE_API_BASE_URL || envSrc.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

  return {
    plugins: [react()],
    define: {
      'import.meta.env.VITE_API_BASE_URL': JSON.stringify(apiBaseUrl),
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 3000,
      open: true,
    },
  };
});
