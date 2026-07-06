# GoDoc — Consultation Booking System

A simplified end-to-end consultation booking flow: a patient views a doctor's open
slots and books one, with **correct behaviour under concurrent booking attempts** as the
central design goal. Built for the GoDoc take-home (Scope 1).

- **Frontend:** Vue 3 + Vite + TypeScript (single-page app)
- **Backend:** FastAPI (Python), thin service layer
- **Database:** Supabase (Postgres), accessed via `supabase-py`

```
Vue 3 SPA  ──HTTP/JSON──▶  FastAPI  ──supabase-py──▶  Supabase Postgres
 pick patient/doctor,       routes + booking          schema is the source of
 book / cancel slots        service + state machine    truth for correctness
```

The frontend never talks to Supabase directly — all data flows through the API, so the
database key stays server-side and the backend is the single place business rules live.

---

## Tech stack justification & trade-offs

| Choice | Why | Trade-off considered |
|---|---|---|
| **Postgres (Supabase)** | The whole problem is *correctness under concurrency*. A relational DB with transactions and unique constraints solves double-booking declaratively. Supabase gives managed Postgres with zero setup. | A document store would push concurrency control into app code. Not worth it. |
| **Partial unique index for correctness** | Double-booking is prevented by the database itself, not by application locks (see below). Simple, provably correct, scales horizontally. | Alternatives (`SELECT FOR UPDATE`, advisory locks, an RPC function) are heavier and hold locks; the index is declarative and lock-free. |
| **FastAPI (thin backend)** | Owns validation and the booking **state machine** in one authoritative, testable place; keeps DB access off the client; is the natural seam for future features (accounts, offboarding, HRM sync). | We could let Vue hit Supabase directly. Rejected: it exposes the DB to the browser and scatters business rules into SQL/RLS. The backend is kept deliberately thin to avoid over-engineering. |
| **supabase-py client** | Uses the provided publishable key, minimal setup, and the correctness guarantee lives in the schema — so a full ORM + direct connection buys little here. | SQLAlchemy + a direct connection would give richer transaction control, but we don't need it once correctness is a DB constraint. |
| **Vue 3 + Vite (SPA)** | Lightweight, fast, and pairs cleanly with a separate API. The UI is small (pick doctor → pick slot → manage bookings). | Next.js/Nuxt would add SSR and server routes that overlap with the Python backend — redundant for this scope. |

---

## The headline: preventing double-booking

**The race:** two patients try to book the same slot at the same instant. A naive
"check if free, then insert" has a gap between the check and the insert where both requests
see the slot as free and both write.

**The design:** slot availability is *derived*, not a mutable flag, and correctness is a
**partial unique index** on the database:

```sql
create unique index one_active_booking_per_slot
  on bookings (slot_id)
  where status in ('pending', 'confirmed');
```

Booking is therefore a single atomic `INSERT`. When two inserts race for the same slot,
Postgres serializes them on the index: **exactly one commits**; the other raises
`23505` (unique violation), which the backend catches and returns as **HTTP 409 Conflict**.

Why this is the right shape:
- **No application locks.** No `SELECT FOR UPDATE`, no advisory locks, no coordination
  between backend instances. The database is the single source of truth, so the API layer
  stays stateless and scales horizontally — N backend replicas remain correct.
- **Immune to app bugs.** Even if the service logic were wrong, the constraint makes a
  double-booking physically impossible.
- **Rebooking still works.** The index only covers *active* statuses, so once a booking is
  `cancelled` the slot is free again (verified by tests).

This is proven by an automated test that fires N concurrent bookings at one slot and asserts
exactly one success + N−1 conflicts (`backend/tests/test_concurrency.py`).

**Alternatives considered:** `SELECT ... FOR UPDATE` (classic, but holds a row lock and needs
direct-transaction control); a plpgsql `book_slot()` RPC (correct, but more moving parts).
The partial unique index gives the same guarantee with the least machinery.

---

## Booking state machine

States: `pending`, `confirmed`, `cancelled`, `completed`. Transitions are enforced in one
place (`backend/app/state_machine.py`):

```
confirmed ──cancel──▶ cancelled        (terminal)
confirmed ──complete─▶ completed        (terminal)
pending   ──confirm──▶ confirmed        (modeled, not exercised — see assumptions)
pending   ──cancel───▶ cancelled
```

Bookings are created directly as `confirmed`. `pending` exists in the schema and transition
table for a future payment/hold flow but is never entered in this build. Transitions are
applied with a compare-and-swap (`update ... where status = <current>`) so a concurrent
status change conflicts rather than silently overwrites.

