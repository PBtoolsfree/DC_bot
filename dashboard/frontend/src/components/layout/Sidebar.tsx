import Link from "next/link";
import { LayoutDashboard, Shield, AlertTriangle, FileText, Settings } from "lucide-react";

export function Sidebar({ guildId }: { guildId: string }) {
  const routes = [
    { href: `/dashboard/${guildId}`, label: "Overview", icon: LayoutDashboard },
    { href: `/dashboard/${guildId}/moderation`, label: "Moderation", icon: AlertTriangle },
    { href: `/dashboard/${guildId}/security`, label: "Security", icon: Shield },
    { href: `/dashboard/${guildId}/logs`, label: "Audit Logs", icon: FileText },
    { href: `/dashboard/${guildId}/settings`, label: "Settings", icon: Settings },
  ];

  return (
    <aside className="w-64 h-full border-r bg-background flex flex-col">
      <div className="h-14 border-b flex items-center px-4 font-bold text-lg">
        SaaS Dashboard
      </div>
      <nav className="flex-1 overflow-y-auto p-4 space-y-2">
        {routes.map((route) => (
          <Link
            key={route.href}
            href={route.href}
            className="flex items-center space-x-3 px-3 py-2 rounded-md hover:bg-accent hover:text-accent-foreground text-sm font-medium transition-colors"
          >
            <route.icon className="w-5 h-5" />
            <span>{route.label}</span>
          </Link>
        ))}
      </nav>
    </aside>
  );
}
