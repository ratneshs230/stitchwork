import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import pc from 'picocolors';
import { runPythonWorker } from '../runWorker.js';

export async function runPreview(bookPath: string, port: number): Promise<number> {
  const abs = resolve(bookPath);
  if (!existsSync(abs)) {
    console.error(pc.red(`book path not found: ${abs}`));
    return 2;
  }
  console.log(pc.cyan(`starting localhost preview on :${port}…`));
  const res = await runPythonWorker('renderer-web', 'stitchwork_renderer_web.cli', [
    '--book',
    abs,
    '--port',
    String(port),
  ]);
  if (!res.ok) {
    console.error(pc.red(`preview failed (exit ${res.exitCode})`));
    if (res.stderr.trim()) console.error(res.stderr.trim());
  }
  return res.ok ? 0 : 1;
}
