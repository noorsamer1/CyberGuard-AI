"use client";

import { useId } from "react";

import { cn } from "@/lib/utils";

type CyberGuardMarkProps = {
  /** Pixel width/height of the square viewBox. */
  size?: number;
  className?: string;
};

/**
 * Custom CyberGuard mark: shield + activity bars (monitoring) with cyan→violet stroke.
 * Use beside the wordmark in header/footer; gradient ids are unique per mount.
 */
export function CyberGuardMark({ size = 36, className }: CyberGuardMarkProps) {
  const raw = useId();
  const gid = `cg-${raw.replace(/:/g, "")}`;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      className={cn("shrink-0 overflow-visible", className)}
      role="img"
      aria-hidden
    >
      <defs>
        <linearGradient id={`${gid}-s`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="rgb(103 232 249)" />
          <stop offset="55%" stopColor="rgb(34 211 238)" />
          <stop offset="100%" stopColor="rgb(167 139 250)" />
        </linearGradient>
      </defs>
      <path
        d="M16 2.25 27.25 6.75v8.35c0 5.15-3.35 10.05-8.55 12.55a1.35 1.35 0 0 1-1.4 0C12.1 25.15 8.75 20.25 8.75 15.1V6.75L16 2.25z"
        fill="rgba(6, 10, 22, 0.72)"
        stroke={`url(#${gid}-s)`}
        strokeWidth="1.35"
        strokeLinejoin="round"
      />
      <g stroke={`url(#${gid}-s)`} strokeWidth="1.85" strokeLinecap="round">
        <line x1="11.5" y1="17.5" x2="11.5" y2="22.25" opacity="0.85" />
        <line x1="16" y1="15.25" x2="16" y2="22.25" />
        <line x1="20.5" y1="18.25" x2="20.5" y2="22.25" opacity="0.85" />
      </g>
      <circle cx="16" cy="11.25" r="1.65" fill={`url(#${gid}-s)`} opacity="0.95" />
    </svg>
  );
}

type CyberGuardLockupProps = {
  /** Show “CyberGuard AI” next to the mark. */
  showWordmark?: boolean;
  /** Mark size in px. */
  markSize?: number;
  /** Smaller chrome for footer / dense UI. */
  variant?: "default" | "compact";
  className?: string;
};

export function CyberGuardLockup({
  showWordmark = true,
  markSize,
  variant = "default",
  className,
}: CyberGuardLockupProps) {
  const resolvedMark = markSize ?? (variant === "compact" ? 24 : 34);
  const chrome =
    variant === "compact"
      ? "rounded-xl p-1 ring-cyan-400/30 shadow-[0_0_16px_-10px_rgba(34,211,238,0.35)]"
      : "rounded-2xl p-1.5 ring-cyan-400/35 shadow-[0_0_24px_-8px_rgba(34,211,238,0.35)]";

  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <span
        className={cn(
          "relative flex shrink-0 items-center justify-center bg-gradient-to-br from-cyan-500/18 via-zinc-950/80 to-violet-500/15 ring-1 ring-inset",
          chrome,
        )}
      >
        <CyberGuardMark size={resolvedMark} />
      </span>
      {showWordmark ? (
        <span
          className={cn(
            "font-[family-name:var(--font-display)] font-semibold tracking-tight text-foreground",
            variant === "compact" ? "text-sm" : "text-lg",
          )}
        >
          CyberGuard AI
        </span>
      ) : null}
    </span>
  );
}
