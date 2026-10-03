import { SyncProgress } from "@/components/SyncProgress";

export default function SyncPage() {
  return (
    <main className="mx-auto max-w-xl px-6 py-16">
      <h1 className="text-2xl font-bold">Syncing your listening history…</h1>
      <p className="mt-3 text-gray-400">
        Phase 2 wires this page to <code>GET /api/v1/sync/status</code> — a real job document
        with counts and timestamps, polled while the backend paginates Spotify.
      </p>
      <SyncProgress processed={120} total={360} />
    </main>
  );
}
