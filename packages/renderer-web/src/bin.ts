#!/usr/bin/env node
import { startPreviewServer } from './server.js';

async function main() {
  let book: string | null = null;
  let port = 7777;
  const args = process.argv.slice(2);
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--book') book = args[++i];
    else if (args[i] === '--port') port = Number(args[++i]);
  }
  if (!book) {
    console.error('usage: stitchwork-preview --book <path> [--port N]');
    process.exit(2);
  }
  const srv = await startPreviewServer(book, port);
  console.log(`stitchwork preview ready at ${srv.url}`);
  const stop = async () => {
    await srv.close();
    process.exit(0);
  };
  process.on('SIGINT', stop);
  process.on('SIGTERM', stop);
}

main().catch((e) => {
  console.error((e as Error).message);
  process.exit(1);
});
