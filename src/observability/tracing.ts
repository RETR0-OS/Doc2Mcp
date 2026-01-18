/**
 * OpenTelemetry tracing setup for Arize Phoenix observability
 */

import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { Resource } from '@opentelemetry/resources';
import { SEMRESATTRS_SERVICE_NAME, SEMRESATTRS_SERVICE_VERSION } from '@opentelemetry/semantic-conventions';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { trace, SpanStatusCode, Span } from '@opentelemetry/api';

export interface TracingConfig {
  serviceName: string;
  serviceVersion: string;
  arizeEndpoint?: string;
  arizeApiKey?: string;
  enabled: boolean;
}

export class TracingManager {
  private provider: NodeTracerProvider | null = null;
  private config: TracingConfig;

  constructor(config: TracingConfig) {
    this.config = config;
  }

  /**
   * Initializes OpenTelemetry tracing
   */
  initialize() {
    if (!this.config.enabled) {
      console.log('Tracing is disabled');
      return;
    }

    const resource = Resource.default().merge(
      new Resource({
        [SEMRESATTRS_SERVICE_NAME]: this.config.serviceName,
        [SEMRESATTRS_SERVICE_VERSION]: this.config.serviceVersion,
      })
    );

    this.provider = new NodeTracerProvider({
      resource,
    });

    // Configure OTLP exporter for Arize Phoenix
    const endpoint = this.config.arizeEndpoint || 'http://localhost:6006/v1/traces';
    const headers: Record<string, string> = {};

    if (this.config.arizeApiKey) {
      headers['Authorization'] = `Bearer ${this.config.arizeApiKey}`;
    }

    const exporter = new OTLPTraceExporter({
      url: endpoint,
      headers,
    });

    this.provider.addSpanProcessor(new BatchSpanProcessor(exporter));
    this.provider.register();

    console.log(`Tracing initialized with endpoint: ${endpoint}`);
  }

  /**
   * Shuts down the tracer provider
   */
  async shutdown() {
    if (this.provider) {
      await this.provider.shutdown();
      console.log('Tracing shut down');
    }
  }

  /**
   * Gets the tracer for creating spans
   */
  getTracer() {
    return trace.getTracer(this.config.serviceName, this.config.serviceVersion);
  }
}

/**
 * Creates a span for a tool execution
 */
export async function traceToolExecution<T>(
  tracer: ReturnType<TracingManager['getTracer']>,
  toolName: string,
  sourceUrl: string,
  sourceType: string,
  endpoint: { path: string; method: string },
  args: Record<string, any>,
  fn: () => Promise<T>
): Promise<T> {
  return tracer.startActiveSpan(
    `tool.${toolName}`,
    {
      attributes: {
        'tool.name': toolName,
        'tool.source_url': sourceUrl,
        'tool.source_type': sourceType,
        'tool.endpoint.path': endpoint.path,
        'tool.endpoint.method': endpoint.method,
        'tool.args': JSON.stringify(args),
      },
    },
    async (span: Span) => {
      try {
        const result = await fn();

        // Add result metadata to span
        if (result && typeof result === 'object') {
          if ('status' in result && typeof (result as any).status === 'number') {
            span.setAttribute('http.status_code', (result as any).status);
          }
          span.setAttribute('tool.success', true);
        }

        span.setStatus({ code: SpanStatusCode.OK });
        return result;
      } catch (error) {
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: error instanceof Error ? error.message : 'Unknown error',
        });
        span.recordException(error instanceof Error ? error : new Error(String(error)));
        span.setAttribute('tool.success', false);
        throw error;
      } finally {
        span.end();
      }
    }
  );
}

/**
 * Creates a span for documentation parsing
 */
export async function traceDocumentationParsing<T>(
  tracer: ReturnType<TracingManager['getTracer']>,
  sourceUrl: string,
  sourceType: string,
  fn: () => Promise<T>
): Promise<T> {
  return tracer.startActiveSpan(
    'parse.documentation',
    {
      attributes: {
        'parse.source_url': sourceUrl,
        'parse.source_type': sourceType,
      },
    },
    async (span: Span) => {
      try {
        const result = await fn();
        span.setStatus({ code: SpanStatusCode.OK });

        // Add result metadata
        if (result && typeof result === 'object' && 'endpoints' in result) {
          span.setAttribute('parse.endpoints_count', (result as any).endpoints.length);
        }

        return result;
      } catch (error) {
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: error instanceof Error ? error.message : 'Unknown error',
        });
        span.recordException(error instanceof Error ? error : new Error(String(error)));
        throw error;
      } finally {
        span.end();
      }
    }
  );
}
