/**
 * Tests for utility functions
 */

import { describe, it, expect } from 'vitest';
import {
  detectDocumentationType,
  sanitizeName,
  generateToolName,
  safeJsonParse,
} from '../utils/helpers.js';

describe('detectDocumentationType', () => {
  it('should detect OpenAPI from URL', () => {
    expect(detectDocumentationType('https://api.com/openapi.json', '')).toBe('openapi');
    expect(detectDocumentationType('https://api.com/swagger.yaml', '')).toBe('openapi');
  });

  it('should detect OpenAPI from content', () => {
    expect(detectDocumentationType('', '{"openapi": "3.0.0"}')).toBe('openapi');
    expect(detectDocumentationType('', 'openapi: 3.0.0')).toBe('openapi');
  });

  it('should detect HTML from content', () => {
    expect(detectDocumentationType('', '<html><body>API Docs</body></html>')).toBe('html');
    expect(detectDocumentationType('', '<!DOCTYPE html>')).toBe('html');
  });

  it('should default to markdown', () => {
    expect(detectDocumentationType('', '# API Documentation')).toBe('markdown');
  });
});

describe('sanitizeName', () => {
  it('should sanitize names to valid identifiers', () => {
    expect(sanitizeName('get-users')).toBe('get_users');
    expect(sanitizeName('user.name')).toBe('user_name');
    expect(sanitizeName('123start')).toBe('_123start');
    expect(sanitizeName('hello___world')).toBe('hello_world');
  });
});

describe('generateToolName', () => {
  it('should generate tool names from method and path', () => {
    expect(generateToolName('GET', '/users')).toBe('getUsers');
    expect(generateToolName('POST', '/api/users')).toBe('postApiUsers');
    expect(generateToolName('DELETE', '/users/{id}')).toBe('deleteUsers');
  });
});

describe('safeJsonParse', () => {
  it('should parse valid JSON', () => {
    const result = safeJsonParse('{"key": "value"}');
    expect(result).toEqual({ key: 'value' });
  });

  it('should throw error for invalid JSON', () => {
    expect(() => safeJsonParse('invalid json')).toThrow('Invalid JSON');
  });
});
