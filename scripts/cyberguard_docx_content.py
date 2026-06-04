"""Replacement text blocks for CyberGuard AI documentation (from codebase)."""

PROJECT_NAME = "CyberGuard AI"

EXECUTIVE_SUMMARY = (
    "CyberGuard AI is an AI-assisted security operations and DevSecOps readiness "
    "platform that ingests security telemetry, applies deterministic detection rules, "
    "optionally enriches findings with an AI Detection Copilot (OpenRouter), and "
    "presents analyst workflows through a modern web dashboard. The system supports "
    "incident investigation, alert triage, PDF reporting, scheduled digest reports, "
    "and a controlled local Cyber Range for demonstration and validation. "
    "Container image vulnerability scanning via Trivy and SBOM export are identified "
    "as planned enhancements (see Future Work); the current release focuses on "
    "SOC-style event monitoring, severity-based alerting, and remediation guidance."
)

# Section bodies keyed by exact Heading 2 text (or unique substring match).
SECTION_BODIES: dict[str, list[str]] = {
    "1.1 Overview": [
        EXECUTIVE_SUMMARY,
        "The platform is implemented as a full-stack application: a FastAPI backend "
        "with PostgreSQL persistence, Redis and Celery for asynchronous AI classification "
        "and PDF generation, and a Next.js (App Router) frontend dashboard. Security "
        "events are normalized into a common schema, evaluated by modular detection rules "
        "(for example brute force, port scan, SQL injection attempts, data exfiltration), "
        "and surfaced as alerts and incidents with MITRE-oriented context where applicable.",
        "Primary application areas include:",
        "Dashboard — KPIs, charts, recent alerts and incidents, and live WebSocket updates.",
        "Alerts — triage queue with severity, rule name, status workflow, and optional AI insight.",
        "Incidents — investigation cases with linked events, AI analysis, briefings, and PDF export.",
        "Attack Lab — synthetic event generation and controlled Cyber Range scenarios against a local target.",
        "Reports — downloadable incident PDFs and optional scheduled email digests.",
        "[INSERT SCREENSHOT: CyberGuard AI dashboard]",
    ],
    "1.2 Project Motivation": [
        "Security teams and student SOC operators often lack a single, repeatable environment "
        "to ingest telemetry, prioritize findings by severity, and produce evidence suitable "
        "for academic or client submission. Manual log review does not scale, and ad-hoc scripts "
        "rarely provide consistent reporting or audit trails.",
        "CyberGuard AI addresses this gap by combining rule-based detection (testable and "
        "deterministic) with optional AI explanations that do not override official severity. "
        "The platform improves DevSecOps readiness by making security visibility, structured "
        "workflows, and exportable reports accessible through one integrated interface.",
    ],
    "1.4 Problem Statement (Limitation of Current Systems)": [
        "Many small teams rely on disconnected tools: raw log viewers, spreadsheets, or "
        "single-purpose scanners without unified triage. Common limitations include:",
        "Difficulty correlating events into incidents and tracking resolution status.",
        "No consistent severity model or analyst workflow across data sources.",
        "Limited reporting for stakeholders (PDF/executive summaries).",
        "AI features that silently change alert priority without auditability.",
        "Lack of safe, local demonstration environments for training and defense presentations.",
        "CyberGuard AI targets these limitations while clearly separating deterministic "
        "detection from advisory AI output.",
    ],
    "1.5 Project Objectives": [
        "Automate ingestion and classification of security events from APIs, uploads, "
        "synthetic generators, and the Cyber Range.",
        "Detect suspicious patterns using modular, testable rules with severity labels.",
        "Provide a dashboard for monitoring alerts, incidents, and operational KPIs.",
        "Generate professional PDF security reports for incidents and scheduled digests.",
        "Offer optional AI-assisted classification and incident analysis via OpenRouter.",
        "Support controlled attack demonstrations without exposing production systems.",
        "Improve DevSecOps readiness through repeatable assessments and exportable evidence.",
        "Planned (not yet implemented): Docker image scanning with Trivy, SBOM export, "
        "and secrets scanning in CI/CD pipelines.",
    ],
    "1.7 Scope": [
        "In scope: JWT-authenticated multi-user API; per-user data isolation (owner_id); "
        "event ingest (JSON batch, single event, file upload); rule-based detection engine; "
        "alerts and incidents; dashboard analytics; WebSocket alert broadcast; incident and "
        "digest PDF reports; report schedules with optional SMTP; Attack Lab scenarios and "
        "Cyber Range integration; optional AI classification and incident analysis.",
        "Out of scope (current release): Trivy/container CVE scanning; SBOM generation; "
        "enterprise SSO; production-grade httpOnly cookie auth; full SIEM connector pack; "
        "24/7 managed SOC services. These are listed under Future Work.",
    ],
    "3.2 Functional Requirements (Restarted & Clean Version)": [
        "FR-01: Users shall register and authenticate (signup, login, refresh token).",
        "FR-02: Users shall ingest security events via API batch, single event, or file upload.",
        "FR-03: The system shall run detection rules on each ingested event and create alerts.",
        "FR-04: High-severity alerts shall open incidents linked to triggering events.",
        "FR-05: Users shall list, filter, and update alert status (new / acknowledged / resolved).",
        "FR-06: Users shall manage incidents (create, update, link events, run AI analysis).",
        "FR-07: Users shall view dashboard summary and charts for a selected time window.",
        "FR-08: Users shall generate and download incident PDF reports.",
        "FR-09: Users shall configure scheduled digest reports and optional email delivery.",
        "FR-10: Users shall run synthetic scenarios and approved Cyber Range scenarios.",
        "FR-11: The system shall queue async AI event classification when enabled.",
        "FR-12: Users shall receive real-time alert notifications via WebSocket.",
        "FR-13 (planned): Scan container images with Trivy and store SBOM/CVE results.",
    ],
    "3.3 Non‑Functional Requirements": [
        "Security: JWT access and refresh tokens; bcrypt password hashing; rate limits on auth; "
        "CORS restricted via configuration; per-user row isolation on queries.",
        "Reliability: PostgreSQL persistence; Celery retries for long-running PDF/AI tasks; "
        "health endpoint for orchestration.",
        "Performance: Paginated list APIs; async AI and PDF via worker; dashboard windows "
        "24h / 7d / 30d.",
        "Usability: Responsive Next.js UI with sidebar navigation and role-oriented pages.",
        "Maintainability: Modular FastAPI routers, SQLAlchemy models, Alembic migrations.",
        "Portability: Docker Compose stack (API, worker, beat, Postgres, Redis, range-target).",
        "Scalability: Horizontally scalable API and workers; Redis broker; stateless API design.",
    ],
    "4.1 Software Architecture": [
        "CyberGuard AI follows a three-tier architecture:",
        "Presentation tier — Next.js frontend (dashboard, alerts, incidents, attack lab, reports, settings).",
        "Application tier — FastAPI REST API and WebSocket manager under /api/v1.",
        "Data tier — PostgreSQL (events, alerts, incidents, reports, users, AI classifications).",
        "Async tier — Celery worker and beat (AI classification, PDF generation, scheduled digests).",
        "External integrations — OpenRouter (optional LLM), SMTP (optional email), local Cyber Range target.",
        "[INSERT SCREENSHOT: CyberGuard AI system architecture diagram]",
    ],
    "5.1 Tools and Technologies Used": [
        "The implementation uses the following stack (verified from repository dependencies):",
    ],
    "5.12 Automated Report Generation Module": [
        "CyberGuard AI generates PDF reports using ReportLab with optional Plotly/Kaleido charts. "
        "Incident reports include severity context, linked events, and visual summaries. "
        "Scheduled digests aggregate recent incidents per user schedule. Downloads are served "
        "via GET /api/v1/reports/{id}/download (application/pdf). Portfolio and briefing "
        "outputs are JSON APIs for in-browser use, not file exports.",
        "[INSERT SCREENSHOT: generated PDF report]",
        "Note: JSON and TXT bulk export of scan results are planned for container scanning "
        "workflows; current release provides PDF incident/digest reports only.",
    ],
    "6.2 Test Environment Setup": [
        "Recommended test environment:",
        "Docker Compose from repository root (Postgres, Redis, API, Celery worker, beat, range-target).",
        "Frontend: npm run dev in frontend/ with NEXT_PUBLIC_API_URL pointing to the API.",
        "Optional: OPENROUTER_API_KEY for AI classification and incident analysis tests.",
        "Optional: SMTP variables for scheduled digest email validation.",
        "Clone repository, copy backend/.env.example to backend/.env, set SECRET_KEY, then "
        "docker compose up --build. Run alembic migrations via API container startup.",
    ],
    "11.1 Conclusion": [
        "CyberGuard AI delivers a practical, full-stack security operations prototype suitable "
        "for academic defense, client demonstrations, and DevSecOps awareness training. By "
        "combining deterministic detection, structured analyst workflows, PDF reporting, and "
        "optional AI assistance, the platform helps teams prioritize risk and communicate "
        "findings professionally. Future integration of container vulnerability scanning "
        "(Trivy) and SBOM tooling will extend the same reporting and dashboard patterns to "
        "image-centric DevSecOps pipelines.",
    ],
    "11.2 Limitations": [
        "Results depend on quality and completeness of ingested events; the platform does not "
        "replace full penetration testing or enterprise SIEM deployments.",
        "AI features require OpenRouter configuration and remain advisory relative to rule severity.",
        "Access tokens in the demo UI use browser storage; production should use httpOnly cookies.",
        "Cyber Range scenarios operate only against the local range-target service.",
        "Container image CVE scanning and SBOM generation are not implemented in the current codebase.",
        "Vulnerability intelligence freshness depends on rule logic and ingested data, not Trivy DB.",
    ],
    "11.3 Future Work": [
        "Integrate Trivy (or equivalent) for Docker image vulnerability and secret scanning.",
        "Export scan results as JSON, TXT, and PDF with severity-based prioritization.",
        "SBOM generation and storage per image/build.",
        "CI/CD and GitHub Actions integration for pipeline gates.",
        "Historical scan tracking and multi-project dashboards.",
        "Role-based access control and enterprise authentication.",
        "Enhanced AI remediation playbooks grounded in CVE/package metadata.",
        "Email and webhook alerting for critical findings.",
    ],
}

