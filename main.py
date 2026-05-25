import time
import os
import sys
import logging
import asyncio
from contextlib import asynccontextmanager
import pymssql
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
import uvicorn

from connection import db_manager, logger, get_db_cursor

# Ensure logs are visible
logger.setLevel(logging.INFO)

# Define lifespan event handler for DB connection persistence and verification
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the lifecycle of the FastAPI application.
    Establishes and verifies database connection before starting the server.
    """
    logger.info("Initializing application startup...")
    
    # 1. Establish and verify SQL Server connection before starting the server
    persistent_conn = None
    try:
        logger.info(f"Connecting to SQL Server database '{db_manager.database}'...")
        
        # Synchronous pymssql connection run in an executor to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        persistent_conn = await loop.run_in_executor(None, db_manager.get_raw_connection)
        
        # Test connection validity
        cursor = persistent_conn.cursor()
        cursor.execute("SELECT @@VERSION;")
        version = cursor.fetchone()[0]
        cursor.close()
        
        logger.info("[SUCCESS] Connected to SQL Server database successfully!")
        logger.info(f"Database Server Version: {version.splitlines()[0]}")
        
        # Store persistent connection and startup time in app state
        app.state.db_conn = persistent_conn
        app.state.startup_time = time.time()
        app.state.db_connected = True
        app.state.db_version = version
        
    except Exception as e:
        logger.error(f"[FATAL] Failed to establish database connection during startup: {e}")
        logger.error("Aborting application startup!")
        # Raising exception here will abort the server startup
        raise RuntimeError(f"Database connection failed: {e}") from e

    # 2. Server is active and accepting requests
    yield
    
    # 3. Clean up database connection on shutdown
    logger.info("Initializing application shutdown...")
    if persistent_conn:
        try:
            persistent_conn.close()
            logger.info("Persistent database connection closed successfully.")
        except Exception as e:
            logger.error(f"Error closing database connection during shutdown: {e}")

# Initialize FastAPI app with beautiful metadata and custom lifespan
app = FastAPI(
    title="GenerativeSEO Keyword Rank Tracker API",
    description="🚀 High-performance API powered by FastAPI, Uvicorn, and Microsoft SQL Server.",
    version="1.0.0",
    lifespan=lifespan
)

# Register API routers
from endpoints import configs_router, rankings_router
app.include_router(configs_router, prefix="/api")
app.include_router(rankings_router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def home_page():
    """
    Stunning, premium, interactive home page with modern aesthetics, HSL color palette,
    glassmorphism, and live connection status.
    """
    uptime = int(time.time() - app.state.startup_time)
    hours, remainder = divmod(uptime, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours:02d}h {minutes:02d}m {seconds:02d}s"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SQL Server API Status</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg-gradient-start: #0f172a;
                --bg-gradient-end: #020617;
                --accent-primary: #38bdf8;
                --accent-secondary: #818cf8;
                --card-bg: rgba(30, 41, 59, 0.4);
                --card-border: rgba(255, 255, 255, 0.08);
                --text-primary: #f8fafc;
                --text-secondary: #94a3b8;
                --status-green: #10b981;
            }}

            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}

            body {{
                font-family: 'Outfit', sans-serif;
                background: linear-gradient(135deg, var(--bg-gradient-start), var(--bg-gradient-end));
                color: var(--text-primary);
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                padding: 2rem;
                overflow-x: hidden;
            }}

            /* Dynamic Background Blobs */
            .blob {{
                position: absolute;
                width: 400px;
                height: 400px;
                border-radius: 50%;
                filter: blur(100px);
                z-index: -1;
                opacity: 0.15;
                animation: float 20s infinite ease-in-out alternate;
            }}
            .blob-1 {{
                background: var(--accent-primary);
                top: 10%;
                left: 15%;
            }}
            .blob-2 {{
                background: var(--accent-secondary);
                bottom: 10%;
                right: 15%;
                animation-delay: -10s;
            }}

            @keyframes float {{
                0% {{ transform: translate(0, 0) scale(1); }}
                100% {{ transform: translate(50px, 50px) scale(1.2); }}
            }}

            /* Main Glassmorphic Container */
            .container {{
                background: var(--card-bg);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border: 1px solid var(--card-border);
                border-radius: 24px;
                padding: 3rem;
                max-width: 800px;
                width: 100%;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }}
            .container:hover {{
                transform: translateY(-4px);
                box-shadow: 0 30px 60px -10px rgba(56, 189, 248, 0.15);
            }}

            header {{
                text-align: center;
                margin-bottom: 2.5rem;
            }}

            h1 {{
                font-weight: 800;
                font-size: 2.5rem;
                letter-spacing: -1px;
                background: linear-gradient(to right, var(--accent-primary), var(--accent-secondary));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.5rem;
            }}

            .subtitle {{
                font-size: 1.1rem;
                color: var(--text-secondary);
            }}

            /* Status Grid */
            .grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1.5rem;
                margin-bottom: 2.5rem;
            }}

            @media(max-width: 600px) {{
                .grid {{
                    grid-template-columns: 1fr;
                }}
            }}

            .card {{
                background: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 16px;
                padding: 1.5rem;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                position: relative;
                overflow: hidden;
            }}

            .card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 4px;
                height: 100%;
                background: var(--accent-primary);
            }}
            .card-status::before {{
                background: var(--status-green);
            }}

            .card-title {{
                font-size: 0.9rem;
                text-transform: uppercase;
                letter-spacing: 1px;
                color: var(--text-secondary);
                margin-bottom: 0.75rem;
                font-weight: 600;
            }}

            .card-value {{
                font-size: 1.5rem;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}

            .pulse-dot {{
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background-color: var(--status-green);
                box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
                animation: pulse 1.6s infinite;
            }}

            @keyframes pulse {{
                0% {{
                    transform: scale(0.95);
                    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
                }}
                70% {{
                    transform: scale(1);
                    box-shadow: 0 0 0 8px rgba(16, 185, 129, 0);
                }}
                100% {{
                    transform: scale(0.95);
                    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
                }}
            }}

            /* Action Buttons & Docs Links */
            .actions {{
                display: flex;
                justify-content: center;
                gap: 1rem;
                margin-top: 1rem;
            }}

            .btn {{
                display: inline-block;
                padding: 0.8rem 1.8rem;
                border-radius: 12px;
                font-weight: 600;
                text-decoration: none;
                transition: all 0.2s ease;
                font-size: 1rem;
                cursor: pointer;
            }}

            .btn-primary {{
                background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
                color: var(--bg-gradient-end);
                border: none;
            }}
            .btn-primary:hover {{
                transform: translateY(-2px);
                box-shadow: 0 10px 20px -5px rgba(56, 189, 248, 0.4);
            }}

            .btn-secondary {{
                background: rgba(255, 255, 255, 0.05);
                color: var(--text-primary);
                border: 1px solid var(--card-border);
            }}
            .btn-secondary:hover {{
                background: rgba(255, 255, 255, 0.1);
                transform: translateY(-2px);
            }}

            footer {{
                margin-top: 3rem;
                font-size: 0.85rem;
                color: var(--text-secondary);
                text-align: center;
            }}

            code {{
                font-family: 'JetBrains Mono', monospace;
                background: rgba(0, 0, 0, 0.2);
                padding: 0.2rem 0.4rem;
                border-radius: 6px;
                font-size: 0.9rem;
            }}
        </style>
    </head>
    <body>
        <div class="blob blob-1"></div>
        <div class="blob blob-2"></div>

        <div class="container">
            <header>
                <h1>GenerativeSEO Rank Tracker API</h1>
                <p class="subtitle">FastAPI & Uvicorn connection engine for Microsoft SQL Server</p>
            </header>

            <div class="grid">
                <div class="card card-status">
                    <span class="card-title">Database Status</span>
                    <div class="card-value">
                        <div class="pulse-dot"></div>
                        Connected
                    </div>
                </div>
                <div class="card">
                    <span class="card-title">API Uptime</span>
                    <div class="card-value">{uptime_str}</div>
                </div>
                <div class="card">
                    <span class="card-title">Connected Server</span>
                    <div class="card-value" style="font-size: 1.1rem; word-break: break-all;">
                        <code>{db_manager.server}</code>
                    </div>
                </div>
                <div class="card">
                    <span class="card-title">Active Database</span>
                    <div class="card-value" style="font-size: 1.1rem;">
                        <code>{db_manager.database}</code>
                    </div>
                </div>
            </div>

            <div class="actions">
                <a href="/docs" class="btn btn-primary">Interactive Swagger Docs</a>
                <a href="/api/health" class="btn btn-secondary">API Health Status</a>
            </div>

            <footer>
                Using Driver: <code>{db_manager.driver}</code> • Python 3.11.9
            </footer>
        </div>
    </body>
    </html>
    """
    return html_content

