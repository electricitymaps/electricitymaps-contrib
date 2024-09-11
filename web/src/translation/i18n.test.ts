import { describe, expect, it } from 'vitest';

import { sanitizeLocale } from './i18n';

describe('sanitizeLocale', () => {
  it.each([
    ['en', 'en'],
    ['en-US', 'en-US'],
    ['fr', 'fr'],
    ['fr-FR', 'fr-FR'],
  ])('should return the locale if it is valid: %s', (input, expected) => {
    expect(sanitizeLocale(input)).toBe(expected);
  });

  it.each([
    ['de).', 'de'],
    ['de-DE-1996', 'de-DE'],
    ['de-DE-1996-1996', 'de-DE'],
  ])('should sanitize partially valid locales: %s', (input, expected) => {
    expect(sanitizeLocale(input)).toBe(expected);
  });

  it.each([
    ['DE-de', 'de-DE'],
    ['DE', 'de'],
  ])('should return the canonical locale if it is valid: %s', (input, expected) => {
    expect(sanitizeLocale(input)).toBe(expected);
  });

  it.each([
    ['e'],
    ['deAT'],
    ['deNOX%20wird'],
    ['itcarbon_intensity'],
    ['carbon_intensity'],
  ])('should return "en" if the locale is invalid', (input) => {
    expect(sanitizeLocale(input)).toBe('en');
  });
});
