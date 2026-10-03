import { ScoreBreakdown } from "@/components/ScoreBreakdown";

export default async function MatchDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <main className="mx-auto max-w-xl px-6 py-16">
      <h1 className="text-2xl font-bold">Match {decodeURIComponent(id)}</h1>
      <p className="mt-3 text-gray-400">
        Phase 4 fills this with shared-taste highlights, chat starters, and the Blend playlist
        button. The score breakdown renders like this:
      </p>
      <ScoreBreakdown genre={0.92} artist={0.71} audio={0.64} />
    </main>
  );
}
