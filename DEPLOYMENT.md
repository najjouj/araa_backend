# Deploying PyLearn — a working, live website

This walks through taking the Phase 5 frontend (`pylearn/`) and the backend
you now have (`pylearn-backend/`) from your machine to a real URL, using
Vercel (frontend) + Railway (backend, Postgres, and the sandbox). Render
is a fine substitute for Railway throughout if you prefer it — the steps
are nearly identical.

Rough total time: 30-45 minutes the first time.

---

## 0. Prerequisites

- A GitHub account (both projects need to live in a repo each service can pull from)
- A [Vercel](https://vercel.com) account (free tier is fine to start)
- A [Railway](https://railway.app) account (free trial credit is fine to start)

---

## 1. Push both projects to GitHub

```bash
cd pylearn
git init && git add . && git commit -m "Phase 5 frontend"
gh repo create pylearn-frontend --public --source=. --push
```

```bash
cd ../pylearn-backend
git init && git add . && git commit -m "Phase 5/6 backend"
gh repo create pylearn-backend --public --source=. --push
```

(No `gh` CLI? Create the two repos on github.com and follow the "push an
existing repository" instructions it shows you.)

---

## 2. Deploy Postgres on Railway

1. railway.app → **New Project** → **Provision PostgreSQL**.
2. Once it's up, open the Postgres service → **Variables** tab → copy the
   `DATABASE_URL` value. You'll paste this into the backend service next.

---

## 3. Deploy the backend on Railway

1. In the same Railway project: **New** → **GitHub Repo** → select `pylearn-backend`.
2. Railway detects the `Dockerfile` automatically and builds from it.
3. Open the new service → **Variables** tab, add:
   - `DATABASE_URL` → paste the value from Step 2
   - `CORS_ORIGINS` → leave as `http://localhost:3000` for now; you'll add
     the real Vercel URL in Step 6
   - `PISTON_URL` → the URL of the Piston service from Step 4 below
   - `JWT_SECRET` → any long random string
4. **Settings** tab → **Networking** → **Generate Domain**. This gives you
   a public URL like `pylearn-backend-production.up.railway.app` — that's
   your live API.
5. Once deployed, open a terminal to the service (Railway's "Shell" feature,
   or run locally against the same `DATABASE_URL`) and run:
   ```bash
   python -m app.seed
   ```
   This populates the demo `lists-intro` lesson so the frontend has
   something real to submit code against.

---

## 4. Deploy the Piston sandbox as its own service

Piston needs privileged container access to create its execution sandboxes,
which most PaaS free tiers restrict — so the most reliable path for an MVP
is a small dedicated VM rather than Railway/Render directly:

1. Spin up the cheapest VM on any provider (DigitalOcean, Hetzner, a free-tier
   GCP/AWS instance all work) with Docker installed.
2. On that VM:
   ```bash
   docker run -d --privileged -p 2000:2000 --name piston ghcr.io/engineer-man/piston
   ```
3. Put a reverse proxy with HTTPS in front of it (Caddy is the simplest —
   two lines of config auto-provisions a Let's Encrypt certificate) so the
   URL is `https://your-sandbox-domain.com/api/v2` rather than raw HTTP.
4. Use that HTTPS URL as `PISTON_URL` in Step 3.

This is the one piece of the stack that's a genuine server to manage rather
than a fully managed platform — a fair trade for not having to build and
secure container isolation yourself. If this step feels like too much
right now, you can temporarily point `PISTON_URL` at a public Piston
instance to keep moving, and swap it for your own once this step is done —
just don't leave student code running against someone else's public
infrastructure long-term.

---

## 5. Deploy the frontend on Vercel

1. vercel.com → **Add New Project** → import `pylearn-frontend` from GitHub.
2. Vercel auto-detects Next.js — no config changes needed.
3. Before the first deploy, add an environment variable:
   - `NEXT_PUBLIC_API_URL` → the Railway backend URL from Step 3
     (e.g. `https://pylearn-backend-production.up.railway.app`)
4. Deploy. You'll get a URL like `pylearn-frontend.vercel.app` — that's
   your live site.

> Note: the Phase 5 scaffold's `CodeExercisePane` currently calls a
> relative `/api/exercises/...` path. Before this step, update that one
> `fetch` call in `src/components/lesson/CodeExercisePane.tsx` to use
> `${process.env.NEXT_PUBLIC_API_URL}/api/exercises/...` so it reaches the
> Railway backend instead of the (nonexistent) same-origin route. This is a
> one-line change — happy to make it directly in the scaffold if you'd like.

---

## 6. Connect the two

Go back to Railway → backend service → **Variables** → update
`CORS_ORIGINS` to your real Vercel URL:

```
CORS_ORIGINS=https://pylearn-frontend.vercel.app
```

Redeploy the backend (Railway does this automatically on variable changes).

---

## 7. Verify

Visit `https://pylearn-frontend.vercel.app/en/roadmap/beginner/lists/lists-intro`.
Run the starter code as-is (it already produces the right answer), and you
should see "1 of 1 tests passing" — confirming the full chain: Vercel →
Railway API → Postgres + Piston sandbox → back to the browser.

---

## What's still missing for a real launch

- **Custom domain** — both Vercel and Railway support adding your own
  domain under their respective "Domains" settings; a five-minute step
  once you own one.
- **Auth** — no login flow exists yet; the `User` model is defined but
  nothing issues sessions/JWTs yet.
- **The other 13 lesson-step types, dashboards, teacher views** — same
  component and route patterns as what's here now.
- **HTTPS certificate renewal** on the Piston VM — Caddy handles this
  automatically, just don't swap it for a config that disables it.
