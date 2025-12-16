import { copyFile, mkdir } from 'fs/promises';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
const rootDir = join(__dirname, '..');
const distFile = join(rootDir, 'dist', 'bundle.js');
const targetFile = join(rootDir, 'static', 'js', 'bundle.js');
const targetDir = dirname(targetFile);

try {
    // Создаем директорию, если её нет
    await mkdir(targetDir, { recursive: true });
    
    // Копируем файл
    await copyFile(distFile, targetFile);
    console.log(`✓ Скопирован ${distFile} -> ${targetFile}`);
} catch (error) {
    if (error.code === 'ENOENT' && error.path === distFile) {
        console.error(`✗ Файл не найден: ${distFile}`);
        console.error('  Убедитесь, что сначала выполнен "npm run build"');
        process.exit(1);
    } else {
        console.error('Ошибка при копировании:', error);
        process.exit(1);
    }
}
