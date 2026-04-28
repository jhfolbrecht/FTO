# FTO Program Database

A web app for managing a law-enforcement Field Training Officer (FTO) program.
Built with Flask + SQLAlchemy + SQLite. Implements the **San Jose Model** of daily
observation reporting.

## Features

- **Three roles** — Admin, Field Training Officer, Trainee — each with a
  role-aware dashboard and access controls.
- **Trainee records** — demographics, academy class, hire/start dates, current
  phase, primary FTO assignment, status (active / remediation / completed / etc.).
- **Daily Observation Reports (DORs)** — full San Jose Model: 32 standardized
  performance categories grouped into 8 sections (Appearance, Attitude,
  Knowledge, Performance, Officer Safety, Control of Conflict, Decision Making,
  Radio, Relationships), each rated 1-7 with NRT (Not Responded To) and
  per-category comments. Narrative blocks for most/least acceptable performance.
  Lockable when finalized.
- **Phase progression** — 4 standard phases (P1 Introduction, P2 Patrol,
  P3 Investigation, P4 Shadow). End-of-phase evaluations with decision
  (advance / repeat / remediate / complete / release) automatically update the
  trainee's phase and status.
- **Reports & dashboards** — phase distribution, FTO workload, 30-day trainee
  averages, hot-spot categories where trainees are weakest, per-trainee
  category breakdowns, score-over-time charts, and CSV export of all DORs.
- **Audit log** — captures logins, password changes, and creation/update of
  trainees, users, DORs, and evaluations.
- **Print-friendly DOR detail view** — clean printout for paper file copies.

## Tech stack

- Python 3.10+ · Flask 3 · Flask-SQLAlchemy · Flask-Login · Flask-WTF
- SQLite by default; Postgres via `DATABASE_URL`
- Bootstrap 5 + Chart.js (CDN, no build step)
- Gunicorn for production
- Configured for Render (`render.yaml`)

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed.py                       # creates demo data
python wsgi.py                       # http://localhost:5000
```

### Default credentials (after `python seed.py`)

| Role     | Username  | Password         |
| -------- | --------- | ---------------- |
| Admin    | `admin`   | `ChangeMe!2026`  |
| FTO      | `jsmith`  | `FtoPass!23`     |
| Trainee  | `rdoe`    | `TraineePass!23` |
| Trainee  | `agarcia` | `TraineePass!23` |

**Change the admin password immediately after first login.** You can also
override the bootstrap password via env var:

```bash
ADMIN_PASSWORD="MyStrongAdminPass!" python seed.py --bootstrap
```

## Deploy to Render

1. Push this folder to a GitHub repository.
2. In Render, click **New > Blueprint** and point it at the repo. Render
   reads `render.yaml` and provisions:
   - one `python` web service running `gunicorn wsgi:app`
   - a 1 GB persistent disk mounted at `/var/data` (where `fto.db` lives)
   - a generated `SECRET_KEY` env var
3. The release step runs `python seed.py --bootstrap`, which idempotently
   creates the default admin user on first boot.
4. Open the service URL, sign in as `admin` / `ChangeMe!2026`, and **change
   the password** under *Change password* in the top nav.

### Render plan note

Persistent disks require **Render's Starter plan ($7/mo)** or higher — the
free plan has ephemeral storage and would lose the SQLite file on restart.
If you need to stay on the free tier, switch to Postgres:

1. In the Render dashboard, **New > PostgreSQL**, free tier.
2. Copy the **Internal Database URL**.
3. On the web service, add env var `DATABASE_URL=<the internal URL>`.
4. Remove (or ignore) the `disk:` block in `render.yaml`.
5. Trigger a redeploy. The app auto-detects Postgres and creates the schema.

### Other hosts

The app runs anywhere that can run a Python WSGI process:

```bash
gunicorn wsgi:app --bind 0.0.0.0:$PORT
```

Required env vars in production:
- `SECRET_KEY` — long random string
- `DATABASE_URL` *or* `SQLITE_PATH`
- `FLASK_ENV=production` — enables secure-cookie flags

## Project layout

```
FTO/
├── app/
│   ├── __init__.py        # app factory
│   ├── extensions.py      # SQLAlchemy instance (avoids circular import)
│   ├── constants.py       # San Jose categories, phases, roles, scale
│   ├── models.py          # User, Trainee, DOR, DORRating, PhaseEvaluation, AuditLog
│   ├── forms.py           # WTForms
│   ├── security.py        # role-based access decorators
│   ├── auth.py            # login / logout / change-password
│   ├── main.py            # role-specific dashboards
│   ├── trainees.py        # trainee CRUD
│   ├── dors.py            # daily observation reports
│   ├── evals.py           # end-of-phase evaluations
│   ├── reports.py         # dashboards, hot-spots, CSV export
│   ├── admin.py           # user management
│   ├── static/style.css
│   └── templates/         # Jinja templates
├── config.py              # config + DATABASE_URL resolution
├── wsgi.py                # gunicorn entrypoint
├── seed.py                # bootstrap admin + demo data
├── requirements.txt
├── render.yaml            # Render Blueprint
├── Procfile               # Heroku/alt PaaS entrypoint
└── .gitignore
```

## Customization

- **Different DOR model** — edit `app/constants.py`. `DOR_CATEGORIES` is the
  canonical category list and `DOR_SECTIONS` controls how they're grouped on
  the form/detail view. The UI rebuilds itself from these constants.
- **Different rating scale** — change `RATING_SCALE` and
  `ACCEPTABLE_THRESHOLD` in `constants.py`. Update `score-N` CSS classes in
  `static/style.css` to match.
- **Different phases** — edit `PHASES` in `constants.py`. Phase advancement
  logic in `evals.py` walks the list in order, so adding/removing phases just
  works.

## Security notes

- Passwords are hashed with `werkzeug.security` (PBKDF2). Never stored plaintext.
- All state-changing endpoints are CSRF-protected via Flask-WTF (the DOR form
  uses a manual HTML form but explicitly includes the CSRF token).
- Production cookies are `Secure`, `HttpOnly`, `SameSite=Lax` when
  `FLASK_ENV=production`.
- Role checks are enforced by `@admin_required` / `@fto_or_admin_required` /
  per-record visibility checks in each blueprint.
- For real deployment in a law-enforcement environment, also add: TLS at the
  edge (Render handles this automatically), backup of the DB volume,
  multi-factor auth (consider Authlib + TOTP), IP allowlisting if appropriate,
  and a documented data-retention policy.
- The audit log captures actor + action + target. You may want to surface it
  in the admin UI — straightforward addition.

## License

Internal project — no license declared. Add one before public distribution.
