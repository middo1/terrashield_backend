# TerraShield API — Frontend Integration Guide

**Base URL:** `https://terrashield-backend.onrender.com`

Read this once, then use `API_CONTRACT.md` (in the backend repo) as the
field-by-field reference while you build. This doc is the "how do I
actually call this thing" version.

---

## 1. Heads up: cold starts
The backend is on Render's free tier, which sleeps after ~15 minutes of
no traffic. The **first** request after it's been idle can take
30-50 seconds to respond while it wakes up. This isn't a bug — if a
request seems to hang on first load, give it a minute before assuming
something's broken. Every request after that is fast.

## 2. Auth flow
1. `POST /login` with username/password → get a token back.
2. Store that token (state, memory, or secure storage — not localStorage
   if you're worried about XSS, but that's a call for your app).
3. Send it on every other request:
   ```
   Authorization: Token <the-token>
   ```
4. There's no refresh/expiry endpoint in this MVP. If a request comes
   back `401`, just re-hit `/login` and get a fresh token.

## 3. Example: login + fetch dashboard (vanilla fetch)
```js
const BASE_URL = 'https://terrashield-backend.onrender.com';

async function login(username, password) {
  const res = await fetch(`${BASE_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const { error } = await res.json();
    throw new Error(error.message);
  }
  const { token } = await res.json();
  return token;
}

async function getDashboard(token) {
  const res = await fetch(`${BASE_URL}/dashboard`, {
    headers: { Authorization: `Token ${token}` },
  });
  if (!res.ok) {
    const { error } = await res.json();
    throw new Error(error.message);
  }
  return res.json();
}
```

## 4. Error handling — one shape, everywhere
Every non-2xx response looks like this:
```json
{
  "error": {
    "code": "validation_error",
    "message": "One or more fields failed validation.",
    "details": { "segment_code": ["This field is required."] }
  }
}
```
`details` is only present for field-level validation errors. Write one
error handler off `error.message` (and `error.code` if you want to
branch behavior, e.g. redirect to login on `authentication_failed`)
rather than parsing each endpoint's failure differently.

## 5. Endpoints at a glance
| Endpoint | Method | Auth required | Purpose |
|---|---|---|---|
| `/login` | POST | No | Get a token |
| `/dashboard` | GET | Yes | Summary stats for the dashboard |
| `/segments` | GET | Yes | List all pipeline segments |
| `/segments/{id}` | GET | Yes | Full detail on one segment |
| `/risk-assess` | POST | Yes | Submit a segment, get back a risk assessment |

Full request/response JSON for each is in `API_CONTRACT.md`.

## 6. If you get a CORS error in the console
That means your frontend's origin isn't in the backend's allowed list
yet. Tell the backend dev exactly what origin your app runs from
(e.g. `http://localhost:5173` for Vite, `http://localhost:3000` for
Create React App / Next, or your deployed frontend's real URL) — it's a
one-line env var change on the backend, not a code change.

## 7. Test credentials
Ask the backend dev for a login to test against — don't guess or reuse
the admin superuser account for frontend testing; ask for a separate
regular user.
