/** Minimal perf benchmark over a book's parse pipeline. Run via `pnpm tsx bench.ts <book>`. */

import { performance } from 'node:perf_hooks';
import { loadBook } from './book.js';

export interface BenchResult {
  chapters: number;
  parseMs: number;
  bytesIn: number;
}

export async function bench(bookPath: string): Promise<BenchResult> {
  const t0 = performance.now();
  const book = loadBook(bookPath);
  const parseMs = performance.now() - t0;
  const bytesIn = book.chapters.reduce((acc, c) => acc + c.source.length, 0);
  return { chapters: book.chapters.length, parseMs, bytesIn };
}
