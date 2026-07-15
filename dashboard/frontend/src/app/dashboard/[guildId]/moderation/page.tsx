"use client";

import { use, useEffect, useState, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";
import {
  AlertTriangle,
  AlertCircle,
  ShieldBan,
  Gavel,
  Timer,
  MessageSquareOff,
  UserX,
  Ban,
  Volume2,
  Lock,
  Unlock,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Inbox,
} from "lucide-react";

interface ModLog {
  id: number;
  action: string;
  executor: string | null;
  target: string | null;
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
  timestamp: string | null;
}

const ACTION_BADGES: Record<string, { label: string; color: string; icon: React.ElementType }> = {
  warn: { label: "Warn", color: "bg-amber-500/15 text-amber-600 border-amber-500/30", icon: AlertTriangle },
  auto_warn: { label: "Auto Warn", color: "bg-amber-500/15 text-amber-600 border-amber-500/30", icon: AlertTriangle },
  kick: { label: "Kick", color: "bg-orange-500/15 text-orange-600 border-orange-500/30", icon: UserX },
  auto_kick: { label: "Auto Kick", color: "bg-orange-500/15 text-orange-600 border-orange-500/30", icon: UserX },
  ban: { label: "Ban", color: "bg-red-500/15 text-red-600 border-red-500/30", icon: Ban },
  auto_ban: { label: "Auto Ban", color: "bg-red-500/15 text-red-600 border-red-500/30", icon: Ban },
  unban: { label: "Unban", color: "bg-emerald-500/15 text-emerald-600 border-emerald-500/30", icon: ShieldBan },
  mute: { label: "Mute", color: "bg-blue-500/15 text-blue-600 border-blue-500/30", icon: Volume2 },
  unmute: { label: "Unmute", color: "bg-emerald-500/15 text-emerald-600 border-emerald-500/30", icon: Volume2 },
  timeout: { label: "Timeout", color: "bg-violet-500/15 text-violet-600 border-violet-500/30", icon: Timer },
  auto_timeout: { label: "Auto Timeout", color: "bg-violet-500/15 text-violet-600 border-violet-500/30", icon: Timer },
  untimeout: { label: "Untimeout", color: "bg-emerald-500/15 text-emerald-600 border-emerald-500/30", icon: Timer },
  softban: { label: "Softban", color: "bg-rose-500/15 text-rose-600 border-rose-500/30", icon: Ban },
  purge: { label: "Purge", color: "bg-pink-500/15 text-pink-600 border-pink-500/30", icon: MessageSquareOff },
  auto_delete: { label: "Auto Delete", color: "bg-pink-500/15 text-pink-600 border-pink-500/30", icon: MessageSquareOff },
  lockdown: { label: "Lockdown", color: "bg-red-500/15 text-red-600 border-red-500/30", icon: Lock },
  unlock: { label: "Unlock", color: "bg-emerald-500/15 text-emerald-600 border-emerald-500/30", icon: Unlock },
  slowmode: { label: "Slowmode", color: "bg-sky-500/15 text-sky-600 border-sky-500/30", icon: Timer },
  note: { label: "Note", color: "bg-slate-500/15 text-slate-600 border-slate-500/30", icon: Gavel },
  anti_nuke: { label: "Anti-Nuke", color: "bg-red-500/15 text-red-600 border-red-500/30", icon: ShieldBan },
  anti_raid: { label: "Anti-Raid", color: "bg-red-500/15 text-red-600 border-red-500/30", icon: ShieldBan },
};

function ActionBadge({ action }: { action: string }) {
  const badge = ACTION_BADGES[action] || {
    label: action,
    color: "bg-muted text-muted-foreground border-border",
    icon: Gavel,
  };
  const Icon = badge.icon;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${badge.color}`}>
      <Icon className="h-3 w-3" />
      {badge.label}
    </span>
  );
}

function formatTimestamp(ts: string | null): string {
  if (!ts) return "—";
  try {
    const date = new Date(ts);
    return date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return ts;
  }
}

function formatSnowflake(id: string | null): string {
  if (!id || id === "null") return "—";
  // Show truncated ID for readability
  return id.length > 8 ? `…${id.slice(-6)}` : id;
}

export default function ModerationPage({ params }: { params: Promise<{ guildId: string }> }) {
  const { guildId } = use(params);

  const [logs, setLogs] = useState<ModLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [days, setDays] = useState("7");

  const fetchLogs = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/logs/${guildId}`, {
        params: { days: parseInt(days), page },
      });
      setLogs(res.data.logs || []);
    } catch (err) {
      console.error(err);
      setError("Failed to load moderation logs.");
    } finally {
      setLoading(false);
    }
  }, [guildId, days, page]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Gavel className="h-8 w-8 text-primary" />
            Moderation
          </h1>
          <p className="text-muted-foreground mt-1">
            View all moderation actions taken in your server.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={days} onValueChange={(v) => { setDays(v ?? "7"); setPage(1); }}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Time range" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">Last 24 hours</SelectItem>
              <SelectItem value="7">Last 7 days</SelectItem>
              <SelectItem value="14">Last 14 days</SelectItem>
              <SelectItem value="30">Last 30 days</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={fetchLogs} variant="outline" size="icon" disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {error && (
        <div className="bg-destructive/15 text-destructive p-3 rounded-md flex items-center gap-2">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {error}
          <Button onClick={fetchLogs} variant="outline" size="sm" className="ml-auto">
            Try Again
          </Button>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Recent Actions</CardTitle>
          <CardDescription>
            Moderation actions from the last {days === "1" ? "24 hours" : `${days} days`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center gap-4">
                  <Skeleton className="h-6 w-24 rounded-full" />
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-48 flex-1" />
                  <Skeleton className="h-4 w-28" />
                </div>
              ))}
            </div>
          ) : logs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <Inbox className="h-12 w-12 mb-3 opacity-50" />
              <p className="text-lg font-medium">No actions found</p>
              <p className="text-sm">No moderation actions in this time range.</p>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Action</TableHead>
                    <TableHead>Target</TableHead>
                    <TableHead>Moderator</TableHead>
                    <TableHead>Details</TableHead>
                    <TableHead className="text-right">Time</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {logs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell>
                        <ActionBadge action={log.action} />
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {formatSnowflake(log.target)}
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {formatSnowflake(log.executor)}
                      </TableCell>
                      <TableCell className="max-w-[300px] truncate text-muted-foreground text-sm">
                        {log.after
                          ? JSON.stringify(log.after).slice(0, 80)
                          : "—"}
                      </TableCell>
                      <TableCell className="text-right text-muted-foreground text-sm">
                        {formatTimestamp(log.timestamp)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <p className="text-sm text-muted-foreground">
                  Page {page}
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                  >
                    <ChevronLeft className="h-4 w-4 mr-1" />
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={logs.length < 50}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    Next
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
