import pc from 'picocolors';

export async function runPublish(_bookPath: string, target: string): Promise<number> {
  console.error(
    pc.yellow('publish is not implemented in v0.1.0 — landing in Sprint 10 (production hardening)')
  );
  console.error(pc.dim(`target requested: ${target}`));
  return 64; // EX_USAGE
}
