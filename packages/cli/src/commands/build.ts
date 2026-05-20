import { mkdirSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import pc from 'picocolors';
import { loadBook } from '../book.js';
import { runPythonWorker } from '../runWorker.js';

export type BuildTarget = 'pdf' | 'epub' | 'ssml' | 'web' | 'aplus' | 'all';

export interface BuildOpts {
  target: BuildTarget;
  outDir: string;
  locale?: string;
  edition?: string;
}

const TARGET_MAP: Record<Exclude<BuildTarget, 'all'>, { pkg: string; module: string }> = {
  pdf: { pkg: 'renderer-typst', module: 'stitchwork_renderer_typst.cli' },
  epub: { pkg: 'renderer-epub', module: 'stitchwork_renderer_epub.cli' },
  ssml: { pkg: 'renderer-audio', module: 'stitchwork_renderer_audio.cli' },
  web: { pkg: 'renderer-web', module: 'stitchwork_renderer_web.cli' },
  aplus: { pkg: 'renderer-aplus', module: 'stitchwork_renderer_aplus.cli' },
};

export async function runBuild(bookPath: string, opts: BuildOpts): Promise<number> {
  const book = loadBook(bookPath);
  const outRoot = resolve(opts.outDir);
  mkdirSync(outRoot, { recursive: true });

  // Persist AST manifest so workers can consume it deterministically
  const astPath = join(outRoot, `${book.manifest.id}.ast.json`);
  const manifestPayload = {
    manifest: book.manifest,
    chapters: book.chapters.map((c) => ({
      id: c.id,
      path: c.path,
      ast: c.result.ast,
    })),
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
  for (const t of targets) {
    const tag = pc.bold(pc.cyan(`[${t}]`));
    console.log(`${tag} rendering ${book.manifest.id}…`);
    const { pkg, module } = TARGET_MAP[t];
    const res = await runPythonWorker(pkg, module, [
      '--ast',
      astPath,
      '--out',
      join(outRoot, t),
      ...(opts.locale ? ['--locale', opts.locale] : []),
      ...(opts.edition ? ['--edition', opts.edition] : []),
    ]);
    if (res.ok) {
      console.log(`${tag} ${pc.green('ok')}`);
      if (res.stdout.trim()) console.log(res.stdout.trim());
    } else {
      failures++;
      console.error(`${tag} ${pc.red('failed')} (exit ${res.exitCode})`);
      if (res.stderr.trim()) console.error(pc.red(res.stderr.trim()));
    }
  }
  return failures === 0 ? 0 : 1;
}
