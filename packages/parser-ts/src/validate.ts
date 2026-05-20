import { schemas, type DirectiveSpec, type OptionSpec } from '@stitchwork/shared-schemas';
import { ErrorCodes, StitchworkParseError } from './errors.js';

interface ValidateArgs {
  directiveName: string;
  rawOptions: Record<string, string>;
  hasBody: boolean;
  line: number;
}

const LOCALE_RE = /^[A-Z]{2}(-[A-Z]{2,3})?$/;
const EDITION_RE = /^\d{4}\.\d+(\.\d+)?$/;
const DATE_TIME_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?(Z|[+-]\d{2}:?\d{2})?$/;

function resolveRef(ref: string): OptionSpec {
  const name = ref.replace('#/definitions/', '');
  const def = (schemas.definitions as Record<string, OptionSpec> | undefined)?.[name];
  if (!def) {
    throw new Error(`Internal: unresolvable schema $ref "${ref}"`);
  }
  return def;
}

function effective(spec: OptionSpec): OptionSpec {
  if (spec.$ref) {
    return { ...resolveRef(spec.$ref), required: spec.required };
  }
  return spec;
}

function parseScalar(value: string, spec: OptionSpec): unknown {
  const eff = effective(spec);
  switch (eff.type) {
    case 'integer': {
      const n = Number.parseInt(value.trim(), 10);
      if (!Number.isFinite(n)) {
        throw new Error(`expected integer, got "${value}"`);
      }
      return n;
    }
    case 'boolean': {
      const t = value.trim().toLowerCase();
      if (t === 'true' || t === 'yes' || t === '1') return true;
      if (t === 'false' || t === 'no' || t === '0') return false;
      throw new Error(`expected boolean, got "${value}"`);
    }
    case 'array': {
      const trimmed = value.trim();
      let parts: string[];
      if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
        parts = trimmed
          .slice(1, -1)
          .split(',')
          .map((p) => p.trim())
          .filter((p) => p.length > 0);
      } else {
        parts = trimmed.split(',').map((p) => p.trim()).filter((p) => p.length > 0);
      }
      if (eff.minItems !== undefined && parts.length < eff.minItems) {
        throw new Error(`array needs ≥${eff.minItems} items, got ${parts.length}`);
      }
      if (eff.items) {
        for (const p of parts) {
          checkScalar(p, eff.items);
        }
      }
      return parts;
    }
    case 'string':
    default:
      checkScalar(value, eff);
      return value;
  }
}

function checkScalar(value: string, spec: OptionSpec): void {
  const eff = effective(spec);
  if (eff.pattern && !new RegExp(eff.pattern).test(value)) {
    throw new Error(`value "${value}" does not match pattern /${eff.pattern}/`);
  }
  if (eff.enum && !eff.enum.includes(value)) {
    throw new Error(`value "${value}" not in {${eff.enum.join(', ')}}`);
  }
  if (eff.format === 'uri') {
    try {
      new URL(value);
    } catch {
      throw new Error(`value "${value}" is not a valid URI`);
    }
  }
  if (eff.format === 'date-time' && !DATE_TIME_RE.test(value)) {
    throw new Error(`value "${value}" is not a valid date-time`);
  }
  // explicit locale / edition refs come through $ref
  if (spec.$ref === '#/definitions/locale' && !LOCALE_RE.test(value)) {
    throw new Error(`value "${value}" is not a valid locale`);
  }
  if (spec.$ref === '#/definitions/editionVersion' && !EDITION_RE.test(value)) {
    throw new Error(`value "${value}" is not a valid edition version`);
  }
  if (eff.minLength !== undefined && value.length < eff.minLength) {
    throw new Error(`value too short (min ${eff.minLength}, got ${value.length})`);
  }
}

function checkConstraints(
  spec: DirectiveSpec,
  resolved: Record<string, unknown>,
  line: number
): void {
  if (!spec.constraints) return;
  for (const c of spec.constraints) {
    const [kind, fieldsRaw] = c.split(':').map((s) => s.trim());
    if (!fieldsRaw) continue;
    const fields = fieldsRaw.split(',').map((f) => f.trim());
    const present = fields.filter((f) => resolved[f] !== undefined);
    if (kind === 'at_least_one_of' && present.length === 0) {
      throw new StitchworkParseError(
        `at least one of {${fields.join(', ')}} is required`,
        ErrorCodes.CONSTRAINT_VIOLATION,
        line
      );
    }
    if (kind === 'exactly_one_of' && present.length !== 1) {
      throw new StitchworkParseError(
        `exactly one of {${fields.join(', ')}} required (got ${present.length})`,
        ErrorCodes.CONSTRAINT_VIOLATION,
        line
      );
    }
  }
}

export function validateOptions({
  directiveName,
  rawOptions,
  hasBody,
  line,
}: ValidateArgs): Record<string, unknown> {
  const spec = schemas.directives[directiveName as keyof typeof schemas.directives];
  if (!spec) {
    throw new StitchworkParseError(
      `unknown directive "${directiveName}"`,
      ErrorCodes.UNKNOWN_DIRECTIVE,
      line
    );
  }

  if (spec.kind === 'block' && spec.hasBody === false && hasBody) {
    throw new StitchworkParseError(
      `directive "${directiveName}" does not accept a body`,
      ErrorCodes.BODY_NOT_ALLOWED,
      line
    );
  }

  const resolved: Record<string, unknown> = {};
  // unknown options: reject
  for (const key of Object.keys(rawOptions)) {
    if (!(key in spec.options)) {
      throw new StitchworkParseError(
        `unknown option "${key}" on directive "${directiveName}"`,
        ErrorCodes.UNKNOWN_OPTION,
        line
      );
    }
  }
  // parse + per-field validate
  for (const [key, optSpec] of Object.entries(spec.options)) {
    const raw = rawOptions[key];
    if (raw === undefined) {
      if (optSpec.required) {
        throw new StitchworkParseError(
          `missing required option "${key}" on directive "${directiveName}"`,
          ErrorCodes.MISSING_REQUIRED_OPTION,
          line
        );
      }
      if (optSpec.default !== undefined) {
        resolved[key] = optSpec.default;
      }
      continue;
    }
    try {
      resolved[key] = parseScalar(raw, optSpec);
    } catch (e) {
      throw new StitchworkParseError(
        `option "${key}" on "${directiveName}": ${(e as Error).message}`,
        ErrorCodes.INVALID_OPTION_VALUE,
        line
      );
    }
  }

  checkConstraints(spec, resolved, line);
  return resolved;
}
