# AgriShield AI

AgriShield AI is a responsive farm dashboard for weather risk, soil moisture, crop guidance, nearby market prices, and a Malayalam/English farming assistant.

## Run locally

1. Install frontend dependencies: `npm install`
2. Start the frontend: `npm run dev`
3. In another terminal, install the API dependencies with `python -m pip install -r backend/requirements.txt`
4. Start the API: `python -m uvicorn backend.main:app --reload --port 8000`

The frontend works with demonstration data when the API is not running. API endpoints are proxied through Vite at `/api` when FastAPI is available. API documentation is at `http://127.0.0.1:8000/docs`.

## Integrations and demo labels

- Demo weather, sensor, market, and farm profile values are labelled in the app. The API uses OpenWeatherMap if `OPENWEATHER_API_KEY` is set; failed requests return demo values with an error note.
- Soil moisture is simulated by default. The `/api/irrigation` endpoint accepts sensor readings; connect an ESP32 to post `{ "moisture_pct": 42, "source": "sensor" }`.
- Crop advice and assistant replies use transparent, simple demo rules. They are not trained ML or generative AI predictions.
- Market values are demonstration figures, not live trading prices.
- Farmer profiles use demo storage when `DATABASE_URL` is absent. When PostgreSQL is configured, the API creates and uses a `farmer_profile` table for durable profile storage.

## Main API routes

`GET /api/health`, `GET /api/dashboard`, `GET /api/climate`, `GET/POST /api/irrigation`, `POST /api/crops/recommend`, `POST /api/assistant`, `GET /api/market`, and `GET/PUT /api/profile`.
