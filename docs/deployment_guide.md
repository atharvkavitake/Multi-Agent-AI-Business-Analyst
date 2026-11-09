# Production Cloud Deployment Guide
## Multi-Agent AI Business Analyst & Automated Business Intelligence System

This guide provides end-to-end instructions for deploying the **Multi-Agent AI Business Analyst & Automated BI System** entirely on **100% free-tier cloud services** with zero monthly hosting costs.

---

## 1. Free-Tier Cloud Architecture Overview

| Component | Free Cloud Provider | Free Tier Specification | Purpose |
| :--- | :--- | :--- | :--- |
| **Backend & Frontend** | **Render Web Services** | 512 MB RAM, 0.1 CPU, Free SSL, Auto CI/CD | Hosts FastAPI backend + mounts responsive enterprise UI at `/app/` |
| **Relational Database** | **Supabase PostgreSQL** | 500 MB storage, pooling engine, automatic SSL | Stores user accounts, dataset metadata, analysis runs, agent results, chat history |
| **Generative AI** | **OpenRouter Free Tier** | Rate-limited free models (Zero credit card required) | Powers AI reasoning (`google/gemini-2.0-flash-exp:free`, `meta-llama/llama-3.3-70b-instruct:free`) |
| **Static UI (Optional)** | **GitHub Pages** | Free unlimited static hosting | Optional decoupled frontend deployment |
| **Keep-Alive Monitor** | **Cron-Job.org / UptimeRobot** | Free HTTP pinging every 10 minutes | Mitigates Render 15-minute inactivity spin-down |

---

## 2. Step 1: Push Code to GitHub

Ensure your local repository is committed and pushed to your personal GitHub account.

```powershell
# Check Git status
git status

# Commit any pending changes
git add .
git commit -m "feat: complete multi-agent BI system ready for deployment"

# Link to your remote GitHub repository
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/multi-agent-bi-system.git
git branch -M master
git push -u origin master
```

---

## 3. Step 2: Set Up Supabase Free PostgreSQL Database

Supabase provides an enterprise-grade managed PostgreSQL database on AWS with high availability and SSL.