@app.get("/api/health")
async def health_check():
    """
    System and database connection health endpoint.
    """
    is_db_connected = False
    db_details = {}
    
    try:
        # Check active status using standard command
        conn = app.state.db_conn
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        res = cursor.fetchone()[0]
        cursor.close()
        
        if res == 1:
            is_db_connected = True
            db_details = {
                "server": db_manager.server,
                "database": db_manager.database,
                "driver": db_manager.driver,
                "windows_auth": db_manager.use_windows_auth
            }
    except Exception as e:
        logger.error(f"Health check database ping failed: {e}")
        is_db_connected = False

    return {
        "status": "healthy" if is_db_connected else "unhealthy",
        "api_active": True,
        "database_connected": is_db_connected,
        "database_details": db_details,
        "uptime_seconds": int(time.time() - app.state.startup_time)
    }

@app.get("/api/db-info")
async def get_db_info(cursor = Depends(get_db_cursor)):
    """
    Secure endpoint querying advanced database configuration details using connection pool.
    """
    try:
        cursor.execute("SELECT @@VERSION;")
        version = cursor.fetchone()[0]
        
        cursor.execute("SELECT DB_NAME();")
        db_name = cursor.fetchone()[0]
        
        # Querying collation
        cursor.execute("SELECT DATABASEPROPERTYEX(DB_NAME(), 'Collation') AS Collation;")
        collation = cursor.fetchone()[0]
        
        return {
            "database_name": db_name,
            "sql_server_version": version,
            "default_collation": collation,
            "driver_name": db_manager.driver
        }
    except Exception as e:
        logger.error(f"Error querying database info: {e}")
        raise HTTPException(status_code=500, detail=f"Database metadata query failed: {str(e)}")

