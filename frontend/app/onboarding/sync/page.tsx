export default function SyncPage() {
  return (
    <main className="mx-auto max-w-xl px-6 py-16">
      <h1 className="text-2xl font-bold">Syncing your listening history…</h1>
      <p className="mt-3 text-gray-400">
        Phase 2 wires this page to <code>GET /api/v1/sync/status</code> — a real job document
        with counts and timestamps, polled while the backend paginates Spotify.
      </p>
      <div className="mt-6 h-2 w-full overflow-hidden rounded bg-[#171f2a]">
        <div className="h-full w-1/3" style={{ background: "var(--accent)" }} />
      </div>
    </main>
  );
}
