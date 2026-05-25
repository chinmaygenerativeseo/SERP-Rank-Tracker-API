# Python SQL Server Connection & API Bootstrapper

A robust, production-ready, and high-performance **FastAPI** web API integrated with **Microsoft SQL Server** (supporting Azure SQL Database, managed instances, and local SQL Server installations).

---

## 🚀 Key Features

- **Sequential Connection Startup**: Verifies and establishes the database connection **before** starting the web server. If the connection fails, startup is safely aborted to prevent running a broken API server.
- **Persistent Connection Lifecycle**: Uses a modern FastAPI `lifespan` manager to maintain a persistent connection state (`app.state.db_conn`) while the server is active, gracefully closing it upon server shutdown.
- **High-Performance Pooling & Non-Blocking Async**: Implements dependency injection for standard database queries using native connection pooling via `pymssql` and offloads external blocking API HTTP calls to `asyncio.to_thread` pools.
- **Dedicated Route Files**: Clean architecture separating endpoints into [endpoints.py](file:///d:/Projects/GenerativeSSO/Python_KeyWordRankTracker/endpoints.py) for easy maintenance.
- **Vibrant Status UI**: Serves a beautiful, glassmorphic welcome page on the root URL (`/`) containing active database stats, status indicators, and live server uptime.

---

## 📂 Project Structure

```
├── .env                  # Local credentials & configs (git-ignored)
├── .env.template         # Template for environment configurations
├── .gitignore            # Git ignore list (protects credentials and virtual env)
├── connection.py         # DB connection builder, context managers, and db dependencies via pymssql
├── endpoints.py          # Custom FastAPI Router file containing configs and SERP rank tracker endpoints
├── main.py               # FastAPI App, Lifespan controller, server home UI, and server runner
├── schema.sql            # Database schema and seed script for local SQL Server initialization
├── requirements.txt      # PyPI project dependencies
├── test_connection.py    # Diagnostic script for quick terminal checks
└── README.md             # This guide
```

---

## 🛠️ Getting Started

### 1. Prerequisites

Ensure you have Python installed, along with Microsoft's SQL Server ODBC drivers.
- If needed, download the drivers here: [Microsoft ODBC Driver for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server).

### 2. Initialize Database Schema

Before starting the server, run the [schema.sql](file:///d:/Projects/GenerativeSSO/Python_KeyWordRankTracker/schema.sql) initialization script on your SQL Server database. This script will:
1. Safely check if the `api_config` and `serp_rank_tracker` tables exist and create them if not.
2. Seed diagnostic configurations (including the active `HasData` API key) for immediate testing.

### 3. Configure Database Credentials

Open the **`.env`** file at the root level and fill in your database variables:

```env
DB_SERVER=your-server-name.database.windows.net
DB_PORT=1433
DB_DATABASE=your-database-name
DB_USE_WINDOWS_AUTH=false
DB_USERNAME=your-username
DB_PASSWORD=your-password
```

---

## 💻 Running the Application Locally

### 1. Run Diagnostic Script (Optional)
To verify database access quickly via the terminal without running the API server:
```bash
.venv\Scripts\python.exe test_connection.py
```

### 2. Run the API Server
Start the Uvicorn-powered FastAPI server:
```bash
.venv\Scripts\python.exe main.py
```

Once running, open your browser and navigate to:
- **Status Dashboard (HTML)**: `http://127.0.0.1:8000/`
- **Interactive API Documentation (Swagger)**: `http://127.0.0.1:8000/docs`

---

## ☁️ Deploying to Render

We use **`pymssql`** to manage database connections. Unlike `pyodbc`, it bundles its own drivers and runs out-of-the-box on Render's native high-performance Python environment without requiring Docker or custom system drivers.

To deploy:
1. In the Render Dashboard, click **New** -> **Blueprint**.
2. Connect your Git repository.
3. Render will automatically parse [render.yaml](file:///d:/Projects/GenerativeSSO/Python_KeyWordRankTracker/render.yaml), set up the Python environment, configure your environment variables, and start the app successfully.

---

## 🔌 API Endpoints Reference

Exposed from [endpoints.py](file:///d:/Projects/GenerativeSSO/Python_KeyWordRankTracker/endpoints.py):

### 1. Keyword Rank Tracker (`/api/keywords`)

* **`POST /api/keywords/serp-rankings`**: Receives an array of keyword rank tracker tasks, queries Google Search Console or HasData API for the first 50 results, parses position ranks, checks SQL Server history, and inserts/updates historical metrics.
  
  **Request Payload JSON Structure (with Geolocation Support)**:
  ```json
  [
    {
      "email": "k.kargutkar26@gmail.com",
      "domain": "https://www.evtechinstitute.com",
      "keyword": ["ev tech institute", "best", "institute"],
      "gl": "in",
      "hl": "en",
      "google_domain": "google.co.in",
      "location": "Vasai,Maharashtra,India"
    }
  ]
  ```

  **Rank Matching Details & Geolocation**:
  - **The Geolocation Problem**: Google Search is highly localized. If a user in India searches "ev institute", they see localized Indian results where local centers rank #1. If an API queries from a US server, they see US-focused results where local Indian centers are unranked.
  - **The Geolocation Solution**: The API now dynamically passes country code (`gl`), language (`hl`), Google domain (`google_domain`), and detailed location coordinates (`location`) to the HasData Google SERP API, ensuring exact local ranking parity.
  - **Intelligent Defaults**: Defaults to `gl="in"`, `hl="en"`, and `google_domain="google.co.in"` to automatically capture local Indian search rankings out of the box!
  - **Position Tracking**: 
    - **If found**: Updates or creates the record in `serp_rank_tracker` with its actual position (1 to 50).
    - **If not found**: Sets `current_position` to **`51`** (representing unranked / rank > 50).
    - **Previous Position**: If no previous ranking history exists in the database, `previous_position` defaults to **`51`**.
    - **Timestamping**: Automatically updates `updated_at = GETDATE()` when saving existing tracker records in the database.

  **Response JSON Structure**:
  ```json
  [
    {
      "email": "k.kargutkar26@gmail.com",
      "domain": "https://www.evtechinstitute.com",
      "keyword_tracking": [
        {
          "keyword": "ev tech institute",
          "status": "FOUND",
          "current_position": 1,
          "previous_position": 51,
          "matched_url": "https://www.evtechinstitute.com/"
        },
        {
          "keyword": "best",
          "status": "NOT_FOUND",
          "current_position": 51,
          "previous_position": 51,
          "matched_url": null
        }
      ]
    }
  ]
  ```

### 2. API Configurations Manager (`/api/configs`)
* **`GET /api/configs/`**: Fetch all api config records.
  - **Query Filters**: 
    - `status`: Filter by status (e.g., `ACTIVE`, `INACTIVE`)
    - `provider`: Search provider name (case-insensitive, wildcard-matching)
  - **Response (Safe)**: Excludes plain text passwords and secret authentication keys automatically using Pydantic serializers.

### 3. Health & System Diagnostics
* **`GET /api/health`**: Verifies dynamic connectivity to SQL Server and returns server uptime.
* **`GET /api/db-info`**: Displays database engine properties, metadata, and default collation configurations.
* **`GET /api/query-test`**: Developer sandbox to run custom parameterized queries (restricted to read-only `SELECT` statements).
