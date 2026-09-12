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
  "pipeline_count": 1,
  "segment_count": 1,
  "average_risk_score": 50.0,
  "risk_level_breakdown": [{ "risk_level": "Medium", "count": 1 }],
  "latest_assessments": [
    {
      "segment_id": "PL-05-SG-12",
      "risk_score": 50,
      "risk_level": "Medium",
      "created_at": "2026-09-09T21:51:35.442628Z"
    }
  ]
}
```

---

## `GET /segments`
**Response — 200**
```json
[
  {
    "id": 1,
    "segment_code": "PL-05-SG-12",
    "pipeline_name": "Default Pipeline",
    "latitude": 6.34,
    "longitude": 5.62
  }
]
```

---

## `GET /segments/{id}`
**Response — 200**
```json
{
  "id": 1,
  "segment_code": "PL-05-SG-12",
  "pipeline": { "id": 1, "name": "Default Pipeline", "location": "Unknown", "status": "active" },
  "latitude": 6.34,
  "longitude": 5.62,
  "environmental_data": {},
  "inspection_history": {},
  "incidents": [],
  "risk_assessments": [
    {
      "id": 1,
      "risk_score": 50,
      "risk_level": "Medium",
      "explanation": "...",
      "recommendation": "Schedule inspection within 30 days.",
      "created_at": "2026-09-09T21:51:35.442628Z"
    }
  ]
}
```
**Response — 404** if the id doesn't exist — see error shape above (`code: "http404"`)

---

## `POST /risk-assess`
**Request**
```json
{
  "segment_code": "PL-05-SG-12",
  "latitude": 6.34,
  "longitude": 5.62,
  "environmental_data": { "corrosion_risk": true, "soil_moisture": true },
  "inspection_history": {}
}
```
`segment_code` is required. Everything else is optional — if the segment already exists, only `segment_code` is needed and stored `environmental_data` is used.

**Response — 201**
```json
{
  "segment_id": "PL-05-SG-12",
  "risk_score": 87,
  "risk_level": "High",
  "explanation": "Corrosion indicators combined with a recent leak incident.",
  "contributing_factors": ["corrosion", "soil_moisture", "past_incident"],
  "recommendation": "Schedule inspection within 7 days."
}
```
**Response — 400** on missing/invalid fields — see error shape above.

---

## Local dev setup for the frontend
1. Backend team runs `python manage.py runserver 8000`.
2. Set `CORS_ALLOWED_ORIGINS` on the backend (env var) to match wherever the frontend dev server runs — defaults to `http://localhost:3000`.
3. Point the frontend's API base URL at `http://127.0.0.1:8000` (or wherever the backend is hosted for shared dev/staging).
