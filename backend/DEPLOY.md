# Deployment Guide

## Deploy Backend to Render

1. Create a GitHub repo and push your `backend/` folder (or whole project) to it.
2. Sign up at https://render.com and create a new **Web Service**.
3. Connect your GitHub repo and select the branch (e.g., `main`).
4. Set the Build Command:

```bash
pip install -r requirements.txt
```

5. Set the Start Command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

6. Add environment variables in the Render dashboard:
- `SECRET_KEY` (your secret)
- `DATABASE_URL` (postgres://... — Render provides a free PostgreSQL instance)
 - `ADMIN_TOKEN` (secure admin token for admin endpoints)
 - `WEBHOOK_SECRET` (secret TradingView will send in alert payloads)
 - `ENVIRONMENT` (set to `production`)

7. Click **Create Web Service** → Deploy. Render will give you a public URL like `https://trading-platform.onrender.com`.

Notes:
- Set `DATABASE_URL` to the Postgres database Render provides. SQLite is not used in production.
- Every push to the connected branch triggers an automatic redeploy.

CI/CD:
- The repository includes a GitHub Actions workflow `backend/.github/workflows/ci.yml` that runs tests and lint on push to `main`.

Requirements:
- Ensure `backend/requirements.txt` contains `psutil`, `slowapi`, and `psycopg[binary]` for production.


## Deploy Frontend to Vercel

1. Push your frontend (React) to GitHub.
2. Sign up at https://vercel.com and import the GitHub repo.
3. Configure the project:
   - Framework: Create React App
   - Build Command: `npm run build`
   - Output Directory: `build`
4. Add environment variable in Vercel:
   - `REACT_APP_API_URL` = `https://trading-platform.onrender.com`
5. Deploy. Vercel provides a public URL like `https://trading-platform.vercel.app`.


## Post-Deployment

- Update your TradingView webhook URL to `https://<your-render-url>/webhook`.
- Monitor logs on Render and Vercel dashboards.
- Use environment variables for secrets and DB credentials (do not commit `.env`).