TECH_STACK_TABLE = [
    ["Component", "Technology", "Version / notes"],
    ["Language", "Python", "3.12+"],
    ["Backend framework", "FastAPI", ">= 0.115"],
    ["ORM / DB", "SQLAlchemy 2, PostgreSQL", "16 (Compose)"],
    ["Migrations", "Alembic", ">= 1.14"],
    ["Task queue", "Celery + Redis", "Redis 7"],
    ["Frontend", "Next.js, React, TypeScript", "Next 16, React 19"],
    ["UI", "Tailwind CSS, shadcn/ui, Recharts", "—"],
    ["Auth", "JWT (python-jose), bcrypt", "—"],
    ["PDF reports", "ReportLab, Plotly, Kaleido", "—"],
    ["AI (optional)", "OpenRouter HTTP API", "Configurable model"],
    ["Detection", "Custom rule engine (Python)", "14+ rules"],
    ["Container scanning", "Trivy (planned)", "Not in current release"],
    ["Deployment", "Docker Compose", "api, worker, beat, postgres, redis"],
]

API_ENDPOINTS_TABLE = [
    ["Method", "Path", "Purpose"],
    ["POST", "/api/v1/auth/signup", "Register user"],
    ["POST", "/api/v1/auth/login", "Obtain JWT tokens"],
    ["POST", "/api/v1/events/ingest", "Batch ingest events"],
    ["POST", "/api/v1/events/upload", "Upload JSON/CSV/logs"],
    ["GET", "/api/v1/alerts", "List alerts (paginated)"],
    ["PATCH", "/api/v1/alerts/{id}/status", "Update alert status"],
    ["GET", "/api/v1/incidents", "List incidents"],
    ["POST", "/api/v1/incidents/{id}/analyze", "AI incident analysis"],
    ["POST", "/api/v1/incidents/{id}/generate-report", "Queue PDF report"],
    ["GET", "/api/v1/reports/{id}/download", "Download PDF"],
    ["GET", "/api/v1/dashboard/summary", "Dashboard KPIs"],
    ["WS", "/api/v1/ws?token=", "Live alert broadcast"],
    ["GET", "/api/v1/range/scenarios", "List Cyber Range scenarios"],
    ["POST", "/api/v1/range/scenarios/{id}/run", "Run range scenario"],
]

