"use client";

import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import { toast } from "sonner";

import { SeverityBadge } from "@/components/common/severity-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { apiFetch } from "@/lib/api/client";
import type { AIClassification, Alert } from "@/lib/api/types";

function formatAttackType(attackType: string): string {
  return attackType.replaceAll("_", " ");
}

function InsightBody({
  ruleSeverity,
  assessment,
}: {
  ruleSeverity: Alert["severity"];
  assessment: AIClassification;
}) {
  const confidencePct = Math.round((assessment.confidence ?? 0) * 100);

  return (
    <div className="space-y-5 pr-1">
      <p className="rounded-md border border-amber-500/25 bg-amber-500/10 px-3 py-2 text-xs text-amber-100/90">
        Advisory only: rule-based severity is unchanged unless you edit the alert manually.
      </p>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-lg border border-border/60 bg-muted/30 p-3">
          <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            Rule severity
          </p>
          <div className="mt-2">
            <SeverityBadge severity={ruleSeverity} />
          </div>
          <p className="mt-2 text-xs text-muted-foreground">From your detection rule.</p>
        </div>
        <div className="rounded-lg border border-cyan-500/20 bg-cyan-500/5 p-3">
          <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            AI suggested severity
          </p>
          <div className="mt-2">
            <SeverityBadge severity={assessment.suggested_severity} />
          </div>
          <p className="mt-2 text-xs text-muted-foreground">Model recommendation for triage context.</p>
        </div>
      </div>

      <div>
        <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
          Model confidence
        </p>
        <div className="mt-2 flex items-center gap-3">
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-cyan-500/80 transition-[width] duration-300"
              style={{ width: `${Math.min(100, Math.max(0, confidencePct))}%` }}
            />
          </div>
          <span className="shrink-0 font-mono text-sm tabular-nums text-foreground">{confidencePct}%</span>
        </div>
        <p className="mt-1.5 text-xs text-muted-foreground">
          How certain the model is about the attack label and suggested severity (not a guarantee).
        </p>
      </div>

      <div>
        <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
          Attack type (AI)
        </p>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <Badge variant="outline" className="border-cyan-500/30 bg-cyan-500/10 text-cyan-200">
            <Sparkles className="mr-1 h-3 w-3" />
            {formatAttackType(assessment.attack_type)}
          </Badge>
        </div>
        <p className="mt-2 text-sm leading-relaxed text-foreground/90">{assessment.why_classified}</p>
        <p className="mt-1 text-xs text-muted-foreground">
          The model chose this attack family and severity from the event context and evidence below.
        </p>
      </div>

      {assessment.evidence.length > 0 && (
        <div>
          <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            Evidence strings
          </p>
          <ul className="mt-2 list-inside list-disc space-y-1 text-xs text-muted-foreground">
            {assessment.evidence.map((line, i) => (
              <li key={i} className="leading-relaxed">
                {line}
              </li>
            ))}
          </ul>
        </div>
      )}

      {(assessment.mitre_tactics.length > 0 || assessment.mitre_techniques.length > 0) && (
        <div className="space-y-2">
          {assessment.mitre_tactics.length > 0 && (
            <div>
              <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                MITRE tactics
              </p>
              <div className="mt-1.5 flex flex-wrap gap-1">
                {assessment.mitre_tactics.map((t) => (
                  <span
                    key={t}
                    className="rounded border border-violet-500/30 bg-violet-500/10 px-2 py-0.5 text-[11px] text-violet-200"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}
          {assessment.mitre_techniques.length > 0 && (
            <div>
              <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                MITRE techniques
              </p>
              <div className="mt-1.5 flex flex-wrap gap-1">
                {assessment.mitre_techniques.map((t) => (
                  <span
                    key={t}
                    className="rounded border border-violet-500/30 bg-violet-500/10 px-2 py-0.5 font-mono text-[11px] text-violet-200"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {assessment.recommended_actions.length > 0 && (
        <div>
          <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            Recommended actions
          </p>
          <ol className="mt-2 list-inside list-decimal space-y-1 text-xs text-muted-foreground">
            {assessment.recommended_actions.map((line, i) => (
              <li key={i} className="leading-relaxed">
                {line}
              </li>
            ))}
          </ol>
        </div>
      )}

      <p className="text-[11px] text-muted-foreground">
        Model: {assessment.model} · {assessment.provider}
      </p>
    </div>
  );
}

export type AlertAIInsightDialogProps = {
  alert: Alert | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onClassificationStored: () => void;
};

export function AlertAIInsightDialog({
  alert,
  open,
  onOpenChange,
  onClassificationStored,
}: AlertAIInsightDialogProps) {
  const [assessment, setAssessment] = useState<AIClassification | null>(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (open && alert) {
      setAssessment(alert.ai_assessment);
    }
  }, [open, alert]);

  async function runClassify() {
    if (!alert) return;
    setRunning(true);
    try {
      const result = await apiFetch<AIClassification>(`/alerts/${alert.id}/ai-classify`, {
        method: "POST",
      });
      setAssessment(result);
      onClassificationStored();
      toast.success("AI insight ready");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "AI insight failed");
    } finally {
      setRunning(false);
    }
  }

  const hasEvent = Boolean(alert?.event_id);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[min(90vh,640px)] gap-0 p-0 sm:max-w-lg" showCloseButton>
        <DialogHeader className="border-b border-border/60 px-4 py-4">
          <DialogTitle className="flex items-center gap-2 pr-8">
            <Sparkles className="h-4 w-4 shrink-0 text-cyan-400" />
            AI insight
          </DialogTitle>
          <DialogDescription className="text-left">
            {alert?.title ?? "Optional second opinion on severity and attack type."}
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="max-h-[calc(min(90vh,640px)-8rem)] px-4 py-4">
          {!alert ? (
            <p className="text-sm text-muted-foreground">No alert selected.</p>
          ) : !hasEvent ? (
            <p className="text-sm text-muted-foreground">
              This alert has no linked event, so there is not enough context for the model to classify.
            </p>
          ) : assessment ? (
            <InsightBody ruleSeverity={alert.severity} assessment={assessment} />
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Run an on-demand analysis to see suggested severity, confidence, rationale, and attack
                typing. This does not change stored severity.
              </p>
              <Button type="button" onClick={() => void runClassify()} disabled={running}>
                {running ? "Running…" : "Run AI analysis"}
              </Button>
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
