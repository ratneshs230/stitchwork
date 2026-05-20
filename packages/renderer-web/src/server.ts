import { createServer } from 'node:http';
import { readFileSync, existsSync, statSync, readdirSync } from 'node:fs';
import { join, resolve, extname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';
import chokidar from 'chokidar';
import { WebSocketServer } from 'ws';
import { parse } from '@stitchwork/parser-ts';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const MIME: Record<string, string> = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
};

function uiDir(): string {
  return resolve(__dirname, '..', 'ui');
}

export interface PreviewServer {
  url: string;
  close: () => Promise<void>;
}

export async function startPreviewServer(bookPath: string, port: number): Promise<PreviewServer> {
  const bookAbs = resolve(bookPath);
  if (!existsSync(bookAbs)) throw new Error(`book path missing: ${bookAbs}`);

  const renderChapter = (relPath: string): string => {
    const full = join(bookAbs, relPath);
    if (!existsSync(full)) throw new Error(`chapter missing: ${full}`);
    const src = readFileSync(full, 'utf8');
    const { ast } = parse(src);
    return astToHtml(ast);
  };

  const listChapters = (): string[] => {
    const dir = join(bookAbs, 'chapters');
    if (!existsSync(dir)) return [];
    return readdirSync(dir)
      .filter((f) => f.endsWith('.md'))
      .map((f) => join('chapters', f));
  };

  const server = createServer((req, res) => {
    const urlPath = (req.url || '/').split('?')[0];
    if (urlPath === '/' || urlPath === '/index.html') {
      const html = readFileSync(join(uiDir(), 'index.html'), 'utf8');
      res.writeHead(200, { 'content-type': MIME['.html'] });
      res.end(html);
      return;
    }
    if (urlPath.startsWith('/api/chapters')) {
      const list = listChapters();
      res.writeHead(200, { 'content-type': MIME['.json'] });
      res.end(JSON.stringify(list));
      return;
    }
    if (urlPath.startsWith('/api/chapter/')) {
      const rel = decodeURIComponent(urlPath.replace('/api/chapter/', ''));
      try {
        const html = renderChapter(rel);
        res.writeHead(200, { 'content-type': MIME['.html'] });
        res.end(html);
      } catch (e) {
        res.writeHead(500, { 'content-type': 'text/plain' });
        res.end((e as Error).message);
      }
      return;
    }
    // Static UI files
    const candidate = join(uiDir(), urlPath);
    if (existsSync(candidate) && statSync(candidate).isFile()) {
      res.writeHead(200, { 'content-type': MIME[extname(candidate)] ?? 'application/octet-stream' });
      res.end(readFileSync(candidate));
      return;
    }
    res.writeHead(404);
    res.end('not found');
  });

  // WebSocket for live-reload notifications
  const wss = new WebSocketServer({ noServer: true });
  server.on('upgrade', (req, socket, head) => {
    if (req.url === '/ws') {
      wss.handleUpgrade(req, socket, head, (ws) => wss.emit('connection', ws, req));
    }
  });

  const watcher = chokidar.watch(join(bookAbs, 'chapters'), { ignoreInitial: true });
  watcher.on('all', (event, path) => {
    wss.clients.forEach((c) => {
      try {
        c.send(JSON.stringify({ kind: 'change', event, path }));
      } catch {
        // ignore
      }
    });
  });

  await new Promise<void>((res2) => server.listen(port, () => res2()));
  const url = `http://localhost:${port}`;

  return {
    url,
    close: async () => {
      await watcher.close();
      wss.close();
      await new Promise<void>((res2) => server.close(() => res2()));
    },
  };
}

// Minimal AST → HTML renderer for preview (heavier renderer lives in EPUB worker)
function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]!));
}

function astToHtml(node: unknown): string {
  if (!node || typeof node !== 'object') return '';
  const n = node as { type: string; children?: unknown[]; value?: string; depth?: number; name?: string; options?: Record<string, unknown>; text?: string; id?: string; ordered?: boolean; lang?: string };
  switch (n.type) {
    case 'root':
      return (n.children || []).map(astToHtml).join('');
    case 'heading':
      return `<h${n.depth ?? 1} id="${escapeHtml(n.id || '')}">${(n.children || []).map(astToHtml).join('')}</h${n.depth ?? 1}>`;
    case 'paragraph':
      return `<p>${(n.children || []).map(astToHtml).join('')}</p>`;
    case 'text':
      return escapeHtml(n.value || '');
    case 'strong':
      return `<strong>${(n.children || []).map(astToHtml).join('')}</strong>`;
    case 'emphasis':
      return `<em>${(n.children || []).map(astToHtml).join('')}</em>`;
    case 'inlineCode':
      return `<code>${escapeHtml(n.value || '')}</code>`;
    case 'code':
      return `<pre><code class="lang-${escapeHtml(n.lang || '')}">${escapeHtml(n.value || '')}</code></pre>`;
    case 'thematicBreak':
      return '<hr/>';
    case 'list': {
      const tag = n.ordered ? 'ol' : 'ul';
      return `<${tag}>${(n.children || []).map(astToHtml).join('')}</${tag}>`;
    }
    case 'listItem':
      return `<li>${(n.children || []).map(astToHtml).join('')}</li>`;
    case 'directive': {
      const inner = (n.children || []).map(astToHtml).join('');
      const opts = JSON.stringify(n.options || {});
      return `<section class="sw-directive sw-${escapeHtml(n.name || '')}" data-options='${escapeHtml(opts)}'>${inner}</section>`;
    }
    case 'role':
      return `<span class="sw-role sw-${escapeHtml(n.name || '')}">${escapeHtml(n.text || '')}</span>`;
    default:
      return '';
  }
}
