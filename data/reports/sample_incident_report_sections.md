# Sample Incident Report Sections

- PDF: `sample_incident_report_v2.pdf`
- Incident ID: 1

## Deterministic sections
- Incident status and metrics (status, MTTA, MTTR, event count)
- Event severity breakdown
- Affected source IPs and destinations
- Correlation summary (alerts, correlated events, rule families)
- Attack timeline table

## AI narrative (advisory)
- Executive summary
- Analysis notes (root cause, impact)
- Prioritized remediation

## Context snapshot
```json
{
  "incident_status": "investigating",
  "severity_breakdown": {
    "medium": 1
  },
  "mtta": "7.9h",
  "mttr": "N/A",
  "affected_source_ips": [
    "127.0.0.1"
  ],
  "affected_destinations": [
    "range-target"
  ],
  "attack_timeline": [
    {
      "phase": "first_observed",
      "timestamp": "2026-05-30T12:00:05",
      "detail": "First linked event (authentication)"
    },
    {
      "phase": "authentication",
      "timestamp": "2026-05-30T12:00:05",
      "detail": "1 event(s) of type authentication"
    }
  ],
  "correlation_summary": {
    "alert_count": 1,
    "correlated_event_count": 1,
    "rule_families": [
      "failed_login_burst"
    ],
    "attack_types": [
      "brute_force"
    ]
  },
  "remediation_progress": "In progress \u2014 investigation underway.",
  "event_count": 1,
  "first_event_at": "2026-05-30T12:00:05",
  "last_event_at": "2026-05-30T12:00:05"
}
```