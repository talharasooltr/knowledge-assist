# Frontend Service (Streamlit)

This directory contains the frontend UI for the Knowledge Assistant multi source. It provides a web-based interface for users and admins to interact with the backend services.

## Local Development

### 1. Setup

1.  **From the repository root, create the shared virtual environment if it does not exist yet.** If `.venv` was already created for the backend, skip the first command. Do not create an environment inside `frontend/`:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

2.  **Install Dependencies**:
    ```bash
    python -m pip install -r frontend/requirements.txt
    ```

### 2. Environment Variable

The frontend needs to know the URL of the backend. This is configured via the `BACKEND_URL` environment variable.

* **For local development**: Set this variable to point to your locally running backend.
    ```bash
    export BACKEND_URL="[http://127.0.0.1:8000](http://127.0.0.1:8000)"
    ```

### 3. Running the Application

* **For Streamlit**:
    ```bash
    streamlit run home.py
    ```
    The application will be available at `http://localhost:8501`.

## Connecting to the Backend

The application code (`home.py`) is designed to read the `BACKEND_URL` from the environment.

```python
import os
BASE_URL = os.getenv("BACKEND_URL", "[http://127.0.0.1:8000](http://127.0.0.1:8000)")
```