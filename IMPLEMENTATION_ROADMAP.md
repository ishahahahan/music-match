# MusicMatch — Implementation Roadmap
### From ideation to a deployed product with login, auto-profiles, and compatibility matching

**Status:** Living document · **Source of truth for:** build plan
**Companion doc:** `.freebuff/codebase-explainer.html` (visual codebase tour, Preview tab)
**Scope decision:** Web app first (Next.js), with a **mobile-ready REST API** — every product feature is reached through a versioned HTTP API that a future mobile client can consume unchanged.
**Data decision:** **NoSQL document database — MongoDB Atlas** (flexible/evolving schema, native FastAPI driver, free tier, built-in vector search for later matching) instead of SQL/Supabase. Firebase Firestore documented as the evaluated alternative (Phase 1/Phase 7). Data models are expected to keep changing, so documents over fixed tables; the legacy SQL schema stays read-only until retired.

---

## 1. Where the project is today

MusicMatch is "Hinge × Spotify": log in with Spotify, derive a music profile from listening history, and match users by a compatibility score. The repo contains three generations of work:

| Generation | What it is | State |
|---|---|---|
| Gen 1 | Jupyter notebooks (scraping, genre experiments, playlists) | Research artifacts; some orphaned (see §2, Phase 0) |
| Gen 2 | FastAPI backend (`backend.py`, 860 LOC) + `database_helper.py` (691 LOC) + `musicmatch_client.py` SDK | Functional prototype; mostly **untracked in git** |
| Gen 3 | Supabase Postgres schema (`schema.sql`, `migrations/`, 20 tables) | Schema written ahead of code; 6 tables dormant; RLS incompatible with current access pattern — **superseded by the NoSQL data-model decision above** |

**What works:** Spotify OAuth (manual, raw-token-in-JSON), profile-data sync endpoints, genre extraction pipeline (`lastfm.py`), genre-preference computation, DB persistence via Supabase.

**What is missing or broken:**

- No frontend at all — the product is unusable by an end user.
- No first-party authentication: endpoints accept `access_token` in request bodies and **query strings**; CORS is `allow_origins=["*"]` with credentials.
- Compatibility score is **capped at 0.40** — `artist_score=0.0` and `audio_score=0.0` are hardcoded in `compute_compatibility_score` (`database_helper.py:542`).
- Sync is non-paginated (`limit=50`, no paging loops), blocking (`time.sleep` in background sync), and `/api/sync/status` **fabricates** `last_synced`.
- Genre extractor is not wired into sync (manual endpoint only); blocklist regexes kill valid genres ("dancehall", "big band").
- No match/accept/reject endpoints, no chat-starter endpoints, no Blend playlist creation.
- No real test suite, no CI. `test_api.py` is a smoke script that needs a live server.
- **P0 secret leak:** real-looking Spotify `CLIENT_ID`/`CLIENT_SECRET` hardcoded in `setup.sh`.
- **P0 `.gitignore` broken:** file is UTF-16 with BOM → git cannot parse it → `.env`, `.cache`, `__pycache__`, ~700 MB datasets are not actually ignored.

The roadmap below fixes security first, then builds the vertical slice **login → auto-profile → match** phase by phase.

---

## 2. Phase 0 — Security & repository hygiene
**Goal:** A trustworthy repo to build on. **Estimate: 1–2 days.** *No phase should start before this lands.*

| # | Task | Detail | Done when |
|---|---|---|---|
| 0.1 | **Rotate Spotify credentials** | The `CLIENT_ID`/`CLIENT_SECRET` in `setup.sh` are treated as compromised. Regenerate in the Spotify Developer Dashboard, delete them from `setup.sh` help text, add `SPOTIFY_CLIENT_ID`/`SPOTIFY_CLIENT_SECRET` to a tracked `.env.example` only. | No secret string exists in any tracked file; new creds live only in `.env` (untracked) and the deployment platform. |
| 0.2 | **Fix `.gitignore`** | Rewrite as UTF-8 (currently UTF-16 BOM, unparseable). Ignore `.env`, `.cache`, `__pycache__/`, `dataset/`, `merged_tracks_features.csv`, `*.pyc`. | `git check-ignore .env` succeeds; `git status` shows no secret/cache entries. |
| 0.3 | **Commit the backend layer** | Track `backend.py`, `database_helper.py`, `musicmatch_client.py`, `test_api.py`, `setup.sh`, and the real docs; delete or rewrite stale ones (`AGENT.md` claims "no local database"; `DELIVERY_REPORT.md`, `IMPLEMENTATION_SUMMARY.md` are scaffolding noise — fold into `README.md` or remove). | Fresh `git clone` + `pip install -r requirements.txt` can start the backend. |
| 0.4 | **Lock down CORS & scopes** | Replace `allow_origins=["*"]` (with credentials) in `backend.py` with an explicit origin allowlist from env. Review `SPOTIFY_SCOPE` — drop scopes the app doesn't use. | Browser requests only succeed from the configured frontend origin. |
| 0.5 | **Archive orphans** | `xanadu.py` (unrelated), `__pycache__` remnants of deleted spiders (`songs_spider`, `genre_sprider`, …), `pdfs/` research papers → `archive/` or remove. Decide dataset fate (keep out of git; document acquisition). | Repo root contains only live project files. |

