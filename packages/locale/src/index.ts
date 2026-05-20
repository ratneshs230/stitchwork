/** Locale + edition resolver — single source of truth, mirrored in renderer-typst/filters.py */

interface DirectiveNode {
  type: 'directive';
  name: string;
  options: Record<string, unknown>;
  children: unknown[];
}

function isDirective(node: unknown, name: string): node is DirectiveNode {
  return (
    typeof node === 'object' &&
    node !== null &&
    (node as { type?: string }).type === 'directive' &&
    (node as { name?: string }).name === name
  );
}

function verTuple(v: string): number[] {
  return v.split('.').map((p) => Number(p));
}

function verCmp(a: number[], b: number[]): number {
  const n = Math.max(a.length, b.length);
  for (let i = 0; i < n; i++) {
    const ai = a[i] ?? 0;
    const bi = b[i] ?? 0;
    if (ai !== bi) return ai - bi;
  }
  return 0;
}

export function editionIncludes(opts: Record<string, unknown>, active: string | null): boolean {
  if (active === null) return true;
  const av = verTuple(active);
  let since = opts.since as string | undefined;
  let until = opts.until as string | undefined;
  const range = opts.range as string | undefined;
  if (range && range.includes('-')) {
    const [lo, hi] = range.split('-');
    since ||= lo.trim();
    until ||= hi.trim();
  }
  if (since && verCmp(av, verTuple(since)) < 0) return false;
  if (until && verCmp(av, verTuple(until)) >= 0) return false;
  return true;
}

export function localeMatches(opts: Record<string, unknown>, active: string | null): boolean {
  if (active === null) return true;
  const locales = (opts.locales as string[] | undefined) ?? [];
  const primary = active.split('-')[0].toUpperCase();
  const full = active.toUpperCase();
  return locales.some((l) => {
    const lu = l.toUpperCase();
    return lu === full || lu === primary || full.startsWith(lu + '-');
  });
}

export interface FilterOptions {
  locale: string | null;
  edition: string | null;
}

export function applyFilters<T extends { children?: T[] }>(
  nodes: T[],
  { locale, edition }: FilterOptions
): T[] {
  const out: T[] = [];
  let i = 0;
  while (i < nodes.length) {
    const node = nodes[i] as unknown;
    if (isDirective(node, 'locale-variant')) {
      const group: DirectiveNode[] = [];
      while (i < nodes.length && isDirective(nodes[i], 'locale-variant')) {
        group.push(nodes[i] as DirectiveNode);
        i++;
      }
      const matched = group.filter((g) => localeMatches(g.options, locale));
      const chosen =
        matched.length > 0
          ? matched
          : group.filter((g) => (g.options as { fallback?: boolean }).fallback === true);
      for (const g of chosen) {
        out.push({ ...(g as unknown as T), children: applyFilters(g.children as unknown as T[], { locale, edition }) });
      }
      continue;
    }
    if (isDirective(node, 'edition')) {
      if (editionIncludes(node.options, edition)) {
        out.push({ ...(node as unknown as T), children: applyFilters((node.children as unknown as T[]) ?? [], { locale, edition }) });
      }
      i++;
      continue;
    }
    const generic = node as { children?: T[] };
    if (generic.children) {
      out.push({ ...(node as T), children: applyFilters(generic.children, { locale, edition }) });
    } else {
      out.push(node as T);
    }
    i++;
  }
  return out;
}
