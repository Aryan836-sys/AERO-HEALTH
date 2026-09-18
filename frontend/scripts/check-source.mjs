import { readdirSync, readFileSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const ts = require('typescript');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const sourceRoot = path.join(root, 'src');
const translations = JSON.parse(readFileSync(path.join(sourceRoot, 'i18n/en.json'), 'utf8'));
const files = [];
const issues = [];
let imports = 0;
let translationCalls = 0;

function walk(directory) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) walk(target);
    else if (/\.(ts|tsx)$/.test(entry.name)) files.push(target);
  }
}

function resolveLocal(specifier, from) {
  const base = path.resolve(path.dirname(from), specifier);
  return ['', '.ts', '.tsx', '.js', '.json', '/index.ts', '/index.tsx'].some(
    (extension) => existsSync(base + extension),
  );
}

walk(sourceRoot);
for (const file of files) {
  const source = ts.createSourceFile(file, readFileSync(file, 'utf8'), ts.ScriptTarget.Latest, true);
  const relative = path.relative(root, file);
  for (const diagnostic of source.parseDiagnostics) {
    issues.push(`${relative}: ${ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n')}`);
  }
  function visit(node) {
    let specifier;
    if ((ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) && node.moduleSpecifier) {
      specifier = node.moduleSpecifier;
    } else if (ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword) {
      specifier = node.arguments[0];
    }
    if (specifier && ts.isStringLiteral(specifier) && specifier.text.startsWith('.')) {
      imports += 1;
      if (!resolveLocal(specifier.text, file)) issues.push(`${relative}: missing import ${specifier.text}`);
    }
    if (ts.isCallExpression(node) && ts.isIdentifier(node.expression) && node.expression.text === 't') {
      const key = node.arguments[0];
      if (key && ts.isStringLiteral(key)) {
        translationCalls += 1;
        if (!(key.text in translations)) issues.push(`${relative}: missing English key ${key.text}`);
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(source);
}

const nepali = JSON.parse(readFileSync(path.join(sourceRoot, 'i18n/ne.json'), 'utf8'));
for (const key of Object.keys(nepali)) {
  if (!(key in translations)) issues.push(`Nepali translation has an unknown key: ${key}`);
}
if (issues.length) {
  issues.forEach((issue) => console.error(issue));
  process.exitCode = 1;
} else {
  console.log(`Source audit passed: ${files.length} TypeScript modules, ${imports} local imports, ${translationCalls} literal translation references.`);
  console.log('This is a source-integrity audit. Use npm run typecheck for dependency-aware TypeScript validation.');
}
