const trims = {
  iphone: { width: 390, fontSize: 16, maxW: '390px' },
  kindle: { width: 600, fontSize: 14, maxW: '600px' },
  paperback: { width: 432 /* 6in @ 72dpi */, fontSize: 11, maxW: '432px' },
};

const status = document.getElementById('status');
const select = document.getElementById('chapter');

async function loadChapter(path) {
  status.textContent = 'loading…';
  const res = await fetch('/api/chapter/' + encodeURIComponent(path));
  const html = await res.text();
  if (!res.ok) {
    status.textContent = 'error: ' + html;
    return;
  }
  for (const key of Object.keys(trims)) {
    const frame = document.getElementById('frame-' + key);
    const trim = trims[key];
    frame.srcdoc = `<!doctype html><html><head><meta charset="utf-8"><style>
      body{font-family:Georgia,serif;max-width:${trim.maxW};margin:0;padding:14px;font-size:${trim.fontSize}px;line-height:1.5;}
      pre{background:#f3f3f3;padding:8px;border-radius:4px;overflow:auto;}
      .sw-practitioner-quote{border-left:3px solid #888;background:#f7f7f7;padding:8px 10px;margin:1em 0;}
      .sw-workbook{border:1px solid #aaa;padding:10px;margin:1em 0;border-radius:4px;}
      .sw-visual{border:1px dashed #999;padding:1em;text-align:center;color:#777;}
      .sw-cite{text-decoration:underline dotted;}
      </style></head><body>${html}</body></html>`;
  }
  status.textContent = 'rendered ' + path;
}

async function init() {
  const list = await fetch('/api/chapters').then((r) => r.json());
  for (const c of list) {
    const opt = document.createElement('option');
    opt.value = c;
    opt.textContent = c;
    select.appendChild(opt);
  }
  if (list.length) {
    select.value = list[0];
    await loadChapter(list[0]);
  }
  select.addEventListener('change', () => loadChapter(select.value));

  const ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onmessage = () => {
    status.textContent = 'change detected — reloading…';
    loadChapter(select.value);
  };
  ws.onclose = () => { status.textContent = 'ws disconnected'; };
}

init();
