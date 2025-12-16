import { defineConfig } from 'vite';
import { resolve } from 'path';
import { fileURLToPath } from 'url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));

export default defineConfig({
  root: resolve(__dirname, 'frontend'),
  build: {
    outDir: resolve(__dirname, 'static/js'),
    emptyOutDir: false, // Не очищаем директорию, чтобы не удалить другие файлы (highlighting.js и т.д.)
    rollupOptions: {
      input: resolve(__dirname, 'frontend/src/main.js'),
      output: {
        entryFileNames: 'bundle.js',
        format: 'iife',
        name: 'App'
      }
    }
  }
});
