type Props = { genre: number; artist: number; audio: number };

const ROWS: Array<{ key: keyof Props; label: string }> = [
  { key: "genre", label: "Genre" },
  { key: "artist", label: "Artists" },
  { key: "audio", label: "Sound" },
];

/** Explains *why* two users match — the 0.4/0.3/0.3 components, not just one number. */
export function ScoreBreakdown({ genre, artist, audio }: Props) {
  const values = { genre, artist, audio };
  const overall = 0.4 * genre + 0.3 * artist + 0.3 * audio;
  return (
    <div className="mt-6 rounded-xl border border-[#232d3a] bg-[#121820] p-5">
      <div className="mb-4 flex items-baseline justify-between">
        <span className="text-sm text-gray-400">Compatibility</span>
        <span className="text-2xl font-bold" style={{ color: "var(--accent)" }}>
          {(overall * 100).toFixed(0)}%
        </span>
      </div>
      {ROWS.map(({ key, label }) => (
        <div key={key} className="mb-2">
          <div className="flex justify-between text-xs text-gray-400">
            <span>{label}</span>
            <span>{(values[key] * 100).toFixed(0)}%</span>
          </div>
          <div className="mt-1 h-1.5 rounded bg-[#171f2a]">
            <div
              className="h-full rounded"
              style={{ width: `${values[key] * 100}%`, background: "var(--accent)" }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
