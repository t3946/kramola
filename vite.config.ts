import { defineConfig } from 'vite';
import { resolve } from 'path';
import { fileURLToPath } from 'url';
import { copyFile, mkdir } from 'fs/promises';
import { dirname } from 'path';

const __dirname = fileURLToPath(new URL('.', import.meta.url));

// Плагин для копирования bundle.js в static/js после сборки
const copyBundlePlugin = () => {
  return {
    name: 'copy-bundle',
    writeBundle() {
      const distFile = resolve(__dirname, 'dist', 'bundle.js');
      const targetFile = resolve(__dirname, 'static', 'js', 'bundle.js');
      const targetDir = dirname(targetFile);
      
      return mkdir(targetDir, { recursive: true })
        .then(() => copyFile(distFile, targetFile))
        .then(() => console.log(`✓ Скопирован bundle.js в static/js`))
        .catch(err => {
          if (err.code !== 'ENOENT') {
            console.error('Ошибка при копировании bundle.js:', err);
          }
        });
    }
  };
};

export default defineConfig({
  root: resolve(__dirname, 'frontend'),
  plugins: [copyBundlePlugin()],
  build: {
    outDir: resolve(__dirname, 'dist'),
    emptyOutDir: true, // Очищаем директорию dist при сборке
    minify: false, // Отключаем минификацию в режиме разработки для более быстрой сборки
    rollupOptions: {
      input: resolve(__dirname, 'frontend/src/main.js'),
      output: {
        entryFileNames: 'bundle.js',
        format: 'iife',
        name: 'App'
      }
    },
    watch: {
      // Настройки для watch режима
      include: ['frontend/src/**']
    }
  }
});
