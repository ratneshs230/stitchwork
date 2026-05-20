/** Smoke test the benchmark on the bundled sample book. */

import { describe, expect, it } from 'vitest';
import { resolve } from 'node:path';
import { bench } from '../src/bench.js';

describe('bench', () => {
  it('parses the sample book in well under 200ms', async () => {
    const book = resolve(__dirname, '..', '..', 'sample-book', 'ai-indian-advocate');
    const res = await bench(book);
    expect(res.chapters).toBeGreaterThanOrEqual(1);
    expect(res.parseMs).toBeLessThan(200);
    expect(res.bytesIn).toBeGreaterThan(0);
  });
});
