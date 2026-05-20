import { mkdirSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import pc from 'picocolors';
import { loadBook } from '../book.js';
import { runPythonWorker, type WorkerResult } from '../runWorker.js';
import { logEvent } from '../log.js';

export type BuildTarget = 'pdf' | 'epub' | 'ssml' | 'web' | 'aplus' | 'all';

export interface BuildOpts {
  target: BuildTarget;
  outDir: string;
  locale?: string;
  edition?: string;
  parallel?: boolean;
}

const TARGET_MAP: Record<Exclude<BuildTarget, 'all'>, { pkg: string; module: string; parallelSafe: boolean }> = {
  pdf: { pkg: 'renderer-typst', module: 'stitchwork_renderer_typst.cli', parallelSafe: true },
  epub: { pkg: 'renderer-epub', module: 'stitchwork_renderer_epub.cli', parallelSafe: true },
  ssml: { pkg: 'renderer-audio', module: 'stitchwork_renderer_audio.cli', parallelSafe: true },
  web: { pkg: 'renderer-web', module: 'stitchwork_renderer_web.cli', parallelSafe: false },
  aplus: { pkg: 'renderer-aplus', module: 'stitchwork_renderer_aplus.cli', parallelSafe: true },
};

async function runTarget(
  t: Exclude<BuildTarget, 'all'>,
  astPath: string,
  outRoot: string,
  opts: BuildOpts
): Promise<{ target: typeof t; res: WorkerResult; ms: number }> {
  const t0 = Date.now();
  const { pkg, module } = TARGET_MAP[t];
  const res = await runPythonWorker(pkg, module, [
    '--ast', astPath,
    '--out', join(outRoot, t),
    ...(opts.locale ? ['--locale', opts.locale] : []),
    ...(opts.edition ? ['--edition', opts.edition] : []),
  ]);
  return { target: t, res, ms: Date.now() - t0 };
}

export async function runBuild(bookPath: string, opts: BuildOpts): Promise<number> {
  const book = loadBook(bookPath);
  const outRoot = resolve(opts.outDir);
  mkdirSync(outRoot, { recursive: true });
  const tStart = Date.now();
  logEvent({ event: 'build.start', book: book.manifest.id, target: opts.target, locale: opts.locale, edition: opts.edition });

  const astPath = join(outRoot, `${book.manifest.id}.ast.json`);
  const manifestPayload = {
    manifest: book.manifest,
    chapters: book.chapters.map((c) => ({ id: c.id, path: c.path, ast: c.result.ast })),
    locale: opts.locale ?? book.manifest.locale ?? null,
    edition: opts.edition ?? book.manifest.edition ?? null,
  };
  writeFileSync(astPath, JSON.stringify(manifestPayload, null, 2), 'utf8');
  console.log(pc.dim(`  ast → ${astPath}`));

  const targets: Array<Exclude<BuildTarget, 'all'>> =
    opts.target === 'all'
      ? (['pdf', 'epub', 'ssml', 'web', 'aplus'] as const).slice()
      : [opts.target];

  let failures = 0;

  const parallelTargets = opts.parallel ? targets.filter((t) => TARGET_MAP[t].parallelSafe) : [];
  const sequentialTargets = targets.filter((t) => !parallelTargets.includes(t));

  if (parallelTargets.length > 0) {
    console.log(pc.dim(`  running ${parallelTargets.length} parallel target(s)`));
    const results = await Promise.all(parallelTargets.map((t) => runTarget(t, astPath, outRoot, opts)));
    for (const { target, res, ms } of results) {
      const tag = pc.bold(pc.cyan(`[${target}]`));
      if (res.ok) {
        console.log(`${tag} ${pc.green('ok')} (${ms}ms)`);
        logEvent({ event: 'build.target.ok', target, ms });
      } else {
        failures++;
        console.error(`${tag} ${pc.red('failed')} (exit ${res.exitCode}, ${ms}ms)`);
        if (res.stderr.trim()) console.error(pc.red(res.stderr.trim()));
        logEvent({ event: 'build.target.fail', target, ms, exit: res.exitCode });
      }
    }
  }

  for (const t of sequentialTargets) {
    const tag = pc.bold(pc.cyan(`[${t}]`));
    console.log(`${tag} rendering ${book.manifest.id}…`);
    const { res, ms } = await runTarget(t, astPath, outRoot, opts);
    if (res.ok) {
      console.log(`${tag} ${pc.green('ok')} (${ms}ms)`);
      if (res.stdout.trim()) console.log(res.stdout.trim());
      logEvent({ event: 'build.target.ok', target: t, ms });
    } else {
      failures++;
      console.error(`${tag} ${pc.red('failed')} (exit ${res.exitCode}, ${ms}ms)`);
      if (res.stderr.trim()) console.error(pc.red(res.stderr.trim()));
      logEvent({ event: 'build.target.fail', target: t, ms, exit: res.exitCode });
    }
  }

  const totalMs = Date.now() - tStart;
  logEvent({ event: 'build.end', book: book.manifest.id, failures, ms: totalMs });
  console.log(pc.dim(`  total: ${totalMs}ms, failures: ${failures}`));
  return failures === 0 ? 0 : 1;
}