---

## Data model

```
doctors  (id, name, specialty)
patients (id, name, email)
slots    (id, doctor_id → doctors, start_time, end_time)   -- check end_time > start_time
bookings (id, slot_id → slots, patient_id → patients, status, created_at, updated_at)
```

- A **slot is available** when no active (`pending`/`confirmed`) booking references it —
  availability is derived, never a stored flag that could drift.
- `updated_at` is maintained by a DB trigger (`moddatetime`).
- Full schema and seed data: [`db/001_schema.sql`](db/001_schema.sql),
  [`db/002_seed.sql`](db/002_seed.sql).

---

## API reference

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/doctors` | List doctors |
| `GET` | `/doctors/{id}/slots` | Available slots for a doctor |
| `GET` | `/patients` | List patients (stands in for login) |
| `GET` | `/patients/{id}/bookings` | A patient's bookings (with slot + doctor) |
| `POST` | `/bookings` | Book a slot `{slot_id, patient_id}` → `201`, or `409` if taken |
| `POST` | `/bookings/{id}/cancel` | `confirmed → cancelled` |
| `POST` | `/bookings/{id}/complete` | `confirmed → completed` |
| `GET` | `/health` | Liveness |

Error codes: `404` (unknown slot/patient/booking), `409` (slot already booked, or invalid
state transition), `422` (request body validation).

Interactive docs at `http://127.0.0.1:8000/docs` when the backend is running.

---

## Setup & run locally

Prerequisites: Python 3.11+, Node 18+. The Supabase project is already provisioned and its
credentials are committed in `backend/.env` and `frontend/.env` (per the assessment's
instruction to commit the env vars — see the note under Limitations).

### 1. Database (already applied; re-run only to reset)

The schema and seed have been applied to the linked Supabase project. To recreate from
scratch, run [`db/001_schema.sql`](db/001_schema.sql) then [`db/002_seed.sql`](db/002_seed.sql)
in the Supabase SQL editor.

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate      # Windows Git Bash;  use .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

If port 8000 is taken, use another port and update `VITE_API_BASE_URL` in `frontend/.env`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the printed URL (default `http://localhost:5173`). Use the **Booking as** switcher to
act as different patients.

### Run tests

```bash
cd backend
pytest
```

Nine tests: the concurrency race (`test_concurrency.py`), state-machine transitions
(`test_state_machine.py`), and booking/availability behaviour (`test_bookings.py`). Tests run
against the real Supabase project (the race test is only meaningful against real Postgres) and
clean up after themselves.

---

## Assumptions & known limitations

- **No authentication.** A patient is chosen from a dropdown instead of logging in, to keep
  focus on the booking mechanics. In production the `patient_id` would come from an auth token.
- **RLS is disabled** on the tables, so the publishable key can read/write directly. This is
  acceptable for a seeded demo but is **not production-safe** — production would enable Row
  Level Security with policies, and the backend would use a server-side service key. The env
  var is committed only because the assessment explicitly asks for it.
- **`pending` / holds not exercised.** Bookings go straight to `confirmed`. A real flow would
  create a `pending` hold, confirm after payment, and auto-expire abandoned holds (an
  `expires_at` + sweep job) — the schema and state machine already accommodate this.
- **Slot times are shown in UTC** so the demo always displays the seeded clinic hours
  (09:00–16:00) regardless of the viewer's timezone.
- **Transient transport errors aren't retried.** `supabase-py` uses a single shared HTTP/2
  connection; a large concurrent burst over one connection can occasionally drop. This never
  affects correctness (the DB constraint still guarantees one winner). Production hardening
  would add retries and **idempotency keys** so a booking that succeeded at the DB but failed
  in transit isn't misreported.
- **Availability is computed in app code** (slots minus active bookings). At larger scale this
  would move to a DB view or a single joined query.

---

## Out of scope / what I'd build next

- **Deployment** (bonus) — the app is deploy-ready (stateless API + static SPA); not deployed
  to keep the submission focused.
- **Scope 2 (documents)** and **Scope 3 (corporate accounts)** — not built. The backend's
  layered structure (routes → service → DB) is where these would slot in: corporate accounts
  as a self-referencing `parent_account_id` hierarchy, employee offboarding as a status change
  that cancels active future bookings and revokes entitlements, and HRM integration as a webhook
  that syncs employee status into that same offboarding path.
