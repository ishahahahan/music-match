export default function ProfilePage() {
  return (
    <main className="mx-auto max-w-xl px-6 py-16">
      <h1 className="text-2xl font-bold">Your profile</h1>
      <p className="mt-3 text-gray-400">
        Phase 3 renders the auto-generated profile here: genre fingerprint, top artists, audio
        blurb — created from listening history with zero manual input via{" "}
        <code>GET /api/v1/me/profile</code>.
      </p>
    </main>
  );
}
