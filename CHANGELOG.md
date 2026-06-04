# Documentation CHANGELOG — CyberGuard AI DOCX

## 2026-05-20 — Template conversion (`Project 404 Final Version 1.docx`)

### Summary

Converted the graduation IDS template into **CyberGuard AI** technical documentation while preserving chapter order, heading hierarchy, numbering, tables, and overall document length. Content reflects the **actual repository** (FastAPI SOC platform), not unimplemented Trivy/SBOM features.

### Output files

| File | Description |
|------|-------------|
| `docs/CyberGuard AI - Technical Documentation.docx` | Primary deliverable |
| `documentation_mapping.md` | Section-by-section mapping table |
| `scripts/update_cyberguard_docx.py` | Regeneration script |
| `scripts/cyberguard_docx_content.py` | Replacement text and tables |
| `docs/docx_headings_extract.txt` | Heading index extracted from template |

### Structural preservation

- All **176** heading nodes retained (chapter/section numbering unchanged unless renamed for clarity).
- **16** tables preserved; stakeholder and use-case tables rewritten for CyberGuard workflows.
- Figure/table caption style and page order unchanged (no wholesale delete/rebuild).

### Major content rewrites (14 sections)

- 1.1 Overview, 1.2 Motivation, 1.4 Problem Statement, 1.5 Objectives, 1.7 Scope  
- 3.2 Functional Requirements, 3.3 Non-Functional Requirements  
- 4.1 Software Architecture, 4.3.1 AI purpose, 5.2 AI detection implementation  
- 5.12 Report generation, 6.2 Test environment, 11.1 Conclusion, 11.2 Limitations, 11.3 Future Work  

### Heading renames (9)

Examples: Chapter 2 title, IDS → SOC terminology, Sniffing Engine → Event Ingestion, Discord module → WebSocket notifications, Appendix A title.

### Global terminology pass (~300+ paragraph/table cell updates)

- IDS / packet-centric language → CyberGuard AI / event-centric language  
- UC-IDS-* → UC-CG-* in use case tables  
- Tool names aligned to stack (FastAPI, Next.js, ReportLab, Celery, PostgreSQL)  

### Additions

- **§5.1.6 REST API Overview** with endpoint list from `backend/app/api/v1/routes/`  
- **Screenshot placeholders** for dashboard, architecture, PDF report, AI dialog, OpenAPI docs  
- **Future Work** explicitly lists Trivy, SBOM, JSON/TXT scan exports, CI/CD integration  

### Accuracy constraints (per codebase review)

| Claim | Status in repo |
|-------|----------------|
| Rule-based detection + incidents | Implemented |
| PDF reports + schedules | Implemented |
| OpenRouter AI copilot | Implemented (optional) |
| Cyber Range | Implemented (Docker) |
| Trivy / Docker CVE scan / SBOM | **Not implemented** — Future Work only |
| JSON/TXT vulnerability report download | **Not implemented** — PDF (+ JSON briefing APIs) only |

### Regeneration

```bash
python scripts/update_cyberguard_docx.py
```

Optional arguments: `--input`, `--output`.

### Recommended manual follow-up before submission

1. Replace all `[INSERT SCREENSHOT: …]` placeholders with real UI captures.  
2. Review Chapters 2, 6–10 for any remaining packet-capture narrative and align with Attack Lab / Range demos.  
3. Update title page team names/signatures if required by your institution.  
4. Refresh References with citations you actually used.  
5. Update class/sequence diagrams in Chapter 4 to match FastAPI + Next.js (if graders check diagrams).  
