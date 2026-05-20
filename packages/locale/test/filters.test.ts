import { describe, it, expect } from 'vitest';
import { applyFilters, editionIncludes, localeMatches } from '../src/index.js';

describe('locale + edition resolver (TS mirror of renderer-typst/filters.py)', () => {
  it('editionIncludes since-only', () => {
    expect(editionIncludes({ since: '2026.1' }, '2026.2')).toBe(true);
    expect(editionIncludes({ since: '2026.1' }, '2026.0')).toBe(false);
  });

  it('editionIncludes range', () => {
    expect(editionIncludes({ range: '2026.1-2027.1' }, '2026.5')).toBe(true);
    expect(editionIncludes({ range: '2026.1-2027.1' }, '2027.1')).toBe(false);
  });

  it('localeMatches primary tag', () => {
    expect(localeMatches({ locales: ['IN'] }, 'en-IN')).toBe(true);
    expect(localeMatches({ locales: ['US'] }, 'en-IN')).toBe(false);
  });

  it('applyFilters keeps matching variant', () => {
    const nodes = [
      { type: 'directive', name: 'locale-variant', options: { locales: ['IN'] }, children: [{ type: 'text', value: 'in' }] },
      { type: 'directive', name: 'locale-variant', options: { locales: ['US'] }, children: [{ type: 'text', value: 'us' }] },
    ];
    const out = applyFilters(nodes, { locale: 'en-IN', edition: null });
    expect(out.length).toBe(1);
    expect((out[0] as { options: { locales: string[] } }).options.locales).toEqual(['IN']);
  });

  it('applyFilters uses fallback', () => {
    const nodes = [
      { type: 'directive', name: 'locale-variant', options: { locales: ['US'] }, children: [{ type: 'text', value: 'us' }] },
      { type: 'directive', name: 'locale-variant', options: { locales: ['UK'], fallback: true }, children: [{ type: 'text', value: 'uk' }] },
    ];
    const out = applyFilters(nodes, { locale: 'en-IN', edition: null });
    expect(out.length).toBe(1);
    expect((out[0] as { options: { fallback?: boolean } }).options.fallback).toBe(true);
  });
});
