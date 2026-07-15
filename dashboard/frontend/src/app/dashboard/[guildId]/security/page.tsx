"use client";

import { use, useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";
import { Shield, Save, AlertCircle, CheckCircle2 } from "lucide-react";

interface VerificationSettings {
  guild_id: string;
  enabled: boolean;
  verification_type: "button" | "math" | "word" | "image";
  quarantine_role_id?: string;
  verified_role_id?: string;
  temporary_role_id?: string;
  verification_channel_id?: string;
  log_channel_id?: string;
  timeout_minutes: number;
  max_attempts: number;
  risk_threshold_high: number;
  language: string;
  delete_failed_messages: boolean;
  kick_on_timeout: boolean;
}

const DEFAULT_SETTINGS: VerificationSettings = {
  guild_id: "",
  enabled: false,
  verification_type: "button",
  quarantine_role_id: "",
  verified_role_id: "",
  temporary_role_id: "",
  verification_channel_id: "",
  log_channel_id: "",
  timeout_minutes: 10,
  max_attempts: 3,
  risk_threshold_high: 70,
  language: "en-US",
  delete_failed_messages: true,
  kick_on_timeout: false,
};

export default function SecurityPage({ params }: { params: Promise<{ guildId: string }> }) {
  const { guildId } = use(params);
  
  const [settings, setSettings] = useState<VerificationSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [isNewConfig, setIsNewConfig] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, [guildId]);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/verification/${guildId}`);
      setSettings(res.data);
      setIsNewConfig(false);
    } catch (err: unknown) {
      console.error(err);
      // Graceful fallback: if API fails (404, 500, etc.), show the form with defaults
      // so the user can still configure and save new settings
      setSettings({ ...DEFAULT_SETTINGS, guild_id: guildId });
      setIsNewConfig(true);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!settings) return;
    
    try {
      setSaving(true);
      setSuccess(false);
      setError(null);
      
      const res = await api.put(`/verification/${guildId}`, settings);
      setSettings(res.data);
      setIsNewConfig(false);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error(err);
      setError("Failed to save settings. Please verify all Discord IDs are correct.");
    } finally {
      setSaving(false);
    }
  };

  const updateSetting = (key: keyof VerificationSettings, value: unknown) => {
    setSettings((prev) => (prev ? { ...prev, [key]: value } : null));
  };

  if (loading) {
    return (
      <div className="space-y-6 max-w-5xl mx-auto">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton className="h-9 w-64" />
            <Skeleton className="h-4 w-96" />
          </div>
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="grid gap-6 md:grid-cols-2">
          <Skeleton className="h-64 rounded-xl" />
          <Skeleton className="h-64 rounded-xl" />
          <Skeleton className="h-48 rounded-xl md:col-span-2" />
        </div>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="flex h-[400px] flex-col items-center justify-center space-y-4">
        <AlertCircle className="h-12 w-12 text-destructive" />
        <h2 className="text-xl font-semibold">Failed to load data</h2>
        <Button onClick={fetchSettings} variant="outline">Try Again</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Shield className="h-8 w-8 text-primary" />
            Security & Verification
          </h1>
          <p className="text-muted-foreground mt-2">
            Configure the anti-raid risk engine and captcha system for your server.
          </p>
        </div>
        <Button onClick={handleSave} disabled={saving} className="gap-2">
          <Save className="h-4 w-4" />
          {saving ? "Saving..." : "Save Changes"}
        </Button>
      </div>

      {isNewConfig && (
        <div className="bg-blue-500/15 text-blue-600 p-3 rounded-md flex items-center gap-2">
          <Shield className="h-4 w-4 flex-shrink-0" />
          No existing configuration found. Configure your settings below and save to create them.
        </div>
      )}

      {error && (
        <div className="bg-destructive/15 text-destructive p-3 rounded-md flex items-center gap-2">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-500/15 text-green-500 p-3 rounded-md flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
          Settings saved successfully!
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        {/* Main Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Core Settings</CardTitle>
            <CardDescription>Enable the system and choose the challenge type.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <label className="text-sm font-medium">Enable Verification</label>
                <p className="text-xs text-muted-foreground">Turn the entire verification system on or off.</p>
              </div>
              <Switch 
                checked={settings.enabled}
                onCheckedChange={(c) => updateSetting("enabled", c)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Verification Type</label>
              <Select 
                value={settings.verification_type} 
                onValueChange={(v) => updateSetting("verification_type", v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="button">Button (Low Security)</SelectItem>
                  <SelectItem value="math">Math Equation (Medium Security)</SelectItem>
                  <SelectItem value="word">Word Challenge (Medium Security)</SelectItem>
                  <SelectItem value="image">Image Captcha (High Security)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Language</label>
              <Select 
                value={settings.language} 
                onValueChange={(v) => updateSetting("language", v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select language" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en-US">English (US)</SelectItem>
                  <SelectItem value="fr">French</SelectItem>
                  <SelectItem value="de">German</SelectItem>
                  <SelectItem value="es">Spanish</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Discord Setup */}
        <Card>
          <CardHeader>
            <CardTitle>Discord Setup</CardTitle>
            <CardDescription>Paste your Discord IDs to link roles and channels.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Verification Channel ID</label>
              <Input 
                placeholder="e.g. 1102250942021238854" 
                value={settings.verification_channel_id || ""}
                onChange={(e) => updateSetting("verification_channel_id", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Quarantine Role ID</label>
              <Input 
                placeholder="e.g. 1102250942021238854" 
                value={settings.quarantine_role_id || ""}
                onChange={(e) => updateSetting("quarantine_role_id", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Verified Role ID</label>
              <Input 
                placeholder="e.g. 1102250942021238854" 
                value={settings.verified_role_id || ""}
                onChange={(e) => updateSetting("verified_role_id", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Log Channel ID (Optional)</label>
              <Input 
                placeholder="e.g. 1102250942021238854" 
                value={settings.log_channel_id || ""}
                onChange={(e) => updateSetting("log_channel_id", e.target.value)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Risk Engine */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Risk Engine & Punishments</CardTitle>
            <CardDescription>Configure how strict the system is against potential raiders.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6 md:grid-cols-2">
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Risk Threshold (1-100)</label>
                <p className="text-xs text-muted-foreground mb-2">Users scoring above this will face harder captchas.</p>
                <Input 
                  type="number" 
                  min={1} 
                  max={100} 
                  value={settings.risk_threshold_high}
                  onChange={(e) => updateSetting("risk_threshold_high", parseInt(e.target.value))}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Timeout Minutes</label>
                <Input 
                  type="number" 
                  min={1} 
                  max={1440} 
                  value={settings.timeout_minutes}
                  onChange={(e) => updateSetting("timeout_minutes", parseInt(e.target.value))}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Max Attempts</label>
                <Input 
                  type="number" 
                  min={1} 
                  max={10} 
                  value={settings.max_attempts}
                  onChange={(e) => updateSetting("max_attempts", parseInt(e.target.value))}
                />
              </div>
            </div>
            
            <div className="space-y-6 pt-2">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <label className="text-sm font-medium text-destructive">Kick on Timeout</label>
                  <p className="text-xs text-muted-foreground">Kick users who fail to verify in time.</p>
                </div>
                <Switch 
                  checked={settings.kick_on_timeout}
                  onCheckedChange={(c) => updateSetting("kick_on_timeout", c)}
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <label className="text-sm font-medium">Delete Failed Messages</label>
                  <p className="text-xs text-muted-foreground">Remove user's failed captcha replies.</p>
                </div>
                <Switch 
                  checked={settings.delete_failed_messages}
                  onCheckedChange={(c) => updateSetting("delete_failed_messages", c)}
                />
              </div>
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
