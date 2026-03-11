# Vercel Deployment Guide

The ProcurAI application is configured as a dual-deployment setup on Vercel and requires a remote database to function in a serverless environment.

## Part 1: Provision a Free PostgreSQL Database

Because Vercel's backend hosting is serverless (ephemeral), the local SQLite database cannot be used in production. We must use a free cloud PostgreSQL database.

1. Go to [Supabase](https://supabase.com/) and create a free account.
2. Click **New Project**, choose an organization, name the project `procurai`, and create a secure database password.
3. Once the database is provisioned (takes a few minutes), navigate to **Project Settings -> Database**.
4. Scroll down to **Connection String** -> **URI**.
5. **CRUCIAL STEP FOR VERCEL**: You MUST use the **Connection Pooler** instead of the Direct Connection. Check the box for "Use connection pooling" (Mode: Transaction).
6. Copy the connection string. Make sure to replace `[YOUR-PASSWORD]` with the password you just created.
   * *Example string: `postgresql://postgres:MySecurePassword123@aws-0-eu-central-1.pooler.supabase.com:6543/postgres`*

---

## Part 2: Deploy the Backend (FastAPI)

1. Push your latest code to your GitHub repository.
2. Go to your **Vercel** dashboard and click **Add New** -> **Project**.
3. Import your repository (`ProcurAI`).
4. **Important configuration**:
   *   **Project Name:** `procurai-backend` (or similar)
   *   **Framework Preset:** `Other`
   *   **Root Directory:** Click Edit and select the `backend` folder.
5. Expand the **Environment Variables** section and add the following keys from your local `.env`:
   *   `DATABASE_URL`: **PASTE THE SUPABASE CONNECTION STRING YOU COPIED IN PART 1**
   *   `MISTRAL_API_KEY`: `your_mistral_api_key_here`
   *   `SECRET_KEY`: `your_jwt_secret_key`
6. Click **Deploy**. Vercel will automatically read the `vercel.json` file inside the `backend` folder and deploy your FastAPI app as serverless functions.
7. Once successfully deployed, click on the project dashboard and copy the **Domains** URL (e.g., `https://procurai-backend.vercel.app`). 
   *   *Test it by going to `https://procurai-backend.vercel.app/docs` in your browser.*

---

## Part 3: Deploy the Frontend (Next.js)

1. Go back to your **Vercel** dashboard and click **Add New** -> **Project** again.
2. Import the exact same GitHub repository (`ProcurAI`).
3. **Important configuration**:
   *   **Project Name:** `procurai-frontend` (or similar)
   *   **Framework Preset:** `Next.js` (Vercel should auto-detect this).
   *   **Root Directory:** Click Edit and select the `frontend` folder.
4. Expand the **Environment Variables** section and add:
   *   `NEXT_PUBLIC_API_URL`: **PASTE THE BACKEND URL YOU COPIED IN PART 2** (e.g., `https://procurai-backend.vercel.app`). *Do not include a trailing slash.*
5. Click **Deploy**.
6. Once deployed, click on the frontend domain and test the application. The frontend should successfully route all user signups, logins, and analysis requests to your live serverless backend.

---

*Note: The machine learning specific PDF extractor `docling` was removed from the serverless deployment file because it vastly exceeds AWS Lambda's 250MB limit. The backend will automatically and seamlessly fallback to using `pypdf` for live production document extraction. Additionally, the backend gracefully falls back to a local SQLite database when running locally without a `DATABASE_URL` environment variable.*
