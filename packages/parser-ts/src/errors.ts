export class StitchworkParseError extends Error {
  readonly line: number;
  readonly column: number;
  readonly code: string;

  constructor(message: string, code: string, line: number, column = 0) {
    super(`${code} at ${line}:${column} — ${message}`);
    this.name = 'StitchworkParseError';
    this.code = code;
    this.line = line;
    this.column = column;
  }
}

export const ErrorCodes = {
  UNKNOWN_DIRECTIVE: 'SW001',
  UNKNOWN_OPTION: 'SW002',
  MISSING_REQUIRED_OPTION: 'SW003',
  INVALID_OPTION_VALUE: 'SW004',
  UNCLOSED_DIRECTIVE: 'SW005',
  BODY_NOT_ALLOWED: 'SW006',
  CONSTRAINT_VIOLATION: 'SW007',
  UNKNOWN_ROLE: 'SW008',
  MALFORMED_FRONTMATTER: 'SW009',
} as const;