EVENT_MODEL_TABLE = [
    ["Field", "Description"],
    ["timestamp", "Event time (UTC)"],
    ["source_ip / destination_ip", "Network endpoints"],
    ["username", "Account involved"],
    ["event_type", "Category (auth, network, etc.)"],
    ["severity", "low | medium | high | critical"],
    ["message / raw_log", "Human-readable and raw log line"],
    ["protocol / port", "Network metadata"],
    ["metadata", "JSON additional fields"],
    ["ai_assessment", "Optional AI classification (API response)"],
]

SECTION_BODIES["4.3.1 Purpose of the AI Component"] = [
    "The AI Detection Copilot provides advisory classification of ingested security events "
    "using OpenRouter-hosted language models. It suggests attack type, confidence, MITRE "
    "tactics/techniques, and recommended actions. Official alert severity remains rule-based "
    "unless an analyst changes it manually.",
    "[INSERT SCREENSHOT: AI insight dialog on alert]",
]

SECTION_BODIES["5.2 Implementation of the ML Prediction Engine"] = [
    "The production AI path is implemented in ai_detection_service.py and Celery task "
    "classify_events_task. After EventService commits ingested events, eligible event IDs "
    "are queued for async classification when AI_DETECTION_ENABLED is true and "
    "OPENROUTER_API_KEY is configured.",
    "Outputs are stored in the ai_classifications table and exposed as ai_assessment on "
    "event and alert API responses. High-confidence suspicious classifications may create "
    "an ai_classifier alert only when no rule-based alert exists for the same event.",
]

