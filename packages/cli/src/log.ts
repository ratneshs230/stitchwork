/** Structured-log emitter — JSONL when STITCHWORK_LOG_JSON=1, otherwise no-op. */

export type LogRecord = Record<string, unknown> & { event: string };

export function logEvent(record: LogRecord): void {
  if (process.env.STITCHWORK_LOG_JSON !== '1') return;
  const payload = { ts: new Date().toISOString(), ...record };
  // eslint-disable-next-line no-console
  process.stderr.write(JSON.stringify(payload) + '\n');
}
