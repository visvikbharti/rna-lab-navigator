/**
 * Basic test to ensure Jest is working
 */

describe('Basic Tests', () => {
  test('should pass basic assertion', () => {
    expect(true).toBe(true);
  });

  test('should perform basic math', () => {
    expect(1 + 1).toBe(2);
  });
});