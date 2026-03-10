# Vercel Deployment Guide

The ProcurAI application is configured as a dual-deployment setup on Vercel. You will create **two separate projects** in Vercel from this single GitHub repository.

---

## Part 1: Deploy the Backend (FastAPI)

1. Push your latest code to your GitHub repository.
2. Go to your **Vercel** dashboard and click **Add New** -> **Project**.
3. Import your repository (`ProcurAI`).
4. **Important configuration**:
   *   **Project Name:** `procurai-backend` (or similar)
   *   **Framework Preset:** `Other`
   *   **Root Directory:** Click Edit and select the `backend` folder.
5. Expand the **Environment Variables** section and add the following keys from your local `.env`:
   *   `MISTRAL_API_KEY`: `your_mistral_api_key_here`
   *   `SECRET_KEY`: `your_jwt_secret_key`
6. Click **Deploy**. Vercel will automatically read the `vercel.json` file inside the `backend` folder and deploy your FastAPI app as serverless functions.
7. Once successfully deployed, click on the project dashboard and copy the **Domains** URL (e.g., `https://procurai-backend.vercel.app`). 
   *   *Test it by going to `https://procurai-backend.vercel.app/docs` in your browser.*

---

## Part 2: Deploy the Frontend (Next.js)

1. Go back to your **Vercel** dashboard and click **Add New** -> **Project** again.
2. Import the exact same GitHub repository (`ProcurAI`).
3. **Important configuration**:
   *   **Project Name:** `procurai-frontend` (or similar)
   *   **Framework Preset:** `Next.js` (Vercel should auto-detect this).
   *   **Root Directory:** Click Edit and select the `frontend` folder.
4. Expand the **Environment Variables** section and add:
   *   `NEXT_PUBLIC_API_URL`: **PASTE THE BACKEND URL YOU COPIED IN PART 1** (e.g., `https://procurai-backend.vercel.app`). *Do not include a trailing slash.*
5. Click **Deploy**.
6. Once deployed, click on the frontend domain and test the application. The frontend should successfully route all user signups, logins, and analysis requests to your live serverless backend.

---

*Note: The machine learning specific PDF extractor `docling` was removed from the serverless deployment file because it vastly exceeds AWS Lambda's 250MB limit. The backend will automatically and seamlessly fallback to using `pypdf` for live production document extraction.*
