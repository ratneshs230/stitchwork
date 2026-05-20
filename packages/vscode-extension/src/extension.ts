import * as vscode from 'vscode';
import { spawn, type ChildProcess } from 'node:child_process';
import { parse, StitchworkParseError } from '@stitchwork/parser-ts';

let previewProc: ChildProcess | undefined;

export function activate(context: vscode.ExtensionContext): void {
  const diag = vscode.languages.createDiagnosticCollection('stitchwork');
  context.subscriptions.push(diag);

  const validateDoc = (doc: vscode.TextDocument) => {
    if (!['stitchwork-myst', 'markdown'].includes(doc.languageId)) return;
    if (!/\.swk\.md$|\.myst$/.test(doc.fileName) && doc.languageId !== 'stitchwork-myst') return;
    try {
      parse(doc.getText());
      diag.set(doc.uri, []);
    } catch (e) {
      if (e instanceof StitchworkParseError) {
        const range = new vscode.Range(
          Math.max(0, e.line - 1),
          0,
          Math.max(0, e.line - 1),
          Number.MAX_SAFE_INTEGER
        );
        diag.set(doc.uri, [
          new vscode.Diagnostic(range, e.message, vscode.DiagnosticSeverity.Error),
        ]);
      }
    }
  };

  context.subscriptions.push(vscode.workspace.onDidOpenTextDocument(validateDoc));
  context.subscriptions.push(vscode.workspace.onDidSaveTextDocument(validateDoc));
  context.subscriptions.push(
    vscode.workspace.onDidChangeTextDocument((e) => validateDoc(e.document))
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('stitchwork.preview', async () => {
      const ws = vscode.workspace.workspaceFolders?.[0];
      if (!ws) {
        vscode.window.showErrorMessage('Open a book directory first.');
        return;
      }
      const cfg = vscode.workspace.getConfiguration('stitchwork');
      const cli = cfg.get<string>('cliPath') || 'stitchwork';
      const port = cfg.get<number>('previewPort') || 7777;
      if (previewProc) {
        previewProc.kill();
      }
      previewProc = spawn(cli, ['preview', ws.uri.fsPath, '--port', String(port)], {
        cwd: ws.uri.fsPath,
        shell: true,
      });
      previewProc.stdout?.on('data', (d) => console.log('[sw]', d.toString()));
      previewProc.stderr?.on('data', (d) => console.error('[sw]', d.toString()));
      const url = vscode.Uri.parse(`http://localhost:${port}`);
      setTimeout(() => vscode.env.openExternal(url), 700);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('stitchwork.outline', async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) return;
      const items: vscode.QuickPickItem[] = [];
      const lines = editor.document.getText().split(/\r?\n/);
      for (let i = 0; i < lines.length; i++) {
        const m = /^(#{1,6})\s+(.+)$/.exec(lines[i]);
        if (m) items.push({ label: '#'.repeat(m[1].length) + ' ' + m[2], description: `line ${i + 1}`, detail: String(i) });
        const dm = /^:::\{([a-z][a-z0-9-]*)\}/.exec(lines[i]);
        if (dm) items.push({ label: `directive: ${dm[1]}`, description: `line ${i + 1}`, detail: String(i) });
      }
      const picked = await vscode.window.showQuickPick(items, { placeHolder: 'Outline + directives' });
      if (picked?.detail) {
        const line = Number(picked.detail);
        editor.revealRange(new vscode.Range(line, 0, line, 0), vscode.TextEditorRevealType.AtTop);
        editor.selection = new vscode.Selection(line, 0, line, 0);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('stitchwork.validate', async () => {
      const ws = vscode.workspace.workspaceFolders?.[0];
      if (!ws) {
        vscode.window.showErrorMessage('Open a book directory first.');
        return;
      }
      const cli = vscode.workspace.getConfiguration('stitchwork').get<string>('cliPath') || 'stitchwork';
      const term = vscode.window.createTerminal('Stitchwork');
      term.sendText(`${cli} validate ${ws.uri.fsPath}`);
      term.show();
    })
  );
}

export function deactivate(): void {
  previewProc?.kill();
  previewProc = undefined;
}
