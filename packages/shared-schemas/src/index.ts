import schemaJson from '../directives.json' with { type: 'json' };

export type DirectiveKind = 'block' | 'role';
export type HumanEdits = 'none' | 'light' | 'heavy' | 'rewrite';
export type VisualRole =
  | 'hero'
  | 'chart'
  | 'diagram'
  | 'infographic'
  | 'screenshot'
  | 'photo'
  | 'illustration';
export type WorkbookKind = 'reflection' | 'fill' | 'checklist' | 'rating' | 'freeform';

export interface OptionSpec {
  type: 'string' | 'integer' | 'boolean' | 'array';
  required?: boolean;
  pattern?: string;
  format?: string;
  enum?: string[];
  minimum?: number;
  maximum?: number;
  minItems?: number;
  minLength?: number;
  items?: OptionSpec;
  $ref?: string;
  default?: unknown;
}

export interface DirectiveSpec {
  kind: DirectiveKind;
  hasBody?: boolean;
  options: Record<string, OptionSpec>;
  constraints?: string[];
}

export interface SchemaDoc {
  definitions: Record<string, OptionSpec>;
  directives: Record<string, DirectiveSpec>;
}

export const schemas = schemaJson as unknown as SchemaDoc;

export const directiveNames: ReadonlyArray<keyof typeof schemas.directives> = Object.keys(
  schemas.directives
) as Array<keyof typeof schemas.directives>;

export function getDirective(name: string): DirectiveSpec | undefined {
  return schemas.directives[name as keyof typeof schemas.directives];
}

export function isKnownDirective(name: string): boolean {
  return name in schemas.directives;
}
