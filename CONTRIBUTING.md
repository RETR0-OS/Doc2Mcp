# Contributing to Doc2MCP

Thank you for your interest in contributing to Doc2MCP! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/RETR0-OS/Doc2Mcp.git
   cd Doc2Mcp
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Build the project**
   ```bash
   npm run build
   ```

4. **Run tests**
   ```bash
   npm test
   ```

5. **Run in development mode**
   ```bash
   npm run dev
   ```

## Project Structure

```
doc2mcp/
├── src/
│   ├── __tests__/         # Test files
│   ├── parsers/           # Documentation parsers
│   ├── generators/        # Tool and schema generators
│   ├── observability/     # OpenTelemetry integration
│   ├── server/           # MCP server implementation
│   ├── types/            # TypeScript types
│   └── utils/            # Utility functions
├── dist/                 # Compiled output
└── docs/                 # Documentation
```

## Coding Standards

### TypeScript

- Use strict TypeScript settings
- Always provide explicit types for function parameters and return values
- Use interfaces for object shapes
- Prefer `const` over `let`
- Use arrow functions where appropriate

### Code Style

- Run `npm run lint` before committing
- Run `npm run format` to auto-format code
- Follow existing code patterns
- Keep functions small and focused
- Write descriptive variable and function names

### Testing

- Write tests for all new features
- Maintain test coverage above 80%
- Use descriptive test names
- Test both success and error cases
- Mock external dependencies

Example test:
```typescript
describe('MyFeature', () => {
  it('should do something specific', () => {
    // Arrange
    const input = 'test';
    
    // Act
    const result = myFunction(input);
    
    // Assert
    expect(result).toBe('expected');
  });
});
```

## Adding New Features

### Adding a New Parser

1. Create a new file in `src/parsers/`
2. Implement the parser interface:
   ```typescript
   export class MyParser {
     async parse(content: string, sourceUrl: string): Promise<APIDocumentation> {
       // Implementation
     }
   }
   ```
3. Add tests in `src/__tests__/`
4. Update `src/parsers/index.ts` to include new parser
5. Update documentation

### Adding New Tool Capabilities

1. Extend `src/types/index.ts` with new types
2. Update `src/generators/tool-generator.ts`
3. Add tests
4. Update README with examples

### Adding Observability Features

1. Extend `src/observability/tracing.ts`
2. Add new span attributes
3. Test tracing in integration tests
4. Document new observability features

## Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test changes
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `chore:` Build process or auxiliary tool changes

Examples:
```
feat: add support for GraphQL schema parsing
fix: handle missing base URL in OpenAPI specs
docs: update deployment guide with Kubernetes example
test: add integration tests for HTML parser
```

## Pull Request Process

1. **Fork the repository** and create your branch from `main`
   ```bash
   git checkout -b feat/my-new-feature
   ```

2. **Make your changes**
   - Write or update tests
   - Update documentation
   - Follow coding standards

3. **Test your changes**
   ```bash
   npm run build
   npm test
   npm run lint
   ```

4. **Commit your changes**
   ```bash
   git commit -m "feat: add new feature"
   ```

5. **Push to your fork**
   ```bash
   git push origin feat/my-new-feature
   ```

6. **Create a Pull Request**
   - Provide a clear description
   - Reference any related issues
   - Include screenshots for UI changes
   - Ensure CI passes

## Testing Guidelines

### Unit Tests

Test individual functions and classes in isolation:

```typescript
describe('generateToolName', () => {
  it('should generate correct tool names', () => {
    expect(generateToolName('GET', '/users')).toBe('getUsers');
  });
});
```

### Integration Tests

Test multiple components working together:

```typescript
describe('Full pipeline', () => {
  it('should parse and generate tools', async () => {
    const parser = new DocumentationParser();
    const generator = new ToolGenerator();
    const doc = await parser.parseFromUrl(url);
    const tools = generator.generateTools(doc);
    expect(tools.length).toBeGreaterThan(0);
  });
});
```

### E2E Tests

Test the server end-to-end (when applicable):

```typescript
describe('Server', () => {
  it('should handle tool requests', async () => {
    const server = new Doc2MCPServer(config);
    await server.initialize();
    // Test server operations
  });
});
```

## Documentation

- Update README.md for user-facing changes
- Update code comments for implementation details
- Add JSDoc comments for public APIs
- Update EXAMPLE.md with new examples
- Update DEPLOYMENT.md for deployment changes

## Security

- Never commit secrets or API keys
- Validate all user inputs
- Handle errors gracefully
- Use secure dependencies
- Report security issues privately

## Getting Help

- Open an issue for bugs or feature requests
- Join discussions for questions
- Check existing issues before creating new ones

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Assume good intentions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
