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

export interface BriefingBenchmark {
  average_score: number | null;
  latest_score: number | null;
  sessions_completed: number;
  trend: string;
}

export interface IncidentBriefing {
  incident_id: number;
  mode: "executive" | "technical";
  executive_summary: string;
  business_impact: string;
  technical_findings: string[];
  recommended_actions: string[];
  mitre_highlights: string[];
  learning_benchmark: BriefingBenchmark;
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

export type ExerciseSessionStatus = "active" | "completed" | "expired" | "cancelled";
export type ExerciseActionType =
  | "acknowledge_alert"
  | "resolve_alert"
  | "escalate_incident"
  | "add_note"
  | "request_hint";

export interface ExerciseScenario {
  id: string;
  name: string;
  description: string;
  severity: string;
  mitre_tactics: string[];
  mitre_techniques: string[];
  threat_actor: string;
  estimated_alerts: number;
  duration_minutes: number;
}

export interface ExerciseAction {
  id: number;
  session_id: number;
  user_id: number;
  action_type: ExerciseActionType;
  target_type: string | null;
  target_id: number | null;
  notes: string | null;
  created_at: string;
}

export interface ExerciseSession {
  id: number;
  user_id: number;
  scenario_id: string;
  status: ExerciseSessionStatus;
  duration_minutes: number;
  started_at: string;
  ends_at: string;
  completed_at: string | null;
  overall_score: number | null;
  detection_score: number | null;
  analysis_score: number | null;
  response_score: number | null;
  reporting_score: number | null;
  strengths: string | null;
  weaknesses: string | null;
  hints_used: number;
  result_json: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  actions: ExerciseAction[];
}

export interface DoctorCoachRequest {
  session_id: number;
  question: string;
  language: "en" | "ar";
}

export interface DoctorCoachResponse {
  session_id: number;
  diagnosis: string;
  likely_gap: string;
  coaching_steps: string[];
  quick_quiz: string[];
}

export interface UIRecommendation {
  id: string;
  title: string;
  rationale: string;
  action_label: string;
  action_href: string;
  severity: "low" | "medium" | "high" | "info" | string;
}