1. Navigate to [Supabase](https://supabase.com/) and click **Sign Up** (or log in via GitHub).
2. Click **New Project**:
   - **Name:** `bi-system-db`
   - **Database Password:** Enter a strong password (save this securely).
   - **Region:** Choose a region close to your Render deployment (e.g., *US East (N. Virginia)* or *Frankfurt*).
   - **Pricing Plan:** Free ($0/month).
3. Wait ~90 seconds for project provisioning.
4. Navigate to **Project Settings** (gear icon) -> **Database** -> **Connection string**:
   - Select **URI**.
   - Select **Mode: Session** (Port 5432) or **Transaction** (Port 6543 via Supavisor pooler).
   - The connection string will look like:
     ```text
     postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxx.supabase.co:5432/postgres
     ```
     *(Note: Replace `[YOUR-PASSWORD]` with your actual password. If your password contains special characters like `@`, `#`, or `$`, URL-encode them: e.g., `@` becomes `%40`).*

> **Automatic Schema Migration:** The FastAPI backend's `lifespan` handler automatically runs `Base.metadata.create_all(bind=engine)` upon boot, provisioning all 6 relational tables (`users`, `datasets`, `analyses`, `agent_results`, `chat_histories`, `reports`) on Supabase on first run. No manual SQL scripts required!

---

## 4. Step 3: Get Free OpenRouter API Key

1. Navigate to [OpenRouter.ai](https://openrouter.ai/) and sign in with Google or GitHub.
2. Go to **Settings** -> **Keys**.
3. Click **Create Key**:
   - **Name:** `BI-System-Free-Tier`
   - **Credit Limit:** Leave blank or $0.
4. Copy the generated key (`sk-or-v1-...`).
5. OpenRouter provides free access to models marked `:free`:
   - `google/gemini-2.0-flash-exp:free` (Default)
   - `meta-llama/llama-3.3-70b-instruct:free` (Fallback)

---

## 5. Step 4: Deploy to Render Web Services

Render allows deploying Python and Docker web services with automatic HTTPS and continuous deployment directly from your GitHub repository.

### Option A: One-Click Blueprint Deployment (Recommended)

1. Navigate to [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** -> **Blueprint**.
3. Connect your GitHub repository (`multi-agent-bi-system`).
4. Render will detect the included [`render.yaml`](../render.yaml) file.
5. In the configuration screen, supply your secret variables:
   - `DATABASE_URL`: Your Supabase connection string.
   - `OPENROUTER_API_KEY`: Your OpenRouter API key.
6. Click **Apply**. Render will build and deploy the application automatically.

---

### Option B: Manual Web Service Setup

If you prefer to configure manually via the Render UI:

1. Click **New +** -> **Web Service**.
2. Connect your GitHub repository.
3. Configure the service settings:
   - **Name:** `multi-agent-bi-system`
   - **Region:** US Oregon (or closest to your Supabase region)
   - **Branch:** `master`
   - **Runtime:** `Python 3`
   - **Build Command:**
     ```bash
     pip install --upgrade pip && pip install -r backend/requirements.txt
     ```
   - **Start Command:**
     ```bash
     uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type:** `Free` (512 MB RAM, 0.1 CPU)

4. Add the following **Environment Variables**:

| Variable Key | Recommended Value | Notes |
| :--- | :--- | :--- |
| `PYTHON_VERSION` | `3.10.11` | Ensures binary wheel compatibility |
| `ENVIRONMENT` | `production` | Enables production optimizations |
| `DEBUG` | `false` | Disables debug stack traces in production |
| `SECRET_KEY` | *(Generate a random 32-character string)* | Used for JWT signing and token verification |
| `DATABASE_URL` | `postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres` | Your Supabase connection string |
| `OPENROUTER_API_KEY` | `sk-or-v1-...` | Free tier API key |
| `DEFAULT_LLM_MODEL` | `google/gemini-2.0-flash-exp:free` | Primary reasoning model |
| `FALLBACK_LLM_MODEL`| `meta-llama/llama-3.3-70b-instruct:free` | Secondary fallback model |
| `CORS_ORIGINS` | `*` | Allow requests from all origins (or your custom domain) |
| `MAX_UPLOAD_SIZE_MB`| `25` | File upload ceiling |
| `ALLOW_GUEST_MODE` | `true` | Allows recruiters to evaluate without registering |

5. Under **Advanced**, set **Health Check Path** to:
   ```text
   /health
   ```
6. Click **Create Web Service**.
7. Render will build the package, install wheels, run schema setup, and assign you a live HTTPS URL (e.g., `https://multi-agent-bi-system.onrender.com`).

---

## 6. Accessing Your Deployed Application

Once deployment completes:
- **Interactive Enterprise UI:** `https://<YOUR-RENDER-URL>.onrender.com/app/`
- **Interactive Swagger Documentation:** `https://<YOUR-RENDER-URL>.onrender.com/docs`
- **Health Check Endpoint:** `https://<YOUR-RENDER-URL>.onrender.com/health`

---

## 7. Step 5: (Optional) Decoupled Frontend on GitHub Pages

If you prefer hosting the static frontend separately on GitHub Pages while keeping the backend on Render:

1. In the `frontend/` directory, open `frontend/js/api.js`.
2. Notice the dynamic host detection:
   ```javascript
   const API_BASE_URL = window.API_BASE_URL || localStorage.getItem("bi_api_url") || window.location.origin;
   ```
3. In GitHub repo settings:
   - Navigate to **Settings** -> **Pages**.
   - Under **Build and deployment**, select **Source:** Deploy from a branch.
   - Choose `master` branch and `/frontend` folder.
   - Click **Save**.
4. Visit your GitHub Pages URL (e.g., `https://<USERNAME>.github.io/multi-agent-bi-system/`).
5. Open the browser console or settings page and enter your live Render API URL:
   ```javascript
   localStorage.setItem("bi_api_url", "https://<YOUR-RENDER-URL>.onrender.com");
   ```

---

## 8. Step 6: Handling Render Free-Tier Cold Starts

### Why Cold Starts Happen
On Render's Free tier, services spin down into sleep mode if they receive no incoming HTTP requests for **15 consecutive minutes**. The next incoming request triggers a container wake-up, which takes **30–50 seconds**.

### Free Mitigation Strategy (Automatic Ping)
You can keep your application permanently warm for $0 using a free automated uptime pinger:

1. Sign up at [Cron-Job.org](https://cron-job.org/) (100% free) or [UptimeRobot](https://uptimerobot.com/).
2. Create a new recurring monitor:
   - **URL:** `https://<YOUR-RENDER-URL>.onrender.com/health`
   - **Interval:** Every **10 minutes**
   - **Method:** `GET`
3. This sends a lightweight request to the `/health` endpoint every 10 minutes, preventing Render from spinning down during business hours and interview evaluations!

---

## 9. Step 7: Production Verification Checklist

Run through this verification checklist once deployed:

- [ ] **Health Check:** Open `https://<YOUR-RENDER-URL>/health` - verify `{"status": "healthy", "database": "connected"}`.
- [ ] **Swagger UI:** Open `https://<YOUR-RENDER-URL>/docs` - verify all 14 endpoints are rendered with interactive try-it-out.
- [ ] **Web UI Landing Page:** Open `https://<YOUR-RENDER-URL>/app/` - verify modern hero section, feature cards, and responsiveness.
- [ ] **Guest Login:** Click **"Explore as Guest"** - verify instant JWT token issuance and redirect to Dashboard.
- [ ] **Upload Benchmark Dataset:** Go to Upload, upload `data/sample_sales.csv` (or any business dataset). Verify automatic schema profiling, KPI computation, and data quality grading (100% / Grade A+).
- [ ] **Multi-Agent Execution:** Click **"Analyze Dataset"** - verify 7 specialized agents run in sequence, showing live stage badges and execution timers.
- [ ] **Interactive Visualizations:** Inspect KPI cards, revenue trends, segment breakdowns, and distribution histograms.
- [ ] **Natural Language Query Engine:** Go to BI Chat, ask *"What was the total revenue?"* and *"Which region is underperforming?"*. Verify instant answers with verified mathematical calculations.
- [ ] **Executive PDF Generation:** Go to Reports, click **"Download Executive PDF"**. Verify clean two-column PDF download with branding, KPI summary tables, and prioritized strategic recommendations.
