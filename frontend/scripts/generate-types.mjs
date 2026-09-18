import { spawnSync } from 'node:child_process';
import { mkdirSync, existsSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const demo = process.argv.includes('--demo');
const supplied = process.argv.find((argument, index) => index > 1 && !argument.startsWith('--'));
const source = demo
  ? path.join(root, 'contracts/openapi.demo.json')
  : supplied || process.env.OPENAPI_URL || 'http://localhost:8000/openapi.json';
const output = path.join(root, 'src/types', demo ? 'api.demo.generated.ts' : 'api.generated.ts');
const packageRoot = path.join(root, 'node_modules/openapi-typescript');
const packageFile = path.join(packageRoot, 'package.json');

if (!existsSync(packageFile)) {
  console.error('Install dependencies first: npm install');
  process.exit(1);
}
const packageInfo = JSON.parse(readFileSync(packageFile, 'utf8'));
const binEntry = typeof packageInfo.bin === 'string' ? packageInfo.bin : packageInfo.bin?.['openapi-typescript'];
if (!binEntry) throw new Error('The installed OpenAPI generator does not expose its CLI.');
const binary = path.resolve(packageRoot, binEntry);
mkdirSync(path.dirname(output), { recursive: true });
console.log(`Generating ${demo ? 'DEMO ONLY' : 'backend'} schema types from ${source}`);
const result = spawnSync(process.execPath, [binary, source, '-o', output], {
  cwd: root,
  stdio: 'inherit',
});
if (result.error) console.error(result.error.message);
if (result.status === 0) {
  console.log('Generated types do not automatically reconcile API response shapes. Update services/api.ts against this schema before enabling real mode.');
}
process.exit(result.status ?? 1);