**Acceptance criteria (Phase 0):** `git status` clean of secrets/caches; CI-ready repo; credential rotation confirmed in Spotify dashboard.

---

## 3. Phase 1 — Auth & account model (login)
**Goal:** A user can log in with Spotify and get a stable MusicMatch account. **Estimate: 1 week.**

This is the foundation of "users can login" in the product requirements.

1. **Spotify OAuth 2.0 authorization-code flow with PKCE**
   - `GET /auth/login` → redirect to Spotify with `code_challenge`; `GET /auth/callback` exchanges `code` + `code_verifier` for tokens **server-side**.
   - Kill the current pattern where raw tokens are returned in JSON for the client to copy via `input()` (works only for the CLI demo).
   - Store refresh token encrypted at rest, tied to the MusicMatch user.
2. **MusicMatch identity as a user document**
   - MongoDB has no foreign keys: create `users/{spotify_id}` on first login — the latent FK violation in `create_or_update_user` (`database_helper.py:48`, upserting without `id` against `schema.sql`) **disappears with the schema**.
   - Referential data is denormalized into documents (top-artists snapshot, genre weights) instead of joins; profile updates become single-document writes — schemas can evolve field-by-field with zero migrations.
3. **Access-control strategy (must ship in this phase)**
   - All reads/writes go through the backend: driver authenticated by `MONGODB_URI` (server secret only) + our JWT middleware for per-user authorization. End users never receive DB credentials.
   - Firestore alternative path: versioned security rules in repo + Admin SDK server-side — the same JWT-middleware pattern applies either way.
4. **First-party API tokens (mobile-ready contract)**
   - `POST /api/v1/auth/token` (Spotify authorization-code flow) → short-lived **JWT access token + refresh token**.
   - All `/api/v1/**` endpoints take `Authorization: Bearer …` — never `access_token` in query strings or JSON bodies (fixes `backend.py` lines ~388, 455, 516, 565, 610, 719 and `POST /api/sync/user`).

**Acceptance criteria:** Log in from a clean browser → callback completes → `GET /api/v1/me` returns the user with no token in the URL; a `users/{spotify_id}` document exists; unauthenticated requests return 401; tokens and `MONGODB_URI` never logged.

---

## 4. Phase 2 — Sync engine correctness (listening history)
**Goal:** Complete, observable, rate-limit-safe ingestion of a user's listening history — the raw material for profiles. **Estimate: 1–1.5 weeks.**

| # | Task | Detail |
|---|---|---|
| 2.1 | **Pagination** | Every Spotify fetch (`limit=50`) loops with `offset` until exhausted (or a documented cap for free-tier users): top tracks/artists (short/medium/long term), saved tracks, saved albums, playlists. |
| 2.2 | **Real background execution** | Replace blocking `time.sleep(0.5)` in `_background_sync_all_data` (`backend.py:237`) with `asyncio.sleep` inside a proper FastAPI background task (or a queue — `arq`/Celery — if runs outgrow one process). |
| 2.3 | **Real sync status** | Persist sync jobs (`status`, `items_fetched`, `started_at`, `finished_at`, `error`) instead of fabricating `last_synced: datetime.now()` (`backend.py:293`). `GET /api/v1/sync/status` reads the job row; frontend polls it during onboarding. |
| 2.4 | **Rate-limit & retry** | Central Spotify client: honor `Retry-After` on 429, exponential backoff on 5xx, per-user serialization so two syncs don't race. |
| 2.5 | **Batch writes** | Replace the N+1 write storm (`upsert_track` + `upsert_track_artists`, `database_helper.py:135`, `:203`) with MongoDB `bulkWrite` upserts (one ordered batch per page of results; respect batch size limits). Replace delete-then-insert with a replace-one/transaction so a crash can't leave empty playlist mirrors. |
| 2.6 | **Idempotency** | Re-running a sync must produce identical data (natural-key upserts, `updated_at` bumps). |
| 2.7 | **Genre extraction in the loop** | Run `GenreExtractor.extract_genres` (`lastfm.py:27`) on synced artists during sync — not only via the manual `POST /api/genres/extract`. Fix the over-aggressive regex blocklist (`.*dance.*` kills "dancehall", `.*live.*` kills "big band"): anchor patterns to word boundaries and drop/adjust the ~60 patterns that match real genres. |