@app.get("/api/query-test")
async def query_test(
    sql: str = Query("SELECT @@VERSION", description="Safe test query to execute"),
    cursor = Depends(get_db_cursor)
):
    """
    Allows executing general utility diagnostic SELECT statements (read-only by recommendation).
    """
    # Restrict to SELECT queries for security safety
    clean_sql = sql.strip().upper()
    if not clean_sql.startswith("SELECT"):
        raise HTTPException(
            status_code=400, 
            detail="Security Policy: Only SELECT statements are permitted via this diagnostic endpoint."
        )
        
    try:
        cursor.execute(sql)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            # Map row elements to columns
            results.append(dict(zip(columns, row)))
            
        return {
            "sql_executed": sql,
            "row_count": len(results),
            "columns": columns,
            "data": results
        }
    except Exception as e:
        logger.error(f"Error executing diagnostic SQL '{sql}': {e}")
        raise HTTPException(status_code=500, detail=f"SQL Execution error: {str(e)}")

# CLI server launcher
def start_server():
    """
    Launches Uvicorn server programmatically.
    Dynamically binds to the correct HOST and PORT for Render/Production deployment.
    """
    # Render sets the PORT environment variable. We default to 8000 for local development.
    port = int(os.getenv("PORT", 8000))
    # Render requires binding to 0.0.0.0 so external traffic can route to the container.
    host = os.getenv("HOST", "0.0.0.0" if os.getenv("RENDER") else "127.0.0.1")
    # Disable reload in production/Render to optimize performance
    reload = os.getenv("RENDER") is None
    
    logger.info(f"Starting server on {host}:{port} (reload={reload})")
    uvicorn.run("main:app", host=host, port=port, reload=reload)

if __name__ == "__main__":
    start_server()

