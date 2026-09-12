# Local Testing Checklist — run this before touching Render

Rule going forward: nothing gets deployed until every box below is checked
**locally, against Postgres** (not sqlite — sqlite is what let the last bug
slip through unnoticed).

## 0. One-time setup
```bash
docker compose up -d
cp .env.example .env
# edit .env if needed, then load it (comment-safe, works in Git Bash too):
set -a
source .env
set +a

pip install -r requirements.txt --break-system-packages
python manage.py migrate
python manage.py createsuperuser
```

## 1. Confirm you're actually on Postgres, not sqlite
```bash
python manage.py runserver 8000 &
curl -s http://127.0.0.1:8000/debug-info | python3 -m json.tool
```
Check `database_engine` — it must say `django.db.backends.postgresql`.
If it says `sqlite3`, your `DATABASE_URL` isn't being picked up — fix that
before doing anything else, since sqlite hides bugs Postgres won't.

Check `database_check.ok` is `true` and `error` is `null`.

## 2. Admin — the thing that broke last time
- [ ] `http://127.0.0.1:8000/admin/login/` loads styled (not raw HTML)
- [ ] Logging in with the superuser succeeds and lands on the admin dashboard
- [ ] You can open the Pipeline/Segment/Incident/RiskAssessment list pages

## 3. API endpoints — run the smoke test against localhost
```bash
BASE_URL=http://127.0.0.1:8000 USERNAME=<your-superuser> PASSWORD=<your-password> ./smoke_test.sh
```
- [ ] All 9 checks pass

## 4. CORS — the one thing curl can't verify
Open a browser console on `http://localhost:3000` (or wherever the
frontend will run) and run:
```js
fetch('http://127.0.0.1:8000/dashboard', {
  headers: { Authorization: 'Token <your-token>' }
}).then(r => r.json()).then(console.log)
```
- [ ] No CORS error in the console, real JSON comes back

## 5. Only once ALL of the above pass locally
Deploy to Render, set the *same* env vars from `.env` there (with the
real Postgres `DATABASE_URL` Render gives you, not the docker-compose
one), then re-run steps 1–4 against the Render URL instead of localhost.

If something fails on Render but passed locally, the difference is
almost always an env var that's set locally but missing/wrong on
Render — compare `.env` against Render's Environment tab line by line
before looking anywhere else.
