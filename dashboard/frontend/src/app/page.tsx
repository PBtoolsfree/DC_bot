import { Shield, Zap, Lock, Settings2 } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <header className="h-16 border-b flex items-center justify-between px-6 lg:px-12">
        <div className="font-bold text-xl flex items-center space-x-2">
          <Shield className="w-6 h-6 text-primary" />
          <span>Management Bot</span>
        </div>
        <nav>
          <a
            href="http://localhost:8000/api/v1/auth/login" // Adjust to backend URL
            className="inline-flex h-9 items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90"
          >
            Login with Discord
          </a>
        </nav>
      </header>

      <main className="px-6 lg:px-12 py-24 space-y-24">
        <section className="text-center space-y-6 max-w-3xl mx-auto">
          <h1 className="text-5xl font-extrabold tracking-tight sm:text-6xl text-foreground">
            Enterprise Discord Management
          </h1>
          <p className="text-xl text-muted-foreground">
            A production-ready SaaS platform to moderate, secure, and manage your Discord communities at scale.
          </p>
          <div className="flex justify-center">
            <a
              href="http://localhost:8000/api/v1/auth/login"
              className="inline-flex h-11 items-center justify-center rounded-md bg-primary px-8 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90"
            >
              Get Started
            </a>
          </div>
        </section>

        <section className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8 max-w-6xl mx-auto">
          {[
            { icon: Shield, title: "Anti-Nuke", desc: "Automated rollback engine for deleted channels and mass-bans." },
            { icon: Zap, title: "AutoMod", desc: "Lightning-fast spam protection and custom regex filtering." },
            { icon: Settings2, title: "Dashboard", desc: "Granular RBAC settings to configure every module instantly." },
            { icon: Lock, title: "Audit Logs", desc: "Exportable, searchable enterprise logging with data retention." }
          ].map((feature, i) => (
            <div key={i} className="space-y-3 p-6 border rounded-xl bg-card">
              <feature.icon className="w-8 h-8 text-primary" />
              <h3 className="font-bold text-lg">{feature.title}</h3>
              <p className="text-sm text-muted-foreground">{feature.desc}</p>
            </div>
          ))}
        </section>
      </main>
    </div>
  );
}
