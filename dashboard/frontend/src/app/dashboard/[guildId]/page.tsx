"use client";

import { use } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useWebSocket } from "@/hooks/useWebSocket";
import { Activity, Users, ShieldAlert, MessagesSquare } from "lucide-react";

export default function GuildDashboard({ params }: { params: Promise<{ guildId: string }> }) {
  const { guildId } = use(params);
  // Real-time events from our FastAPI WebSocket
  const { messages } = useWebSocket(guildId);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">Overview</h1>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Members</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Live Data</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Security Incidents</CardTitle>
            <ShieldAlert className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0 Active</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Recent Activity Stream</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 max-h-[400px] overflow-y-auto">
              {messages.length === 0 ? (
                <div className="text-sm text-muted-foreground">Waiting for events...</div>
              ) : (
                messages.map((msg, i) => (
                  <div key={i} className="flex items-center text-sm border-b pb-2">
                    <Activity className="mr-2 h-4 w-4 text-blue-500" />
                    <span className="font-medium mr-2">{msg.action}</span>
                    <span className="text-muted-foreground">Target: {msg.target}</span>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
