# Auth - Django Login/Signup App

## Deploying to Render

### Option A - Blueprint (recommended)
1. Push this project to a GitHub/GitLab repo (make sure manage.py is at the repo root, or set Render's Root Directory to wherever it lives).
2. In Render, click New + -> Blueprint, point it at the repo. Render will read render.yaml and create BOTH a free Postgres database (auth-django-db) and the web service in one go, wiring DATABASE_URL and a generated SECRET_KEY automatically. No manual database setup needed.
3. Click Apply. Render runs build.sh (installs deps, collects static files, runs migrations against the new Postgres database) and starts the app with gunicorn Auth.wsgi:application.

### Option B - Manual Web Service
1. New + -> Web Service -> connect your repo.
2. Build Command: ./build.sh
3. Start Command: gunicorn Auth.wsgi:application
4. Environment variables:
   - SECRET_KEY - generate one (Render can auto-generate under "Generate Value")
   - DEBUG - False
   - (optional) ALLOWED_HOSTS - only needed if you attach a custom domain; Render's own *.onrender.com hostname is trusted automatically
   - (optional) DATABASE_URL - attach a Render Postgres instance for persistent storage (see below)

### Database note
- Using the Blueprint (Option A): a free Postgres database is created and wired up for you automatically via render.yaml - nothing else to do.
- Using a manual Web Service (Option B) or if you skipped the database in the Blueprint: the app falls back to SQLite, which lives on Render's ephemeral disk and resets on every deploy. Add a free Render Postgres instance and set its Internal Database URL as the DATABASE_URL env var to fix that; the app picks it up automatically via dj-database-url.
- Render's free Postgres plan expires after 30 days. When you're ready for something longer-lived, upgrade the database's plan in the Render dashboard (no code changes needed).

### Local development
```
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
DEBUG defaults to False; set DEBUG=True in your shell for local dev to see full error pages and skip the HTTPS-only cookie/redirect settings.

## What changed for deployment-readiness
- SECRET_KEY, DEBUG, and ALLOWED_HOSTS now read from environment variables instead of being hardcoded/empty.
- Added whitenoise so static files (Login/static/style.css) are served correctly with DEBUG=False, plus STATIC_ROOT/collectstatic support.
- Added gunicorn as the production WSGI server (Django's runserver isn't safe/performant for production).
- Added dj-database-url + psycopg2-binary so you can switch from SQLite to Postgres just by setting DATABASE_URL.
- Added HTTPS-only security settings (SECURE_SSL_REDIRECT, secure cookies) that only activate when DEBUG=False.
- Fixed a bug: the Login app had no actual migration file (only an empty migrations/__init__.py), so its User table was never created and signup/login would have failed with a "no such table" error. Generated Login/migrations/0001_initial.py and verified signup/login end-to-end.
- Added build.sh, Procfile, and render.yaml for a one-click Render Blueprint deploy.

## Heads up - this app isn't using real security best practices
This looks like a learning/demo project, so a couple of things worth knowing before using it for anything real:
- Passwords are hashed correctly (make_password/check_password), which is good.
- The home page (index.html/views.index) currently displays the logged-in user's password hash, raw session details, and other internals directly on the page - fine for debugging, but you'll want to strip that out before showing this to real users.
- There's no rate-limiting on login/signup, so it's open to brute-force attempts as-is.

Happy to fix either of those if you'd like - just say the word.
