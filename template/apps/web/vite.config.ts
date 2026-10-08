import path from 'node:path';
import { fileURLToPath } from 'node:url';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

const webRoot = fileURLToPath(new URL('.', import.meta.url));
const workspaceRoot = path.resolve(webRoot, '../..');

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    fs: { allow: [webRoot, path.resolve(workspaceRoot, 'locales')] },
    proxy: { '/api': process.env['API_PROXY_TARGET'] ?? 'http://127.0.0.1:8000' },
  },
});
