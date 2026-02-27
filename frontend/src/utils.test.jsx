import { describe, it, expect } from 'vitest';
import { normalizeString, NormalizationType } from './utils';

describe('normalizeString utility', () => {
    // Test 1
    it('formats snake_case strings to Title Case by default', () => {
        const input = 'hello_world_example';
        const result = normalizeString(input);
        expect(result).toBe('Hello World Example');
    });

    // Test 2
    it('respects the UPPER_CASE normalization type', () => {
        const input = 'some_random_text';
        const result = normalizeString(input, NormalizationType.UPPER_CASE);
        expect(result).toBe('SOME RANDOM TEXT');
    });
});