"use client";

import { use, useEffect, useState, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";
import {
  Settings as SettingsIcon,
  AlertCircle,
  CheckCircle2,
  Shield,
  Gavel,
  Bot,
  MessageCircle,
  Sparkles,
  Ticket,
  RefreshCw,
  Save,
} from "lucide-react";

interface ModuleConfig {
  name: string;
  label: string;
  description: string;
  icon: React.ElementType;
  enabled: boolean;
  config: Record<string, unknown>;
  loading: boolean;
  dirty: boolean;
}

const MODULE_DEFINITIONS = [
  {
    name: "moderation",
    label: "Moderation",
    description: "Warn, kick, ban, mute, timeout and purge commands.",
    icon: Gavel,
  },
  {
    name: "automod",
    label: "Auto Moderation",
    description: "Automatic detection and removal of spam, links, and bad words.",
    icon: Bot,
  },
  {
    name: "security",
    label: "Security & Verification",
    description: "Anti-raid engine, captcha verification, and risk scoring.",
    icon: Shield,
  },
  {
    name: "welcome",
    label: "Welcome System",
    description: "Welcome messages, auto-roles, and DM greetings for new members.",
    icon: MessageCircle,
  },
  {
    name: "xp",
    label: "XP & Levels",
    description: "Experience points, leveling, role rewards, and leaderboards.",
    icon: Sparkles,
  },
  {
    name: "tickets",
    label: "Tickets",
    description: "Support ticket system with transcripts and categories.",
    icon: Ticket,
  },
];

export default function SettingsPage({ params }: { params: Promise<{ guildId: string }> }) {
  const { guildId } = use(params);

  const [modules, setModules] = useState<ModuleConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingModule, setSavingModule] = useState<string | null>(null);
  const [successModule, setSuccessModule] = useState<string | null>(null);

  const fetchAllModules = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const results = await Promise.allSettled(
        MODULE_DEFINITIONS.map(async (mod) => {
          try {
            const res = await api.get(`/settings/${guildId}/${mod.name}`);
            return {
              ...mod,
              enabled: res.data.enabled ?? false,
              config: res.data.config ?? {},
              loading: false,
              dirty: false,
            };
          } catch {
            // Module not configured yet — show as disabled
            return {
              ...mod,
              enabled: false,
              config: {},
              loading: false,
              dirty: false,
            };
          }
        })
      );

      const moduleConfigs = results.map((result, i) => {
        if (result.status === "fulfilled") return result.value;
        return {
          ...MODULE_DEFINITIONS[i],
          enabled: false,
          config: {},
          loading: false,
          dirty: false,
        };
      });

      setModules(moduleConfigs);
    } catch (err) {
      console.error(err);
      setError("Failed to load module settings.");
    } finally {
      setLoading(false);
    }
  }, [guildId]);

  useEffect(() => {
    fetchAllModules();
  }, [fetchAllModules]);

  const toggleModule = (moduleName: string, enabled: boolean) => {
    setModules((prev) =>
      prev.map((m) =>
        m.name === moduleName ? { ...m, enabled, dirty: true } : m
      )
    );
  };

  const saveModule = async (moduleName: string) => {
    const mod = modules.find((m) => m.name === moduleName);
    if (!mod) return;

    try {
      setSavingModule(moduleName);
      setError(null);

      await api.put(`/settings/${guildId}/${moduleName}`, {
        enabled: mod.enabled,
        config: mod.config,
      });

      setModules((prev) =>
        prev.map((m) =>
          m.name === moduleName ? { ...m, dirty: false } : m
        )
      );

      setSuccessModule(moduleName);
      setTimeout(() => setSuccessModule(null), 2000);
    } catch (err) {
      console.error(err);
      setError(`Failed to save ${mod.label} settings.`);
    } finally {
      setSavingModule(null);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <SettingsIcon className="h-8 w-8 text-primary" />
            Settings
          </h1>
          <p className="text-muted-foreground mt-1">
            Enable or disable bot modules for your server.
          </p>
        </div>
        <Button onClick={fetchAllModules} variant="outline" size="icon" disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </Button>
      </div>

      {error && (
        <div className="bg-destructive/15 text-destructive p-3 rounded-md flex items-center gap-2">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-40 rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {modules.map((mod) => {
            const Icon = mod.icon;
            const isSaving = savingModule === mod.name;
            const isSuccess = successModule === mod.name;

            return (
              <Card
                key={mod.name}
                className={`transition-all duration-200 ${
                  mod.enabled
                    ? "border-primary/30 shadow-sm"
                    : "opacity-75"
                }`}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div
                        className={`p-2 rounded-lg ${
                          mod.enabled
                            ? "bg-primary/10 text-primary"
                            : "bg-muted text-muted-foreground"
                        }`}
                      >
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <CardTitle className="text-base">{mod.label}</CardTitle>
                      </div>
                    </div>
                    <Switch
                      checked={mod.enabled}
                      onCheckedChange={(c) => toggleModule(mod.name, c)}
                    />
                  </div>
                </CardHeader>
                <CardContent>
                  <CardDescription className="mb-4">
                    {mod.description}
                  </CardDescription>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {mod.enabled ? (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-600 bg-emerald-500/15 px-2 py-0.5 rounded-full">
                          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                          <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/50" />
                          Disabled
                        </span>
                      )}
                    </div>

                    {mod.dirty && (
                      <Button
                        size="sm"
                        disabled={isSaving}
                        onClick={() => saveModule(mod.name)}
                        className="gap-1.5"
                      >
                        {isSaving ? (
                          <RefreshCw className="h-3 w-3 animate-spin" />
                        ) : isSuccess ? (
                          <CheckCircle2 className="h-3 w-3" />
                        ) : (
                          <Save className="h-3 w-3" />
                        )}
                        {isSaving ? "Saving..." : isSuccess ? "Saved!" : "Save"}
                      </Button>
                    )}

                    {isSuccess && !mod.dirty && (
                      <span className="text-xs text-emerald-600 flex items-center gap-1">
                        <CheckCircle2 className="h-3 w-3" />
                        Saved
                      </span>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
