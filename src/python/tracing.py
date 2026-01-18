"""OpenTelemetry tracing setup for Doc2MCP"""
import sys
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource


class TracingManager:
    """Manages OpenTelemetry tracing configuration"""
    
    def __init__(self, phoenix_endpoint: str, enable_console: bool = True):
        self.phoenix_endpoint = phoenix_endpoint
        self.enable_console = enable_console
        self.provider = None
        self.tracer = None
        
    def setup(self):
        """Initialize OpenTelemetry tracing"""
        print("[TRACING] 🔧 Setting up OpenTelemetry...", file=sys.stderr)
        
        resource = Resource(attributes={
            "service.name": "doc2mcp",
            "service.version": "1.0.0"
        })
        
        self.provider = TracerProvider(resource=resource)
        
        # Phoenix OTLP exporter
        print(f"[TRACING] 🔗 Phoenix endpoint: {self.phoenix_endpoint}", file=sys.stderr)
        otlp_exporter = OTLPSpanExporter(endpoint=self.phoenix_endpoint)
        self.provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        
        # Console exporter for debugging
        if self.enable_console:
            console_exporter = ConsoleSpanExporter()
            self.provider.add_span_processor(BatchSpanProcessor(console_exporter))
        
        trace.set_tracer_provider(self.provider)
        self.tracer = trace.get_tracer(__name__)
        
        print("[TRACING] ✅ Tracing initialized", file=sys.stderr)
        return self.tracer
    
    def get_tracer(self):
        """Get the tracer instance"""
        if not self.tracer:
            return self.setup()
        return self.tracer
