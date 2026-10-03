const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center gap-6 px-6 text-center">
      <h1 className="text-4xl font-bold tracking-tight">
        Music<span style={{ color: "var(--accent)" }}>Match</span>
      </h1>
      <p className="text-gray-400">
        Log in with Spotify, get a profile built from your listening history, and see who you
        actually match.
      </p>
      <a
        href={`${API_URL}/api/v1/auth/login`}
        className="rounded-full px-8 py-3 font-semibold text-black"
        style={{ background: "var(--accent)" }}
      >
        Log in with Spotify
      </a>
      <p className="text-xs text-gray-500">
        Backend health: <a href={`${API_URL}/api/v1/health`}>{API_URL}/api/v1/health</a>
      </p>
    </main>
  );
}
