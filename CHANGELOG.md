# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-18

### Added

#### Phase 1: Project Setup & Configuration
- TypeScript project configuration with strict mode
- Package.json with all core dependencies
- ESLint and Prettier configuration
- Build and development scripts
- .gitignore for node_modules and build artifacts

#### Phase 2: Documentation Parsing
- OpenAPI/Swagger 2.0 and 3.0 parser supporting JSON and YAML
- HTML documentation parser with endpoint extraction
- Markdown documentation parser with pattern matching
- Unified documentation model and types
- URL fetching with error handling
- Automatic documentation type detection

#### Phase 3: Tool Generation
- Zod schema generation from API parameters
- JSON Schema conversion for MCP compatibility
- Tool handler implementation with HTTP execution
- Parameter extraction (path, query, header, body)
- Response handling with status codes
- Tool metadata with source lineage

#### Phase 4: Arize Observability Integration
- OpenTelemetry tracing setup
- Arize Phoenix OTLP exporter configuration
- Span creation for tool executions
- Documentation source lineage tracking
- Error tracking and exception recording
- Performance metrics and attributes

#### Phase 5: MCP Server Implementation
- MCP server using @modelcontextprotocol/sdk
- Stdio transport for client communication
- Dynamic tool registration from URLs
- List tools handler
- Call tool handler with error handling
- Environment variable configuration
- Graceful shutdown handling

#### Phase 6: Testing & Documentation
- Unit tests for utility functions
- Parser tests (OpenAPI, HTML, Markdown)
- Schema generator tests
- Integration tests for full pipeline
- Comprehensive README with examples
- Deployment guide (Docker, Kubernetes, systemd, PM2)
- Example configurations and usage guide
- Contributing guidelines
- MIT License
- CI/CD workflows (GitHub Actions)

### Features

- Multi-format support: OpenAPI/Swagger, HTML, Markdown
- Automatic tool generation from API documentation
- Full OpenTelemetry observability with Arize Phoenix
- Runtime validation with Zod schemas
- Production-ready error handling
- Type-safe TypeScript implementation
- Stdio-based MCP server
- Environment-based configuration
- Comprehensive test coverage
- Deployment-ready configurations

### Documentation

- README.md with usage examples
- EXAMPLE.md with Petstore API walkthrough
- DEPLOYMENT.md with multiple deployment options
- CONTRIBUTING.md with development guidelines
- mcp-config.example.json for client configuration
- .env.example for environment setup

### Testing

- 20+ test cases covering all major components
- Unit tests for parsers and generators
- Integration tests for end-to-end flow
- Vitest configuration with coverage support

[1.0.0]: https://github.com/RETR0-OS/Doc2Mcp/releases/tag/v1.0.0
