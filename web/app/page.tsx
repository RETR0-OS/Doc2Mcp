import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { AuthNav, HeroAuthButtons, CTAAuthButtons } from '@/components/AuthNav'
import { Zap, Database, Eye, Terminal } from 'lucide-react'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 w-full border-b border-border bg-background/80 backdrop-blur-sm z-50">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="h-6 w-6 text-primary" />
            <span className="font-bold text-xl">Doc2MCP</span>
          </div>
          
          <nav className="flex items-center gap-4">
            <AuthNav />
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4">
        <div className="container mx-auto max-w-5xl text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-primary/20 bg-primary/10 text-primary text-sm mb-6 animate-fade-in">
            <Zap className="h-4 w-4" />
            <span>Powered by Google Gemini</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold mb-6 animate-slide-up">
            Intelligent
            <span className="text-primary"> Documentation Search</span>
            <br />
            for AI Agents
          </h1>
          
          <p className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto animate-slide-up" style={{ animationDelay: '0.1s' }}>
            Transform any documentation into searchable knowledge. Let AI agents explore, understand, and answer questions from your docs automatically.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center animate-slide-up" style={{ animationDelay: '0.2s' }}>
            <HeroAuthButtons />
            <Button size="lg" variant="outline" asChild>
              <a href="https://github.com/RETR0-OS/Doc2Mcp" target="_blank" rel="noopener noreferrer">
                View on GitHub
              </a>
            </Button>
          </div>

          {/* Demo Video/Screenshot Placeholder */}
          <div className="mt-16 rounded-lg border border-border bg-card p-1 animate-slide-up" style={{ animationDelay: '0.3s' }}>
            <div className="aspect-video rounded-md bg-muted flex items-center justify-center">
              <p className="text-muted-foreground">Demo Video Coming Soon</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4 bg-card/30">
        <div className="container mx-auto max-w-6xl">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-12">
            Why Doc2MCP?
          </h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard
              icon={<Zap className="h-8 w-8 text-primary" />}
              title="Intelligent Exploration"
              description="AI agent iteratively explores docs, deciding what to read next based on your query. No manual indexing needed."
            />
            <FeatureCard
              icon={<Database className="h-8 w-8 text-primary" />}
              title="Smart Caching"
              description="Caches explored pages with summaries for instant retrieval. Saves API costs and speeds up repeated queries."
            />
            <FeatureCard
              icon={<Eye className="h-8 w-8 text-primary" />}
              title="Full Observability"
              description="Watch your agent think in real-time. Track exploration paths, costs, and decisions with Phoenix tracing."
            />
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-4">
        <div className="container mx-auto max-w-4xl">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-12">
            Simple Setup
          </h2>
          
          <div className="space-y-6">
            <Step
              number="1"
              title="Add Documentation Sources"
              description="Point to any documentation URL or local files you want to make searchable."
            />
            <Step
              number="2"
              title="Generate MCP Config"
              description="Get a ready-to-use MCP config for VS Code, Claude Desktop, or any MCP client."
            />
            <Step
              number="3"
              title="Ask Questions"
              description="Your AI assistant can now search docs intelligently and answer questions with citations."
            />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 bg-primary/5 border-y border-primary/20">
        <div className="container mx-auto max-w-3xl text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            Ready to make your docs AI-searchable?
          </h2>
          <p className="text-lg text-muted-foreground mb-8">
            Join developers building smarter documentation experiences
          </p>
          <CTAAuthButtons />
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-border">
        <div className="container mx-auto max-w-6xl">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <Terminal className="h-5 w-5 text-primary" />
              <span className="font-bold">Doc2MCP</span>
            </div>
            <p className="text-sm text-muted-foreground">
              © 2026 Doc2MCP. Open source under MIT License.
            </p>
            <div className="flex gap-4">
              <a href="https://github.com/RETR0-OS/Doc2Mcp" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                GitHub
              </a>
              <a href="/docs" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                Docs
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="p-6 rounded-lg border border-border bg-card hover:border-primary/50 transition-colors">
      <div className="mb-4">{icon}</div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-muted-foreground">{description}</p>
    </div>
  )
}

function Step({ number, title, description }: { number: string; title: string; description: string }) {
  return (
    <div className="flex gap-6 items-start">
      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary flex items-center justify-center font-bold">
        {number}
      </div>
      <div className="flex-1 pt-1">
        <h3 className="text-xl font-semibold mb-2">{title}</h3>
        <p className="text-muted-foreground">{description}</p>
      </div>
    </div>
  )
}
