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
  FileText,
  AlertCircle,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Inbox,
  Info,
  AlertTriangle as WarningIcon,
  Flame,
  Zap,
  Search,
} from "lucide-react";

interface AuditLog {
  id: number;
  action: string;
  executor: string | null;
  target: string | null;
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
  timestamp: string | null;
}

const SEVERITY_BADGES: Record<number, { label: string; color: string; icon: React.ElementType }> = {
  1: { label: "Info", color: "bg-blue-500/15 text-blue-600 border-blue-500/30", icon: Info },
  2: { label: "Warning", color: "bg-amber-500/15 text-amber-600 border-amber-500/30", icon: WarningIcon },
  3: { label: "High", color: "bg-orange-500/15 text-orange-600 border-orange-500/30", icon: Flame },
  4: { label: "Critical", color: "bg-red-500/15 text-red-600 border-red-500/30", icon: Zap },
};

function formatTimestamp(ts: string | null): string {
  if (!ts) return "—";
  try {
    const date = new Date(ts);
    return date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return ts;
  }
}

function formatSnowflake(id: string | null): string {
  if (!id || id === "null") return "—";
  return id.length > 8 ? `…${id.slice(-6)}` : id;
}

function getActionLabel(action: string): string {
  return action
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function LogsPage({ params }: { params: Promise<{ guildId: string }> }) {
  const { guildId } = use(params);

  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [days, setDays] = useState("7");
  const [actionFilter, setActionFilter] = useState("all");

  const fetchLogs = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const queryParams: Record<string, string | number> = {
        days: parseInt(days),
        page,
      };
      if (actionFilter !== "all") {
        queryParams.action_type = actionFilter;
      }
      const res = await api.get(`/logs/${guildId}`, { params: queryParams });
      setLogs(res.data.logs || []);
    } catch (err) {
      console.error(err);
      setError("Failed to load audit logs.");
    } finally {
      setLoading(false);
    }
  }, [guildId, days, page, actionFilter]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <FileText className="h-8 w-8 text-primary" />
            Audit Logs
          </h1>
          <p className="text-muted-foreground mt-1">
            Full event trail for your server — every action, tracked.
          </p>
        </div>
        <Button onClick={fetchLogs} variant="outline" size="icon" disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <Search className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Filters:</span>
            </div>
            <Select value={actionFilter} onValueChange={(v) => { setActionFilter(v ?? "all"); setPage(1); }}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Action type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Actions</SelectItem>
                <SelectItem value="message_delete">Message Delete</SelectItem>
                <SelectItem value="message_edit">Message Edit</SelectItem>
                <SelectItem value="member_join">Member Join</SelectItem>
                <SelectItem value="member_leave">Member Leave</SelectItem>
                <SelectItem value="member_ban">Member Ban</SelectItem>
                <SelectItem value="member_unban">Member Unban</SelectItem>
                <SelectItem value="role_create">Role Create</SelectItem>
                <SelectItem value="role_delete">Role Delete</SelectItem>
                <SelectItem value="channel_create">Channel Create</SelectItem>
                <SelectItem value="channel_delete">Channel Delete</SelectItem>
                <SelectItem value="verification_pass">Verification Pass</SelectItem>
                <SelectItem value="verification_fail">Verification Fail</SelectItem>
              </SelectContent>
            </Select>
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
          </div>
        </CardContent>
      </Card>

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
          <CardTitle>Event Log</CardTitle>
          <CardDescription>
            Showing events from the last {days === "1" ? "24 hours" : `${days} days`}
            {actionFilter !== "all" ? ` · Filtered by: ${getActionLabel(actionFilter)}` : ""}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="flex items-center gap-4">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-48 flex-1" />
                  <Skeleton className="h-4 w-36" />
                </div>
              ))}
            </div>
          ) : logs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <Inbox className="h-12 w-12 mb-3 opacity-50" />
              <p className="text-lg font-medium">No events found</p>
              <p className="text-sm">No audit log events match your current filters.</p>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Action</TableHead>
                    <TableHead>Executor</TableHead>
                    <TableHead>Target</TableHead>
                    <TableHead>Before / After</TableHead>
                    <TableHead className="text-right">Timestamp</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {logs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell>
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border bg-primary/10 text-primary border-primary/20">
                          {getActionLabel(log.action)}
                        </span>
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {formatSnowflake(log.executor)}
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {formatSnowflake(log.target)}
                      </TableCell>
                      <TableCell className="max-w-[280px] text-sm text-muted-foreground">
                        {log.before || log.after ? (
                          <div className="space-y-0.5">
                            {log.before && (
                              <div className="truncate">
                                <span className="text-red-500 font-mono text-xs">−</span>{" "}
                                {JSON.stringify(log.before).slice(0, 60)}
                              </div>
                            )}
                            {log.after && (
                              <div className="truncate">
                                <span className="text-green-500 font-mono text-xs">+</span>{" "}
                                {JSON.stringify(log.after).slice(0, 60)}
                              </div>
                            )}
                          </div>
                        ) : (
                          "—"
                        )}
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
                  Page {page} · {logs.length} event{logs.length !== 1 ? "s" : ""}
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
