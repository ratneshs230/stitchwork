#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import { parse } from '../index.js';

const args = process.argv.slice(2);
if (args.length === 0) {
  console.error('usage: stitchwork-parse <file.md>');
  process.exit(2);
}
try {
  const src = readFileSync(args[0], 'utf8');
  const { ast, warnings } = parse(src);
  process.stdout.write(JSON.stringify({ ast, warnings }, null, 2) + '\n');
} catch (err) {
  console.error((err as Error).message);
  process.exit(1);
}
