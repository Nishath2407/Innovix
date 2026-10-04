# Deployment

Target architecture: React (Vercel) → Flask API (Railway or Render) → PostgreSQL (managed).

1. **Create a GitHub repository** and push this project (`.gitignore` already
   excludes `.env`, `node_modules/`, `venv/`, database files).
2. **Provision PostgreSQL** (Railway/Render/Supabase all work) and copy the
   connection string.
3. **Configure the backend service** (Railway/Render):
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:$PORT run:app`
4. **Set backend environment variables**: `DATABASE_URL`, `SECRET_KEY`,
   `JWT_SECRET_KEY`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`,
   `CORS_ORIGINS` (your Vercel URL), `FRONTEND_URL`.
5. **Run migrations** against the production database:
   `flask db upgrade` (after `flask db init && flask db migrate` if this is
   the first deploy — see Flask-Migrate docs).
6. **Seed demo data** (optional, staging only): `python scripts/seed_database.py`.
7. **Deploy the frontend to Vercel**: set root directory to `frontend/`,
   build command `npm run build`, output directory `dist`.
8. **Set frontend environment variables**: `VITE_API_URL` (your backend URL),
   `VITE_RAZORPAY_KEY_ID`.
9. **Configure CORS** on the backend to allow the exact Vercel domain.
10. **Configure Razorpay** with live keys once ready for real payments —
    never commit them.
11. **Verify** `GET /api/health` returns `{"status": "ok"}` from the deployed
    backend URL.
12. **Enable HTTPS** (Vercel/Railway/Render provide this by default) —
    required for secure cookies to function (`SESSION_COOKIE_SECURE=True` in
    production config).
13. **Smoke test** registration, login, therapist discovery, and booking
    against the live deployment before sharing the URL.
14. **Legal review**: replace placeholder `/terms`, `/privacy`, and
    `/medical-disclaimer` content with reviewed legal text before onboarding
    real users.
