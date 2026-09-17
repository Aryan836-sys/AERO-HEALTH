import { spawnSync } from 'node:child_process';
import { mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const output = path.join(root, '.test-build');
rmSync(output, { recursive: true, force: true });
mkdirSync(output, { recursive: true });
const sources = [
  'src/utils/aqi.ts', 'src/utils/geo.ts', 'src/utils/format.ts',
  'src/utils/validation.ts', 'src/utils/advisory.ts',
  'src/services/fixtures.ts', 'src/services/storage.ts', 'src/services/mockApi.ts',
];
// npm puts the project's pinned compiler on PATH. A global tsc also works offline.
const compiler = spawnSync(process.platform === 'win32' ? 'tsc.cmd' : 'tsc', [
  ...sources, '--outDir', '.test-build', '--target', 'ES2022', '--module', 'CommonJS',
  '--moduleResolution', 'Node', '--strict', '--skipLibCheck', '--lib', 'ES2022,DOM',
], { cwd: root, stdio: 'inherit', shell: process.platform === 'win32' });
if (compiler.error) {
  console.error('TypeScript is unavailable. Run npm install before npm test.');
  process.exit(1);
}
if (compiler.status !== 0) process.exit(compiler.status ?? 1);
writeFileSync(path.join(output, 'package.json'), '{"type":"commonjs"}\n');
const tests = spawnSync(process.execPath, ['--test', 'tests/unit.test.cjs'], { cwd: root, stdio: 'inherit' });
process.exit(tests.status ?? 1);
