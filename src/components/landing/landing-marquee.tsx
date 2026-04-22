const labels = [
  "Rule-based detection",
  "Real-time alerts",
  "WebSocket feed",
  "Incidents",
  "OpenRouter AI",
  "PDF reports",
  "Scheduled digests",
  "FastAPI",
  "Next.js App Router",
  "PostgreSQL",
  "Redis",
  "Celery",
  "JWT auth",
  "Severity triage",
  "Docker-ready",
  "Alembic migrations",
  "TanStack Query",
];

function Chip({ children }: { children: string }) {
  return (
    <span className="mx-2 inline-flex shrink-0 items-center rounded-full border border-border/55 bg-card/55 px-4 py-2 text-xs font-medium uppercase tracking-wider text-muted-foreground shadow-sm shadow-black/20 backdrop-blur-sm transition-colors duration-200 hover:border-cyan-500/35 hover:text-foreground">
      {children}
    </span>
  );
}

export function LandingMarquee() {
  const doubled = [...labels, ...labels];

  return (
    <section className="relative z-10 overflow-hidden border-y border-border/45 bg-muted/20 py-12 shadow-inner shadow-black/30">
      <p className="sr-only">Technology and capability highlights</p>
      <div className="flex overflow-hidden [mask-image:linear-gradient(to_right,transparent,black_8%,black_92%,transparent)]">
        <div className="landing-marquee-track flex gap-0 py-1">
          {doubled.map((label, i) => (
            <Chip key={`${label}-${i}`}>{label}</Chip>
          ))}
        </div>
      </div>
    </section>
  );
}
