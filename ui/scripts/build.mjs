import { copyFile, mkdir } from 'node:fs/promises';
await mkdir('dist', { recursive: true });
for (const file of ['index.html', 'styles.css', 'evidence.json', 'comparison.json', 'intent-comparison.json', 'review.html', 'review.css', 'review-source.json', 'review-packet.json']) {
  await copyFile(`public/${file}`, `dist/${file}`);
}