**Acceptance criteria:** A user with 2,000+ saved tracks syncs to 100% with zero data loss vs. the Spotify API; status endpoint reports genuine progress; two concurrent syncs don't duplicate rows; re-sync is a no-op diff; genres populated for all synced artists.

---

## 5. Phase 3 — Auto-profile & compatibility scoring
**Goal:** "Create a profile (or make one for them)" and a **real** compatibility score. **Estimate: 1–1.5 weeks.**

### 5.1 Auto-generated profile

Built from listening history, no user input required:

- **Genre fingerprint** — the weighted genre vector from `compute_user_genre_preferences` (`database_helper.py:336`, weight `w=(N−p+1)/N` per artist rank).
- **Top artists / top tracks / eras** — from the three time windows.
- **Audio-feature fingerprint** — mean/std of the 9 persisted `track_audio_features` fields (energy, valence, danceability, tempo…) → "your sound: high-energy, upbeat, dance-leaning".
- **Music personality blurb** — deterministic template text over the above (v1; LLM polish optional later).
- **Profile controls** — visibility (discoverable / hidden), and a "looking for" preference (later: `user_preferences`, currently dormant — wire or drop in this phase).

Exposes `GET /api/v1/me/profile` and public `GET /api/v1/users/{id}` (respecting visibility).

### 5.2 Compatibility score — remove the 0.40 cap

`compute_compatibility_score` (`database_helper.py:522`) today orders the two UUIDs (satisfying the `user1_id < user2_id` constraint), calls RPC `compute_genre_overlap`, and weights **0.4 genre / 0.3 artist / 0.3 audio** — but `artist_score = 0.0` and `audio_score = 0.0` are hardcoded, so no pair can exceed **0.40**.

Implement the two missing components:

- **Artist score (0.3):** weighted Jaccard over top-200 artists — `Σ min(w_a, w_b) / Σ max(w_a, w_b)` using rank-based weights (captures popularity-aware overlap, not just set intersection).
- **Audio score (0.3):** cosine similarity between the two users' normalized audio-feature centroids (z-score per feature across the user population, or min-max to [0,1], before cosine).
- **Overall:** `0.4·genre + 0.3·artist + 0.3·audio ∈ [0,1]`, persisted to `compatibility_scores` with the **component breakdown** so the UI can explain *why* two users match ("92% genre, 71% artists, 64% sound").
- Scoring runs in **application code** — no SQL RPCs: compute genre/artist/audio components in the batch job and persist the score document with its breakdown; key pairs by ordered IDs (min–max) so one document exists per pair.
- The legacy SQL leftovers (`user_audio_preferences`, `user_saved_albums`, `user_preferences`) are decided per access pattern: embed as fields on the user document (audio centroid lives on the profile) or as subcollections — no `CREATE TABLE` needed when the model changes.

**Acceptance criteria:** Controlled fixtures verify all three components: two identical histories → score ≥ 0.95; disjoint histories → ≤ 0.1; a pure-genre-only fixture shows the 0.40 cap **disappearing**. Profile endpoint renders a complete profile with zero user input.

---

## 6. Phase 4 — Matching product surface (match users)
**Goal:** Users see and act on matches. **Estimate: 1 week.**

1. **Candidate discovery**
   - v1: pairwise scoring for the user cohort (batch job nightly + on-demand for new users; fine up to ~10k users).
   - v2 threshold: precompute embeddings of the profile vector, switch to vector similarity (MongoDB Atlas Vector Search — or Firestore + Vertex AI Vector Search on the Firebase path) when pairwise grows O(n²).
