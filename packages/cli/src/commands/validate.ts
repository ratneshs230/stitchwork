import pc from 'picocolors';
import { loadBook } from '../book.js';
import { StitchworkParseError } from '@stitchwork/parser-ts';

export async function runValidate(bookPath: string): Promise<number> {
  let failures = 0;
  try {
    const book = loadBook(bookPath);
    console.log(pc.green('✓'), `book.yml + ${book.chapters.length} chapter(s) parsed clean`);
    let directiveCount = 0;
    let roleCount = 0;
    for (const ch of book.chapters) {
      const counts = countDirectivesAndRoles(ch.result.ast);
      directiveCount += counts.directives;
      roleCount += counts.roles;
    }
    console.log(
      pc.dim(`  ${directiveCount} directive instances, ${roleCount} role instances total`)
    );
  } catch (e) {
    failures++;
    if (e instanceof StitchworkParseError) {
      console.error(pc.red('✗ parser'), e.message);
    } else {
      console.error(pc.red('✗ validate'), (e as Error).message);
    }
  }
  // External-tool validators (EPUBCheck, Ace, Ghostscript -dPDFX) are wired
  // via the CI workflow; locally they're best-effort and reported separately
  // by the renderer-specific validate subcommands once those packages exist.
  return failures === 0 ? 0 : 1;
}

function countDirectivesAndRoles(node: unknown): { directives: number; roles: number } {
  let directives = 0;
  let roles = 0;
  const walk = (n: unknown) => {
    if (!n || typeof n !== 'object') return;
    const t = (n as { type?: string }).type;
    if (t === 'directive') directives++;
    if (t === 'role') roles++;
    const children = (n as { children?: unknown[] }).children;
    if (Array.isArray(children)) for (const c of children) walk(c);
  };
  walk(node);
  return { directives, roles };
}
