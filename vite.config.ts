import { defineConfig } from 'vite';
import { resolve } from 'path';
import { fileURLToPath } from 'url';
import { copyFile, mkdir } from 'fs/promises';
import { dirname } from 'path';

const __dirname = fileURLToPath(new URL('.', import.meta.url));

const copyToStaticPlugin = () => {
  const copyIfExists = (
    source: string,
    target: string
  ): Promise<void> =>
    mkdir(dirname(target), { recursive: true })
      .then(() => copyFile(source, target))
      .catch((err: NodeJS.ErrnoException) => {
        if (err.code !== 'ENOENT') {
          console.error('Copy to static failed:', err);
        }
      });
  return {
    name: 'copy-to-static',
    writeBundle(_options: unknown, bundle: Record<string, { type?: string; fileName?: string }>) {
      const distDir = resolve(__dirname, 'dist');
      const promises: Promise<void>[] = [];
      const jsSource = resolve(distDir, 'bundle.js');
      promises.push(copyIfExists(jsSource, resolve(__dirname, 'static', 'js', 'bundle.js')));
      const cssEntry = Object.keys(bundle).find(
        (key) => bundle[key].type === 'asset' && key.endsWith('.css')
      );
      if (cssEntry) {
        const cssSource = resolve(distDir, bundle[cssEntry].fileName ?? cssEntry);
        promises.push(
          copyIfExists(cssSource, resolve(__dirname, 'static', 'css', 'bundle.css'))
        );
      }
      return Promise.all(promises);
    },
  };
};

export default defineConfig({
  root: resolve(__dirname, 'frontend'),
  plugins: [copyToStaticPlugin()],
  css: {
    preprocessorOptions: {
      scss: {},
    },
  },
  build: {
    outDir: resolve(__dirname, 'dist'),
    emptyOutDir: true,
    minify: false,
    rollupOptions: {
      input: resolve(__dirname, 'frontend/src/Main.js'),
      output: {
        entryFileNames: 'bundle.js',
        assetFileNames: (assetInfo) => {
          const name = assetInfo.name ?? '';
          return name.endsWith('.css') ? 'css/bundle[extname]' : 'assets/[name]-[hash][extname]';
        },
        format: 'iife',
        name: 'App',
      },
    },
    watch: {
      include: ['frontend/src/**', 'frontend/css/**'],
    },
  },
});
