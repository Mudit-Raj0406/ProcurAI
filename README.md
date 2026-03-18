# ProcurAI - Intelligent Procurement Assistant

## Setup Instructions

### Backend (Python/FastAPI)

1.  Navigate to the `backend` directory.
2.  Create a virtual environment (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Important**: Set your Google Cloud credentials or API Key relative to how you configured `services/llm_extractor.py`.
    - If using Vertex AI, ensure `gcloud auth application-default login` is run.
    - If using Gemini API Key, set `GOOGLE_API_KEY` in environment.
5.  Run the server:
    ```bash
    uvicorn main:app --reload --port 8010
    ```
    The API will be available at `http://localhost:8010`.

### Frontend (Next.js)

1.  Navigate to the `frontend` directory.
2.  Install dependencies:
    ```bash
    npm install
    # or
    yarn install
    ```
3.  Run the development server:
    ```bash
    npm run dev
    ```
    The dashboard will be available at `http://localhost:3010`.

## Features
- **Upload**: Drag & drop PDF RFQs/Quotes.
- **Extraction**: Automatically extracts Price, Lead Time, MOQ, Payment Terms, and IATF Compliance using Gemini Pro.
- **Risk Analysis**: Flags potential risks like missing compliance or long lead times.
- **Comparison**: Side-by-side view of all vendor stats.
