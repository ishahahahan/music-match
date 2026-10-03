type Props = {
  processed: number;
  total: number;
  stage?: string;
};

/**
 * Polls visually with `GET /api/v1/sync/status` in Phase 2 — this is the render-only
 * starting point: counts come from the job document (fetched/found/failed), not guessed.
 */
export function SyncProgress({ processed, total, stage = "Fetching top tracks" }: Props) {
  const pct = total > 0 ? Math.min(1, processed / total) : 0;
  return (
    <div className="mt-6 rounded-xl border border-[#232d3a] bg-[#121820] p-5">
      <div className="mb-2 flex items-baseline justify-between text-sm">
        <span className="text-gray-400">{stage}</span>
        <span className="tabular-nums text-gray-300">
          {processed} / {total}
        </span>
      </div>
      <div
        className="h-2 w-full overflow-hidden rounded bg-[#171f2a]"
        role="progressbar"
        aria-valuenow={Math.round(pct * 100)}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="h-full rounded transition-all duration-500"
          style={{ width: `${pct * 100}%`, background: "var(--accent)" }}
        />
      </div>
    </div>
  );
}
