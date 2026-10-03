type Props = {
  name: string;
  /** Overall compatibility 0–1 (0.4 genre + 0.3 artists + 0.3 audio). */
  score: number;
  sharedTopArtist?: string;
};

/** Compact card for a potential match — pairs with ScoreBreakdown on the detail page. */
export function MatchCard({ name, score, sharedTopArtist }: Props) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-[#232d3a] bg-[#121820] p-5">
      <div>
        <div className="text-lg font-semibold">{name}</div>
        {sharedTopArtist ? (
          <div className="mt-1 text-xs text-gray-400">
            Top artist in common: <span className="text-gray-300">{sharedTopArtist}</span>
          </div>
        ) : null}
      </div>
      <div
        className="text-2xl font-bold tabular-nums"
        style={{ color: "var(--accent)" }}
        aria-label={`${Math.round(score * 100)} percent compatible`}
      >
        {(score * 100).toFixed(0)}%
      </div>
    </div>
  );
}
