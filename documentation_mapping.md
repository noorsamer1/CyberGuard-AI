# Documentation mapping — Project 404 template → CyberGuard AI

Source template: `Project 404 Final Version 1.docx` (IDS graduation structure, ~245 pages).  
Output: `docs/CyberGuard AI - Technical Documentation.docx`.

**Codebase note:** The repository implements a **SOC monitoring platform** (FastAPI, events, rules, alerts, incidents, PDF reports, Cyber Range). **Trivy / Docker image CVE scanning / SBOM export are not implemented**; they are documented under Future Work and in scope notes, not as shipped features.

| Original section | CyberGuard AI section | Action |
|------------------|----------------------|--------|
| Title / front matter | CyberGuard AI — Technical Documentation | Rewrite titles |
| Chapter 1: Introduction | Chapter 1: Introduction (same) | Rewrite bodies (1.1–1.7) |
| 1.1 Overview | 1.1 Overview | Rewrite — executive summary, dashboard areas |
| 1.2 Project Motivation | 1.2 Project Motivation | Rewrite |
| 1.3 Literature review (in Ch.1) | 1.3 Review of Related Literature | Adapt — SOC/DevSecOps context |
| 1.4 Problem Statement | 1.4 Problem Statement | Rewrite |
| 1.5 Project Objectives | 1.5 Project Objectives | Rewrite + planned Trivy |
| 1.6 Project Plan | 1.6 Project Plan | Keep structure; global term replace |
| 1.7 Scope | 1.7 Scope | Rewrite in/out of scope |
| Chapter 2: Literature Review | Chapter 2: Background and Related Work | Rename + adapt |
| 2.1 Introduction to IDS | 2.1 Security Operations and Detection Concepts | Rename + adapt |
| 2.2 IDS Architecture | 2.2 SOC Platform Architecture Patterns | Rename + adapt |
| 2.3 Detection Types | 2.3 Rule-Based and AI-Assisted Detection | Rename + adapt |
| 2.4–2.6 Research sections | Same numbering | Adapt terminology (global replace) |
| Chapter 3: System Analysis | Chapter 3: System Analysis (same) | Rewrite FR/NFR; update tables |
| 3.1 Stakeholders | 3.1 Stakeholders | Rewrite stakeholder table |
| 3.2 Functional Requirements | 3.2 Functional Requirements | Full rewrite (FR-01–FR-13) |
| 3.3 Non-Functional Requirements | 3.3 Non-Functional Requirements | Full rewrite |
| 3.4 Use Case Diagram | 3.4 Use Case Diagram | Keep; update caption text |
| 3.5 Use Cases (UC-IDS-*) | 3.5 Use Cases (UC-CG-*) | Rewrite use case tables |
| Chapter 4: System Design | Chapter 4: System Design (same) | Rewrite 4.1; adapt 4.2–4.4 |
| 4.1 Software Architecture | 4.1 Software Architecture | Full rewrite (3-tier + async) |
| 4.2 Sequence / class diagrams | 4.2 Software Design | Keep diagrams; update labels via replace |
| 4.3 ML Prediction Module | 4.3 AI Detection Copilot | Rewrite 4.3.1, 5.2; adapt subsections |
| 4.4 UI (Network/Endpoint tabs) | 4.4 UI (Dashboard/Alerts/Incidents) | Rename headings; screenshot placeholders |
| Chapter 5: Implementation | Chapter 5: Implementation (same) | Adapt modules to backend services |
| 5.1 Tools and Technologies | 5.1 Tools and Technologies | Rewrite intro; add 5.1.6 API table |
| 5.2 ML Prediction Engine | 5.2 AI Detection Service | Full rewrite |
| 5.3 Code fragments | 5.3 Important Code Fragments | Adapt references to FastAPI/React |
| 5.4–5.5 Packet / threat logging | Event ingestion & alert pipeline | Adapt (global + headings) |
| 5.6 CSV/HTML reports | 5.6 PDF Report Generation | Rewrite |
| 5.7 Endpoint Flask server | 5.7 FastAPI REST and WebSocket | Rename |
| 5.8 Discord notifications | 5.8 WebSocket Real-Time Notifications | Rename + replace |
| 5.9 Sniffing engine | 5.9 Event Ingestion Service | Rename + replace |
| 5.10–5.11 Traffic analysis / filtering | Detection rules & alert views | Adapt |
| 5.12 Automated reports | 5.12 Automated Report Generation | Full rewrite (PDF) |
| 5.13 Mobile IDS | Web dashboard (Next.js) | Adapt — PWA/mobile as future |
| Chapter 6: Testing | Chapter 6: Testing (same) | Rewrite 6.2 setup; adapt scenarios to range |
| 6.4 Attack scenarios (nmap etc.) | Cyber Range / synthetic scenarios | Adapt narrative |
| Chapter 7: Network Analysis | Chapter 7: Deployment & Environment | Adapt — Docker Compose topology |
| Chapter 8: Network Design | Chapter 8: Deployment Architecture | Adapt — logical/physical compose services |
| Chapter 9: Network Implementation | Chapter 9: Deployment Implementation | Adapt — compose steps |
| Chapter 10: Quality Analysis | Chapter 10: Quality Analysis (same) | Adapt metrics to alerts/incidents |
| Chapter 11: Conclusion | Chapter 11: Conclusion (same) | Rewrite 11.1–11.3 |
| References | References | Keep; add CyberGuard-related citations as needed |
| Appendix A — UI screenshots | Appendix A — CyberGuard AI UI | Rename; placeholders |
| Appendix B — Code | Appendix B — Code Documentation | Point to backend/app, frontend/src |

## Content not in original template (added or embedded)

| Topic | Location in output |
|-------|------------------|
| REST API endpoint table | Inserted after §5.1 (5.1.6) |
| Trivy / SBOM (planned) | §1.5, §1.7, §11.3 Future Work |
| Cyber Range safety model | §1.7, §5.x (via replace), README-aligned |
| WebSocket alerts | §5.8 rename, FR-12 |
| OpenRouter AI copilot | §4.3, §5.2, limitations |

## Screenshot placeholders inserted

- `[INSERT SCREENSHOT: CyberGuard AI dashboard]`
- `[INSERT SCREENSHOT: CyberGuard AI system architecture diagram]`
- `[INSERT SCREENSHOT: generated PDF report]`
- `[INSERT SCREENSHOT: AI insight dialog on alert]`
- `[INSERT SCREENSHOT: OpenAPI /docs page]`

Replace placeholders with actual captures before final submission.
