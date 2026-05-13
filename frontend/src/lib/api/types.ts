export type Severity = "low" | "medium" | "high" | "critical";
export type AlertStatus = "new" | "acknowledged" | "resolved";
export type IncidentStatus = "open" | "investigating" | "resolved" | "false_positive";

export interface User {
  id: number;
  name: string;
  email: string;
  role: string;
  created_at: string;
}

export interface Event {
  id: number;
  timestamp: string;
  source_ip: string | null;
  destination_ip: string | null;
  username: string | null;
  event_type: string;
  status: string | null;
  severity: Severity;
  message: string | null;
  protocol: string | null;
  port: number | null;
  raw_log: string | null;
  source_system: string | null;
  metadata: Record<string, unknown> | null;
  ai_assessment: AIClassification | null;
  created_at: string;
}

export interface Alert {
  id: number;
  event_id: number | null;
  title: string;
  description: string | null;
  severity: Severity;
  rule_name: string;
  status: AlertStatus;
  reasoning: string | null;
  ai_assessment: AIClassification | null;
  mitre_techniques: MitreTechnique[];
  threat_profile: ThreatProfile | null;
  created_at: string;
  updated_at: string;
}

export interface MitreTechnique {
  tactic: string;
  technique: string;
  technique_id: string;
  sub_technique: string | null;
}

export interface ThreatProfile {
  actor: string;
  confidence: string;
  cve_references: string[];
  kill_chain_phase: string;
}

export interface AIClassification {
  id: number;
  event_id: number;
  alert_id: number | null;
  incident_id: number | null;
  provider: string;
  model: string;
  prompt_type: string;
  attack_type: string;
  confidence: number;
  suggested_severity: Severity;
  why_classified: string;
  evidence: string[];
  mitre_tactics: string[];
  mitre_techniques: string[];
  recommended_actions: string[];
  should_create_alert: boolean;
  raw_response: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface Incident {
  id: number;
  title: string;
  summary: string;
  severity: Severity;
  status: IncidentStatus;
  ai_summary: string | null;
  remediation: string | null;
  analyst_notes: string | null;
  created_at: string;
  resolved_at: string | null;
  updated_at: string;
  mitre_techniques: MitreTechnique[];
  threat_profiles: ThreatProfile[];
  events: Event[];
}

export interface IncidentPortfolioAI {
  executive_summary: string;
  key_findings: string[];
  risks: string[];
  recommendations: string[];
  themes: string[];
}

export interface IncidentPortfolioReport {
  generated_at: string;
  filters: { status: string | null; severity: string | null; q: string | null };
  max_items: number;
  truncated: boolean;
  truncation_note: string | null;
  stats: Record<string, unknown>;
  charts: {
    severity_bar: Array<{ name: string; count: number }>;
    status_bar: Array<{ name: string; count: number }>;
    weekly_line: Array<{ week_start: string; count: number }>;
    rules_bar: Array<{ rule_name: string; count: number }>;
    mitre_bar: Array<{ technique_id: string; label: string; count: number }>;
  };
  ai: IncidentPortfolioAI | null;
  ai_error: string | null;
}

export interface IncidentBriefing {
  incident_id: number;
  mode: "executive" | "technical";
  executive_summary: string;
  business_impact: string;
  technical_findings: string[];
  recommended_actions: string[];
  mitre_highlights: string[];
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface DashboardSummary {
  events_today: number;
  suspicious_events: number;
  dangerous_events: number;
  active_incidents: number;
  resolved_incidents: number;
  open_alerts: number;
  mtta_minutes: number;
  mttr_minutes: number;
  new_alerts_24h: number;
  unassigned_open_incidents: number;
  critical_open_incidents: number;
  event_to_alert_conversion_pct: number;
  mitre_coverage_count: number;
  security_overview: string | null;
}

export interface AttackTimelinePoint {
  bucket: string;
  events: number;
  alerts: number;
  incidents: number;
}

export interface WorkQueueBuckets {
  alerts_new: number;
  alerts_acknowledged: number;
  alerts_resolved: number;
  incidents_open: number;
  incidents_investigating: number;
  incidents_resolved: number;
  incidents_overdue: number;
}

export interface RuleCount {
  rule_name: string;
  count: number;
}

export interface SourceRiskPoint {
  source_ip: string;
  high_critical_events: number;
  alerts: number;
}

export interface MitreCoveragePoint {
  technique_id: string;
  count: number;
}

export interface AnomalySignals {
  exfiltration_alerts: number;
  auth_anomaly_alerts: number;
  outbound_transfer_events: number;
  privileged_login_events: number;
}

export interface DashboardCharts {
  severity_distribution: { severity: Severity; count: number }[];
  events_timeline: { bucket: string; count: number }[];
  top_event_types: { event_type: string; count: number }[];
  source_ip_activity: { source_ip: string; count: number }[];
  attack_timeline: AttackTimelinePoint[];
  work_queue: WorkQueueBuckets;
  top_rules_24h: RuleCount[];
  top_risks: SourceRiskPoint[];
  mitre_coverage: MitreCoveragePoint[];
  anomaly_signals: AnomalySignals;
}

export interface Report {
  id: number;
  incident_id: number;
  report_type: string;
  file_path: string;
  created_at: string;
}

export type ReportScheduleFrequency = "hourly" | "twice_daily" | "daily" | "weekly";

export interface ReportSchedule {
  id: number;
  user_id: number;
  min_severity: Severity;
  frequency: ReportScheduleFrequency;
  recipient_email: string;
  enabled: boolean;
  /** HH:MM UTC; null = run whenever the interval elapses (legacy) */
  preferred_time_utc: string | null;
  /** 0=Monday … 6=Sunday; only for weekly */
  weekly_day_utc: number | null;
  last_run_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface UIRecommendation {
  id: string;
  title: string;
  rationale: string;
  action_label: string;
  action_href: string;
  severity: "low" | "medium" | "high" | "info" | string;
}
