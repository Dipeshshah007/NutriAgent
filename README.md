# 🥗 NutriAgent — AI-Powered Personalized Nutrition & Meal Planning System

A full-stack, white-label platform that turns a person's body, goal, diet and allergies into **calorie/macro targets → ML recommendations → an optimised weekly meal plan → a shopping cart → checkout → daily tracking → an AI coach**. Includes customer and admin portals.

**Stack (100 % free tools):** React 18 + Vite + Recharts · FastAPI · SQLAlchemy 2 · SQLite / PostgreSQL · scikit-learn + NumPy · optional Google Gemini free tier · JWT + bcrypt

| Catalog | AI meal planner |
|---|---|
| ![catalog](docs/screenshots/02_catalog.png) | ![planner](docs/screenshots/06_planner.png) |
| **Diet tracker** | **Admin dashboard** |
| ![tracker](docs/screenshots/07_tracker.png) | ![admin](docs/screenshots/10_admin_dash.png) |

📄 Full write-up (problem, solution, users, scalability, cost, FR/NFR): **[docs/PROJECT_REPORT.md](docs/PROJECT_REPORT.md)**

---

## 1. Architecture

![architecture](docs/architecture.png)

Editable sources: `docs/architecture.mmd`, `docs/erd.mmd` (Mermaid — preview in VS Code with the *Markdown Preview Mermaid Support* extension). Database ER diagram: `docs/erd.png`.

```
nutriagent/
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI app, CORS, serves built frontend
│   │   ├── config.py          env-driven settings (white-label, store rules)
│   │   ├── models.py          SQLAlchemy tables
│   │   ├── schemas.py         Pydantic request/response models
│   │   ├── security.py / deps.py   bcrypt, JWT, RBAC dependencies
│   │   ├── seed.py            admin + demo user + 46-item catalog + demo history
│   │   ├── routers/           auth, catalog, cart, orders, profile, tracker, planner, chat, admin
│   │   └── ml/
│   │       ├── nutrition.py   BMR / TDEE / macro targets, diet & allergen rules
│   │       ├── recommender.py content-based cosine-similarity recommender
│   │       ├── planner.py     constrained meal-plan optimiser
│   │       └── coach.py       Gemini (free) + offline fallback coach
│   └── tests/test_api.py      11 automated tests
├── frontend/src/              React pages, components, context, styles
├── docs/                      report, diagrams, screenshots
├── Dockerfile · docker-compose.yml
```

---

## 2. Prerequisites (all free)

| Tool | Version | Check |
|---|---|---|
| VS Code | any | — |
| Python | 3.10 or newer (built & tested on 3.13) | `python --version` |
| Node.js | 18 or newer (tested on 22) | `node --version` |
| Git | any | `git --version` |

Recommended VS Code extensions (VS Code will offer them automatically from `.vscode/extensions.json`): Python, Prettier, REST Client, SQLite Viewer, Markdown Preview Mermaid Support.

---

## 3. Run it — step by step

