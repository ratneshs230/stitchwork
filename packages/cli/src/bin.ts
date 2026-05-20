#!/usr/bin/env node
import { Command } from 'commander';
import pc from 'picocolors';
import { runBuild } from './commands/build.js';
import { runPreview } from './commands/preview.js';
import { runValidate } from './commands/validate.js';
import { runPublish } from './commands/publish.js';

const program = new Command();
program
  .name('stitchwork')
  .description('Stitchwork — one source → print, ebook, audiobook, web, A+.')
  .version('0.1.0');

program
  .command('build')
  .description('Render a book to one or more targets')
  .argument('<book>', 'Path to a book directory containing book.yml')
  .option(
    '-t, --target <kind>',
    'Render target: pdf | epub | ssml | web | aplus | all',
    'all'
  )
  .option('-o, --out <dir>', 'Output root directory', 'dist')
  .option('--locale <code>', 'Locale to select for locale-variant directives')
  .option('--edition <ver>', 'Edition to gate edition directives (e.g. 2026.1)')
  .action(async (book: string, opts) => {
    const code = await runBuild(book, {
      target: opts.target,
      outDir: opts.out,
      locale: opts.locale,
      edition: opts.edition,
    });
    process.exit(code);
  });

program
  .command('preview')
  .description('Start a localhost preview with file watching')
  .argument('<book>', 'Path to a book directory')
  .option('-p, --port <num>', 'Listen port', (v) => Number(v), 7777)
  .action(async (book: string, opts) => {
    const code = await runPreview(book, opts.port);
    process.exit(code);
  });

program
  .command('validate')
  .description('Parse, validate directives, and report counts')
  .argument('<book>', 'Path to a book directory')
  .action(async (book: string) => {
    const code = await runValidate(book);
    process.exit(code);
  });

program
  .command('publish')
  .description('Publish to a downstream store (stub until Sprint 10)')
  .argument('<book>', 'Path to a book directory')
  .option('-t, --target <name>', 'Distribution target', 'kdp')
  .action(async (book: string, opts) => {
    const code = await runPublish(book, opts.target);
    process.exit(code);
  });

program.parseAsync(process.argv).catch((err) => {
  console.error(pc.red('fatal:'), (err as Error).message);
  process.exit(2);
});
