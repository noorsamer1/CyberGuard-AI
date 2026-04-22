"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api/client";
import type { User } from "@/lib/api/types";
import { useAuthStore } from "@/store/auth-store";

export default function ProfilePage() {
  const qc = useQueryClient();
  const setUser = useAuthStore((s) => s.setUser);
  const { data: me } = useQuery({
    queryKey: ["me-profile"],
    queryFn: () => apiFetch<User>("/auth/me"),
  });
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");

  useEffect(() => {
    if (me) {
      setName(me.name);
      setEmail(me.email);
    }
  }, [me]);

  const save = useMutation({
    mutationFn: () =>
      apiFetch<User>("/users/me", {
        method: "PATCH",
        json: { name: name || undefined, email: email || undefined },
      }),
    onSuccess: (u) => {
      setUser(u);
      toast.success("Profile updated");
      qc.invalidateQueries({ queryKey: ["me-profile"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Profile</h1>
        <p className="text-sm text-muted-foreground">Your analyst identity in CyberGuard AI.</p>
      </div>
      <Card className="border-border/60 bg-card/40">
        <CardHeader>
          <CardTitle className="text-base">Account</CardTitle>
          <CardDescription>Update display name and email.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input id="name" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <Button onClick={() => save.mutate()} disabled={save.isPending}>
            Save changes
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