GLOBAL_REPLACEMENTS: list[tuple[str, str]] = [
    ("Intrusion Detection System (IDS)", "CyberGuard AI security operations platform"),
    ("Intrusion Detection System", "CyberGuard AI"),
    (" the IDS ", " CyberGuard AI "),
    ("The IDS ", "CyberGuard AI "),
    ("IDS Monitor", "CyberGuard AI"),
    ("UC-IDS-", "UC-CG-"),
    ("packet capture", "security event ingestion"),
    ("Packet Capture", "Event Ingestion"),
    ("packet sniffing", "event ingestion"),
    ("Sniffing Engine", "Event Ingestion Service"),
    ("Network Monitoring Tab", "Dashboard"),
    ("Endpoint Alerts Tab", "Alerts"),
    ("Network Analytics Tab", "Dashboard Analytics"),
    ("IOC Signatures Tab", "Detection Rules Configuration"),
    ("Scapy", "FastAPI / httpx"),
    ("Matplotlib", "Recharts"),
    ("Flask server", "FastAPI API"),
    ("HTML/CSV reports", "PDF reports"),
    ("Android-based Alert Viewer", "Next.js web dashboard"),
    ("Machine Learning Prediction Module", "AI Detection Copilot (OpenRouter)"),
    ("risk score based on behavioral network features", "AI classification with confidence and MITRE context"),
    ("Discord", "WebSocket"),
    ("discord", "websocket"),
    ("packet sniff", "event ingest"),
    ("Scapy", "httpx"),
    ("Wireshark", "log upload"),
    ("live packets", "live events"),
    ("captured packets", "ingested events"),
    ("TCP SYN Scan", "port scan scenario (Cyber Range)"),
    ("LLMNR/NBT-NS", "controlled range demonstration"),
]

HEADING_RENAMES: dict[str, str] = {
    "Chapter 2: Literature Review": "Chapter 2: Background and Related Work",
    "2.1 Introduction to IDS": "2.1 Security Operations and Detection Concepts",
    "2.2 IDS Architecture": "2.2 SOC Platform Architecture Patterns",
    "2.3 Detection Types": "2.3 Rule-Based and AI-Assisted Detection",
    "5.9 Sniffing Engine (Packet Capture Module)": "5.9 Event Ingestion Service",
    "5.6 CSV Export and Report Generation Module": "5.6 PDF Report Generation Module",
    "5.8 Discord Notification Module": "5.8 WebSocket Real-Time Notifications",
    "5.7 Endpoint Alert Server Module": "5.7 FastAPI REST and WebSocket Layer",
    "Appendix A – User Interface Screenshots": "Appendix A – CyberGuard AI User Interface Screenshots",
}
