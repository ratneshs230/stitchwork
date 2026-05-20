import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/** Locate the repo root so we can find sibling packages. */
function repoRoot(): string {
  // dist/runWorker.js → ../../ is packages/cli/, ../../../ is repo
  return resolve(__dirname, '..', '..', '..');
}

export interface WorkerResult {
  ok: boolean;
  stdout: string;
  stderr: string;
  exitCode: number;
}

export async function runPythonWorker(
  packageDir: string,
  moduleName: string,
  args: string[]
): Promise<WorkerResult> {
  const root = repoRoot();
  const cwd = join(root, 'packages', packageDir);
  if (!existsSync(cwd)) {
    return {
      ok: false,
      stdout: '',
      stderr: `Worker package not found: ${cwd}`,
      exitCode: 127,
    };
  }
  // Prefer `uv run` so the per-package environment is respected.
  const cmd = process.platform === 'win32' ? 'uv.cmd' : 'uv';
  return new Promise((resolveP) => {
    const proc = spawn(cmd, ['run', 'python', '-m', moduleName, ...args], {
      cwd,
      env: process.env,
      stdio: ['ignore', 'pipe', 'pipe'],
      shell: process.platform === 'win32',
    });
    const out: Buffer[] = [];
    const err: Buffer[] = [];
    proc.stdout.on('data', (d) => out.push(d));
    proc.stderr.on('data', (d) => err.push(d));
    proc.on('close', (code) => {
      resolveP({
        ok: code === 0,
        stdout: Buffer.concat(out).toString('utf8'),
        stderr: Buffer.concat(err).toString('utf8'),
        exitCode: code ?? 1,
      });
    });
    proc.on('error', (e) => {
      resolveP({ ok: false, stdout: '', stderr: e.message, exitCode: 127 });
    });
  });
}