2. **Endpoints**
   - `GET /api/v1/matches` — ranked list with score + breakdown + each person's headline (top genre, top artist).
   - `POST /api/v1/matches/{user_id}/accept` · `/reject` — wire the matches model: `users/{id}/swipes` subcollection + `matches/{pair_id}` document (states: `pending → liked/matched → passed`); mutual accept = **match**.
   - `GET /api/v1/matches/{user_id}/chat-starters` — surface the existing `generate_chat_starters()` SQL function (dormant) through an endpoint; generate prompts from shared artists/genres.
   - `DELETE /api/v1/matches/{user_id}` — unmatch.
3. **Blend playlist creation** — the differentiator: for a matched pair, create a **collaborative blend playlist** via the Spotify Web API (create playlist → add tracks ranked by shared taste: union of both users' top tracks, re-ranked by the pairwise score components). Store `blend_playlist_id` on the match document.
4. **Feed ordering & freshness** — recompute scores incrementally when either user re-syncs (invalidate that user's score rows).

**Acceptance criteria:** Two test accounts with known-overlap histories see each other in ranked matches, accept → mutual match appears, chat starters reference a genuinely shared artist, and one tap creates a real playlist visible in both users' Spotify accounts.

---

## 7. Phase 5 — API contract hardening (mobile-ready)
**Goal:** One stable, documented API for web now and mobile later. **Estimate: 3–5 days** (overlaps Phase 4).

- **Version & envelope:** all product endpoints under `/api/v1`; uniform `APIResponse` shape; **fix `APIResponse.timestamp = datetime.now().isoformat()` evaluated once at import** (`backend.py:119`) → compute per response.
- **Pagination contract:** cursor/limit on list endpoints (`matches`, `tracks`, `playlists`).
- **Errors:** consistent JSON error model + proper HTTP codes; remove `print` logging → structured `logging` with request IDs; never log tokens.
- **Validation:** `Query(regex=…)` is deprecated → `pattern=` (`backend.py:360`, 427, 637); fail fast with 422 + field messages.
- **OpenAPI:** FastAPI `/docs` is the contract; publish the generated OpenAPI JSON to the repo (`openapi.json`) so a mobile client can codegen against it. Document the auth flow (PKCE + Bearer) for third-party/mobile clients.
- **CORS for SPA:** explicit origins + credentials, allow `Authorization` header.

**Acceptance criteria:** A stranger can build a minimal client from `openapi.json` alone; every endpoint authenticated by Bearer token; no token appears in any URL, body, or log line.

---

## 8. Phase 6 — Web frontend
**Goal:** A real user can complete login → profile → match. **Estimate: 2–3 weeks.**

**Stack:** Next.js (App Router) + TypeScript + Tailwind; hosted on Vercel; talks only to `/api/v1`.

**Screens (vertical slice):**

| Route | Purpose |
|---|---|
| `/` | Landing → "Log in with Spotify" (starts PKCE flow) |
| `/onboarding/sync` | Live sync progress polling `/sync/status` (real job data from 2.3) |
| `/profile` | Auto-generated profile: genre fingerprint, top artists, audio-blurb, edit visibility |
| `/matches` | Ranked candidates with score breakdown bars (genre/artist/audio) |
| `/matches/[id]` | Match detail: shared-taste highlights, chat starters, **Make Blend playlist** button |
| `/settings` | Re-sync, visibility, disconnect Spotify |

**UX requirements:** profile is usable *before* the user writes anything (auto-profile); score breakdown shown, not just a number; loading/empty/error states for sync; mobile-responsive (it's also the mobile web experience).

**Acceptance criteria:** Cold user with zero prior account completes login → watches real sync progress → sees a full profile → matches → creates a Blend playlist, on a fresh browser, with no manual token pasting.

---

## 9. Phase 7 — Deployment
**Goal:** The product is live. **Estimate: 3–5 days** (can start after Phase 1).

| Piece | Target | Notes |
|---|---|---|
| Backend | Docker image → Render / Fly.io / Railway | `uvicorn backend:app`; healthcheck `/health` |
| Database | **MongoDB Atlas** (free M0 → paid tiers; alt: Firebase Firestore) | `MONGODB_URI` in platform secrets only; collections created on first write (schema-less); index definitions via `migrate-mongo`; Firestore path: Firebase project + security rules in repo |
| Frontend | Vercel | `NEXT_PUBLIC_API_URL` env |
| Spotify redirect URIs | Dashboard: prod + local | Exact-match URIs registered |
| Secrets | Platform env vars only | `.env.example` tracked; `.env` never |
| Environments | `staging` + `prod` | Staging DB separate; smoke tests against staging |

Also: application log aggregation, error alerting (Sentry or platform-native), basic uptime check, database backups enabled.

**Acceptance criteria:** A stranger can open the prod URL, log in with Spotify, and complete the Phase 6 flow end-to-end; no secret in the repo or in client bundles (grep the built assets); rollback = redeploy previous image.

---

## 10. Phase 8 — Testing & CI (runs continuously from Phase 1)
**Goal:** Refactor without fear. **Estimate: ongoing, ~1 day to bootstrap.**

- **Unit tests (pytest):**
  - Genre extraction: fixture artists → expected genres; blocklist regression tests ("dancehall", "big band" survive).
  - Compatibility: identical/disjoint/mixed fixtures for each component; assert the 0.40 cap is gone; UUID-swap invariance of the ordering constraint.
  - Profile derivation from a fixed listening-history fixture.
  - Sync pagination & idempotency against a mocked Spotify client.
- **Integration (opt-in):** convert `test_api.py` into pytest markers (`@pytest.mark.integration`) that run only when a server + credentials are present.
- **GitHub Actions:** on PR → `black --check`, `flake8`, `pytest`, (later) `npm run build`. Cache deps; secrets from GitHub Environments.
- **No network in default tests:** Spotify and the database (MongoDB, via an in-memory/mock repository) fully mocked so CI is deterministic.

**Acceptance criteria:** `pytest` green locally and in CI with no external services; a PR that breaks the score math or blocklist fails CI.

---

## 11. Sequencing & timeline (solo dev, part-time ≈ evenings)

```
Week 0        Phase 0  security & hygiene
Week 1        Phase 1  auth (login)                ─┐
Week 2–3      Phase 2  sync correctness             ├─ core backend
Week 3–4      Phase 3  profile + scoring            ─┘
Week 4        Phase 5  API hardening (interleaved)
Week 5        Phase 4  matches, chat starters, Blend
Week 6–8      Phase 6  web frontend
Week 8        Phase 7  deployment
Week 8+       Phase 8  CI/tests (bootstrapped week 1, enforced throughout)
```

**Critical path:** Phase 0 → 1 → 2 → 3 → 4 → 6 → 7. Phases 5 and 8 interleave. Fastest MVP-to-prod path (login + profile + matches, quality bar on scoring/tests): **~8 weeks**.

**First demo milestone ("walking skeleton"):** end of Week 2 — one user logs in and their sync progress is real, even before matching exists.

---

## 12. Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| Leaked Spotify secret already abused | High | **Rotate first (0.1)**; audit dashboard usage after rotation |
| Broken `.gitignore` may have committed secrets/datasets | High | History scan (`git log -p` for secrets); rewrite history only if confirmed; datasets kept out of git going forward |
| Access-control gap: leaked DB creds or over-permissive rules | High | Phase 1 backend-only access decision (JWT middleware) before writing more DB code; no client-side DB access in MVP |
| NoSQL vendor lock-in (Firebase/MongoDB) | Medium | Thin repository layer over the driver; self-contained documents keep export/migration feasible |
| Spotify rate limits during sync | Medium | Backoff, per-user serialization, incremental syncs |
| Pairwise matching O(n²) at scale | Medium | Batch precompute now; vector-index design note (Atlas Vector Search) for v2 |
| Scope creep (chat, social feed) | Medium | Chat starters only in MVP; real chat is post-MVP |
| Spotify API/ToS changes (static dataset from 2019 is stale) | Medium | All features from live API, not static CSVs; pin API version |

---

## 13. Definition of Done (final product)

- [ ] User logs in with Spotify on web; account persists across sessions; no tokens in URLs/logs/repo.
- [ ] A profile is **auto-created from listening history** the first time they log in, and renders without any manual input.
- [ ] Compatibility scores are computed across **all three** components (genre/artist/audio), are honest in [0,1], and show a per-component breakdown.
- [ ] Users browse ranked matches, accept/reject, see chat starters on mutual match, and can create a Blend playlist in Spotify.
- [ ] Versioned `/api/v1` documented via OpenAPI — a mobile client can be built with zero backend changes.
- [ ] Deployed at a public URL with staging + prod, CI enforcing lint/tests, and a green test suite that runs without external services.
