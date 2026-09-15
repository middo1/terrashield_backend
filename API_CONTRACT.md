# TerraShield API Contract — MVP

Base URL: `https://terrashield-backend.onrender.com` (local dev: `http://127.0.0.1:8000`)

## Auth
Every endpoint except `/login` requires a token in the header:
```
Authorization: Token <token>
```
Get the token from `/login`. Store it (memory or secure storage) — there's no refresh endpoint in the MVP, so re-login when it's invalid (401).

## Error shape (all endpoints)
```json
{
  "error": {
    "code": "validation_error",
    "message": "One or more fields failed validation.",
    "details": { "segment_code": ["This field is required."] }
  }
}
```
`details` is omitted when there's nothing field-specific to show. Handle errors generically off `error.code` / `error.message`; don't parse per-endpoint.

---

## `POST /login`
**Request**
```json
{ "username": "tester", "password": "testpass123" }
```
Note: the login screen mockup labels this field "Email" — send whatever value goes in that field as `username`. There's no separate email-based auth in the MVP.

**Response — 200**
```json
{ "token": "8df3c082dd53ee7d81858e1b2e20711bed4123cc" }
```
**Response — 401** — see error shape above (`code: "authentication_failed"`)

---

## `GET /dashboard`
**Response — 200**
```json
{
  "total_pipelines": 18,
  "total_segments": 44,
  "high_risk_count": 6,
  "medium_risk_count": 11,
  "low_risk_count": 27,
  "risk_trend": [
    { "date": "2026-09-01", "average_risk_score": 42.3 },
    { "date": "2026-09-02", "average_risk_score": 45.0 }
  ],
  "recent_alerts": [
    { "segment_id": "PL-05-SG-12", "risk_level": "High", "created_at": "2026-09-09T21:51:35Z" },
    { "segment_id": "PL-02-SG-04", "risk_level": "Medium", "created_at": "2026-09-09T18:10:02Z" }
  ]
}
```
- `risk_trend` covers the last 14 days, one entry per day that has at least one assessment (no entry = no data that day, not zero — don't plot it as 0).
- `recent_alerts` is the 5 most recent assessments that are High or Medium (Low-risk results are excluded from alerts).
- `high_risk_count` / `medium_risk_count` / `low_risk_count` count segments by their *latest* assessment, not total assessments run.

---

## `GET /segments`
Query params (both optional):
- `?search=<text>` — matches segment code or pipeline name/code
- `?risk_level=<High|Medium|Low>` — filters by latest risk level

**Response — 200**
```json
[
  {
    "id": 1,
    "segment_code": "PL-05-SG-12",
    "pipeline_name": "Trans-Niger Segment",
    "latitude": 4.815,
    "longitude": 7.049,
    "status": "Active",
    "risk_level": "High",
    "risk_score": 87,
    "last_assessed_at": "2026-09-09T21:51:35Z"
  }
]
```
- `segment_code` is the full display id (`{pipeline.code}-{segment.code}`), matching what's shown in the UI everywhere.
- `risk_level` / `risk_score` / `last_assessed_at` are `null` if the segment has never been assessed.
- Format `last_assessed_at` client-side (e.g. "2h ago") — the backend returns a plain ISO timestamp.

---

## `GET /segments/{id}`
**Response — 200**
```json
{
  "id": 1,
  "segment_code": "PL-05-SG-12",
  "pipeline": { "id": 1, "code": "PL-05", "name": "Trans-Niger Segment", "location": "Unknown", "status": "active" },
  "latitude": 4.815,
  "longitude": 7.049,
  "status": "Active — flagged",
  "environmental_data": { "elevation": 18, "flood_risk": "High" },
  "inspection_history": {},
  "incidents": [
    { "id": 1, "incident_type": "Vandalism", "date": "2026-03-12", "severity": "" }
  ],
  "risk_assessments": [
    {
      "id": 1, "risk_score": 87, "risk_level": "High",
      "explanation": "...", "recommendation": "Schedule inspection within 7 days.",
      "created_at": "2026-09-09T21:51:35Z"
    }
  ]
}
```
**Response — 404** if the id doesn't exist — see error shape above (`code: "http404"`)

---

## `POST /risk-assess`
**Request** — this is the exact dataset the Segment Details page prepares and posts:
```json
{
  "pipeline_id": "PL-05",
  "segment_code": "SG-12",
  "latitude": 4.815,
  "longitude": 7.049,
  "environmental_data": { "elevation": 18, "flood_risk": "High" },
  "incident_history": [{ "type": "Vandalism", "date": "2026-03-12" }]
}
```
- `pipeline_id` and `segment_code` are **separate short codes** (e.g. `"PL-05"` + `"SG-12"`), not the combined `"PL-05-SG-12"` id shown in the UI.
- `pipeline_id` + `segment_code` are required. Everything else is optional — if the pipeline/segment already exist, they're reused; if not, they're created on the fly.
- `incident_history` items are saved as incident records on the segment (duplicates by type+date are ignored, safe to resend the same history on every assessment).

**Response — 201**
```json
{
  "segment_id": "PL-05-SG-12",
  "risk_score": 87,
  "risk_level": "High",
  "explanation": "Corrosion indicators combined with a recent incident raise this segment's overall exposure.",
  "contributing_factors": ["elevated flood risk", "low elevation", "1 recorded incident(s)"],
  "recommendation": "Schedule inspection within 7 days."
}
```
Note `segment_id` in the response **is** the combined display id (`"PL-05-SG-12"`) — asymmetric from the request on purpose, since the response is for display and the request is for lookup/creation.

**Response — 400** on missing/invalid fields — see error shape above.

---

## Local dev setup for the frontend
1. Backend team runs `python manage.py runserver 8000` (or points you at the Render URL above).
2. Set `CORS_ALLOWED_ORIGINS` on the backend (env var) to match wherever the frontend dev server runs — defaults to `http://localhost:3000`.
3. Point the frontend's API base URL at `http://127.0.0.1:8000` locally, or the Render URL for shared dev.
