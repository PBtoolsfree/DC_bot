"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api/client";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export default function GuildSelector() {
  const [guilds, setGuilds] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/guilds")
      .then((res) => {
        setGuilds(res.data);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-muted-foreground">Loading servers...</div>;
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-5xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Select a Server</h1>
          <p className="text-muted-foreground">Select a server to manage its settings.</p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {guilds.map((guild) => (
            <Link key={guild.id} href={`/dashboard/${guild.id}`}>
              <Card className="hover:border-primary transition-colors cursor-pointer group">
                <CardHeader className="flex flex-row items-center gap-4">
                  <Avatar className="h-12 w-12 border">
                    <AvatarImage src={guild.icon ? `https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.png` : ""} />
                    <AvatarFallback>{guild.name.charAt(0)}</AvatarFallback>
                  </Avatar>
                  <div>
                    <CardTitle className="text-base group-hover:text-primary transition-colors">{guild.name}</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      {guild.owner ? "Owner" : "Admin"}
                    </p>
                  </div>
                </CardHeader>
              </Card>
            </Link>
          ))}
          {guilds.length === 0 && (
            <div className="col-span-full text-center p-12 border rounded-lg bg-muted/20">
              <p className="text-muted-foreground">No servers found where you have Administrator permissions.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
