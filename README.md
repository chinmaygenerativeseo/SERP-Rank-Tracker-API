# Python SQL Server Connection & API Bootstrapper

A robust, production-ready, and high-performance **FastAPI** web API integrated with **Microsoft SQL Server** (supporting Azure SQL Database, managed instances, and local SQL Server installations).

---

## 🚀 Key Features

- **Sequential Connection Startup**: Verifies and establishes the database connection **before** starting the web server. If the connection fails, startup is safely aborted to prevent running a broken API server.
- **Persistent Connection Lifecycle**: Uses a modern FastAPI `lifespan` manager to maintain a persistent connection state (`app.state.db_conn`) while the server is active, gracefully closing it upon server shutdown.
- **High-Performance Pooling & Non-Blocking Async**: Implements dependency injection for standard database queries using native ODBC connection pooling and offloads external blocking API HTTP calls to `asyncio.to_thread` pools.
- **Dedicated Route Files**: Clean architecture separating endpoints into [endpoints.py](file:///d:/Projects/GenerativeSSO/Python_KeyWordRankTracker/endpoints.py) for easy maintenance.
- **Auto-Driver Detection**: Scans the OS dynamically for the latest installed SQL Server ODBC driver.
- **Vibrant Status UI**: Serves a beautiful, glassmorphic welcome page on the root URL (`/`) containing active database stats, status indicators, and live server uptime.

---

## 📂 Project Structure

```
├── .env                  # Local credentials & configs (git-ignored)
├── .env.template         # Template for environment configurations
├── .gitignore            # Git ignore list (protects credentials and virtual env)
├── connection.py         # DB connection builder, driver scanner, context managers, and db dependencies
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

## 💻 Running the Application

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

## 🔌 API Endpoints Reference

Exposed from [endpoints.py](file:///d:/Projects/GenerativeSSO/Python_KeyWordRankTracker/endpoints.py):

### 1. Keyword Rank Tracker (`/api/keywords`)

* **`POST /api/keywords/serp-rankings`**: Receives an array of keyword rank tracker tasks, queries Google Search Console or HasData API for the first 50 results, parses position ranks, checks SQL Server history, and inserts/updates historical metrics.
  
  **Request Payload JSON Structure**:
  ```json
  [
    {
      "email": "k.kargutkar26@gmail.com",
      "domain": "https://www.evtechinstitute.com",
      "keyword": ["ev tech institute", "best", "institute"]
    }
  ]
  ```

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
          "previous_position": 0,
          "matched_url": "https://www.evtechinstitute.com/"
        },
        {
          "keyword": "best",
          "status": "NOT_FOUND",
          "current_position": 0,
          "previous_position": 0,
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
