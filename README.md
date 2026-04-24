# 4M Gold AI

AI-powered gold direction forecasting app built with FastAPI, MySQL, and React.

## What It Does

- Predicts gold direction for the next 5 calendar days
- Returns `UP` and `DOWN` probabilities, not exact prices
- Fetches gold, oil, and USD market data from Alpha Vantage
- Caches market history in MySQL for training and predictions
- Supports manual historical backfill
- Supports automatic daily updates and startup syncing
- Supports user registration/login
- Supports buy/sell gold transactions and profit/loss summaries

## Data Source

The backend now uses Alpha Vantage instead of Yahoo Finance.

- Gold prices: Alpha Vantage commodity history
- Oil prices: Alpha Vantage WTI series
- USD index: stored as a USD strength proxy from the Alpha Vantage `FX_DAILY` USD/EUR series

Because the project respects the Alpha Vantage free tier, the backend minimizes API calls by:

- Caching fetched data in MySQL
- Skipping duplicate dates
- Tracking sync logs and last update date
- Using a lightweight daily snapshot for startup and scheduled updates

## Project Structure

```text
4m-gold-ai/
  backend/
    app/
      core/
      db/
      models/
      routes/
      schemas/
      services/
    scripts/
    requirements.txt
    schema.sql
  frontend/
    src/
    package.json
    vite.config.js
```

## Backend Setup

1. Create a MySQL database.
2. Copy `backend/.env.example` to `backend/.env`.
3. Fill in:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `ALPHA_VANTAGE_API_KEY`
4. Install Python dependencies:

```bash
cd backend
pip install -r requirements.txt
```

5. Run the API:

```bash
uvicorn app.main:app --reload --port 8000
```

## Environment Variables

The most important backend variables are:

```env
ALPHA_VANTAGE_API_KEY=YOUR_API_KEY_HERE
APP_TIMEZONE=Africa/Cairo
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/4m_gold_ai
AUTO_SYNC_ON_STARTUP=true
AUTO_TRAIN_ON_STARTUP=true
```

Optional:

- `ALPHA_VANTAGE_BASE_URL` defaults to `https://www.alphavantage.co/query`
- `MODEL_PATH` defaults to `artifacts/gold_model.pkl`
- `DATABASE_URL` should point to the Railway public MySQL URL in production

## Market Data Sync

The backend exposes both manual and automatic sync flows.

### Manual historical backfill

`POST /fetch-historical-data`

- Triggered manually by the user or admin
- Backfills up to 5 years of historical data when available
- Stores rows in MySQL
- Skips duplicate dates

### Daily update

- Runs automatically every 24 hours
- Fetches only the current snapshot
- Skips work if today's row already exists

### Startup sync

- On backend startup, the app checks whether today's row exists
- If not, it fetches and stores today's data

### Admin status

`GET /market/admin/status`

Returns:

- Latest market date
- Latest sync time
- API calls used today
- Whether today's row already exists
- The last sync log entry

## API Endpoints

### Market

- `POST /market/sync` - fetch today's market snapshot
- `POST /fetch-historical-data` - backfill historical data
- `GET /market/latest` - get the latest market row
- `GET /market/admin/status` - get sync status and API usage

### Predictions

- `GET /predictions/next-5-days` - generate 5-day direction probabilities

### Auth / Portfolio

Existing authentication and portfolio routes remain available under the same backend app.

## Model Training

The AI pipeline reads from MySQL, not Excel.

Train manually with:

```bash
cd backend
python scripts/train_model.py
```

This script:

- Ensures market data is available
- Trains the linear regression model from database rows
- Saves the model artifact to `artifacts/gold_model.pkl`

## Frontend Setup

1. Install Node dependencies:

```bash
cd frontend
npm install
```

2. Start the dev server:

```bash
npm run dev
```

3. For deployed builds, set:

```env
VITE_API_URL=https://your-railway-backend.up.railway.app
```

The frontend build command is:

```bash
npm run build
```

Vite outputs the production site to `frontend/dist`.

## Deployment

### Backend on Railway

Deploy the `backend` directory as the Railway service root.

Railway can use the included:

- `backend/railway.toml`
- `backend/Procfile`
- `backend/.python-version`
- `.python-version`

The backend is pinned to Python 3.11.

The production start command is:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set these Railway environment variables:

```env
SECRET_KEY=replace_with_a_long_random_secret
FRONTEND_ORIGINS=https://your-netlify-site.netlify.app
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
APP_TIMEZONE=Africa/Cairo
AUTO_SYNC_ON_STARTUP=true
AUTO_TRAIN_ON_STARTUP=true
DATABASE_URL=mysql+pymysql://USER:PASSWORD@shuttle.proxy.rlwy.net:PORT/4m_gold_ai
```

Use the Railway public MySQL URL, not the internal host.

### Frontend on Netlify

Deploy from the repository root using the included `netlify.toml`.

Netlify settings:

- Build command: `cd frontend && npm ci && npm run build`
- Publish directory: `frontend/dist`
- Environment variable: `VITE_API_URL=https://your-railway-backend.up.railway.app`

SPA routing is handled by:

- `netlify.toml`
- `frontend/public/_redirects`

This lets routes like `/dashboard`, `/portfolio`, and `/profile` refresh correctly on Netlify.

## Notes

- The backend uses MySQL for all historical market storage and training data.
- The market table enforces unique dates, and the startup migration upgrades older `usd_price` databases to `usd_index`.
- If the Alpha Vantage API key is missing, the app can still start, but any market sync request will fail with a clear error.
- Set `FRONTEND_ORIGINS` on Railway to the exact Netlify URL so browser requests are allowed by CORS.
- Set `VITE_API_URL` on Netlify to the exact Railway backend URL so Axios calls the deployed API.