Open the `nutriagent` folder in VS Code (**File → Open Folder**), then open the integrated terminal (**Ctrl + `**).

### Step 1 — Backend (terminal 1)

**Windows (PowerShell):**
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1        # if blocked:  Set-ExecutionPolicy -Scope Process Bypass
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

**macOS / Linux:**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

On first start the database is created and seeded automatically. Check <http://localhost:8000/api/health> → `{"status":"ok"}` and the interactive API docs at <http://localhost:8000/docs>.

> If `pip install` fails on `psycopg2-binary` (only needed for PostgreSQL), delete that line from `requirements.txt` and re-run.

### Step 2 — Frontend (terminal 2)

```bash
cd frontend
npm install
npm run dev
```

Open **<http://localhost:5173>**. (Vite proxies `/api` to port 8000.)

### Step 3 — Log in

| Role | URL | Email | Password |
|---|---|---|---|
| Customer (pre-filled history) | `/login` | `demo@nutriagent.dev` | `Demo@123` |
| Admin | `/admin/login` | `admin@nutriagent.dev` | `Admin@123` |
| New customer | `/register` | your own | — |

> Change the seeded passwords and `SECRET_KEY` in `backend/.env` before deploying anywhere public. Seed accounts are only created if they don't exist, so delete `backend/nutriagent.db` to re-seed.

### Step 4 — Walk through the app (this is also your demo script)

1. **Profile** → set age/weight/goal/diet/allergies → targets update instantly.
2. **Shop** → filter by diet, exclude allergens, sort by protein → open a product → **Add to cart**.
3. Home page → **Recommended for you** (cosine-similarity ranking with reasons).
4. **Meal Planner** → *Generate plan* → check the day-vs-target bars → **Add whole plan to cart**.
5. **Cart → Checkout** → address, payment (card `4242 4242 4242 4242` – demo only) → **Place order** → **Orders**.
6. **Tracker** → log a meal, add weight, watch the charts. **AI Coach** → ask "What should I eat for dinner?".
7. Log out → **Admin login** → Dashboard, Products (create/edit/hide), Orders (change status; *cancelled* restocks), Users.

### Optional — single-server "production" mode

```bash
cd frontend && npm run build          # creates frontend/dist
cd ../backend && uvicorn app.main:app --port 8000
```
FastAPI now serves the React app and the API together at <http://localhost:8000>.

### Optional — free AI coach with Gemini

1. Create a free key at <https://aistudio.google.com/apikey>.
2. Put it in `backend/.env`: `GEMINI_API_KEY=...` (model name is `GEMINI_MODEL`; if Google retires the default, set a current one from their docs).
3. Restart the backend. The Coach page badge changes from `offline-coach` to `gemini`. Any error silently falls back to the offline coach.

### Optional — PostgreSQL / Docker

```bash
docker compose up --build        # app on http://localhost:8000, Postgres included
```
Or set `DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/db` in `.env`.
*(The Docker files and the PostgreSQL path were not executed in the environment this project was built in — SQLite + the full test suite and a browser walkthrough were. Expect to do a quick first-run check.)*

### Run the tests

```bash
cd backend
pytest -q          # 11 tests: auth, RBAC, catalog filters, nutrition math, recommender safety, plans for 6 diets, cart→checkout, admin CRUD, coach
```

---

## 4. Re-use it for *any* nutrition / meal / diet platform

Nothing is hard-wired to one business:

* **Rebrand:** `APP_NAME`, `APP_TAGLINE`, `CURRENCY_SYMBOL`, tax/shipping in `.env`.
* **New catalog:** items are generic (`kind`: meal · snack · ingredient · supplement · drink; per-serving macros; tags; allergens). Replace the list in `backend/app/seed.py` or use the Admin panel.
* **Use cases:** meal-delivery store · supplement shop · grocery planner · gym/corporate wellness · cafeteria or hospital diet monitoring (hide the store pages, keep tracker + planner).
* **New diets:** add the tag to products and a rule in `ml/nutrition.py::diet_compatible`.

## 5. API overview (`/docs` has the full interactive spec)

| Area | Endpoints |
|---|---|
| Auth | `POST /api/auth/register · login · admin-login`, `GET /api/auth/me` |
| Catalog | `GET /api/products` (q, category, diet, exclude_allergens, max_calories, min_protein, sort, page), `/products/{id}`, `/products/recommended`, `/categories` |
| Cart | `GET/POST /api/cart`, `PUT/DELETE /api/cart/{product_id}` |
| Orders | `POST /api/orders` (checkout), `GET /api/orders` |
| Profile | `GET/PUT /api/profile` (returns computed targets) |
| Tracker | `POST/GET /api/tracker/logs`, `GET /api/tracker/summary`, `POST /api/tracker/weight` |
| Planner | `POST /api/planner/generate`, `GET /latest`, `POST /{id}/add-to-cart` |
| Coach | `POST /api/chat` |
| Admin | `/api/admin/stats · products · orders · users` |

## 6. How the ML works (interview-ready summary)

* **Targets:** Mifflin-St Jeor BMR × activity factor, ±goal adjustment, protein g/kg, remaining split to fat/carbs.
* **Recommender:** content-based. Item vector = [macro energy shares, calorie density, fibre density, tag one-hots, kind one-hots]. User vector = 0.7·(ideal profile from targets/goal/diet) + 0.3·(centroid of past purchases/logs). Rank by cosine similarity after hard diet/allergen filters — a safety constraint, never a soft score.
* **Planner:** per slot, top-K candidates with best serving size (0.25 steps) → exhaustive search over slot combinations minimising weighted squared error to calorie/protein/carb/fat targets + variety penalty.
* **Coach:** retrieval-grounded prompting — the LLM only receives structured facts our engine computed, with an offline rule-based fallback.
* **Known limitations:** small hand-curated catalog, nutrition values are approximate demo data, no collaborative filtering yet (needs real usage data), not a medical product.

## 7. Put it on GitHub (when you're ready)

```bash
git init
git add .
git commit -m "feat: NutriAgent - AI-powered personalized nutrition & meal planning"
git branch -M main
git remote add origin https://github.com/<your-username>/nutriagent.git
git push -u origin main
```
Create the empty repo first at <https://github.com/new>. Then: add topics (`fastapi`, `react`, `machine-learning`, `recommender-system`, `nutrition`, `full-stack`), pin the repo, and record a 60–90 s screen capture of the demo script above for the README.

**Resume bullets (all verifiable from this repo):**
* Built a full-stack AI nutrition platform (React, FastAPI, SQLAlchemy, PostgreSQL/SQLite) with JWT auth, role-based admin portal, catalog, cart, and transactional checkout with inventory control.
* Implemented a content-based recommender (cosine similarity over macro/tag feature vectors with implicit-feedback blending) and a constrained meal-plan optimiser that fits daily calorie/macro targets while enforcing diet and allergen constraints.
* Integrated a grounded LLM coach (Gemini free tier) with deterministic offline fallback; wrote 11 automated API tests and documented architecture, scalability path and FR/NFR.

## Disclaimer

Educational/portfolio project. Nutrition output is general wellness guidance, **not medical advice**. Payments are simulated.

## License

MIT
