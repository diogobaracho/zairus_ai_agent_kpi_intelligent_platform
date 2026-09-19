import { describe, expect, it } from 'vitest';
import { formatDuration, formatValue, pctChange, statusTone } from './format';

describe('format helpers', () => {
  it('formats values by unit', () => {
    expect(formatValue(627.45, '$MM')).toBe('$627.45MM');
    expect(formatValue(164.22, '$')).toBe('$164.22');
    expect(formatValue(285339, 'customers')).toBe('285.3K customers');
    expect(formatValue(2_500_000, 'units')).toBe('2.50M units');
    expect(formatValue(null, '$')).toBe('—');
  });
  it('percent change, duration, tone', () => {
    expect(pctChange(110, 100)).toBe('+10.0%');
    expect(pctChange(90, 100)).toBe('-10.0%');
    expect(pctChange(1, 0)).toBe('—');
    expect(formatDuration(12)).toBe('12 ms');
    expect(formatDuration(1500)).toBe('1.50 s');
    expect(statusTone('ok')).toBe('ok');
    expect(statusTone('rejected')).toBe('warn');
    expect(statusTone('timeout')).toBe('bad');
  });
});
