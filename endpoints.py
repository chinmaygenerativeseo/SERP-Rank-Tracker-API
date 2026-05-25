from typing import List, Optional
from datetime import datetime
import asyncio
import http.client
import urllib.parse
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from connection import logger, get_db_cursor

# Initialize Routers
configs_router = APIRouter(
    prefix="/configs",
    tags=["API Configurations"]
)

rankings_router = APIRouter(
    prefix="/keywords",
    tags=["Keyword Rank Tracker"]
)

# Pydantic Schemas for validation and response serialization
class APIConfigBase(BaseModel):
    api_provider: str = Field(..., description="Name of the API provider (e.g., Google, OpenAI, SEMrush)")
    api_provider_username: Optional[str] = Field(None, description="Username associated with the provider")
    base_url: str = Field(..., description="Base API endpoint URL")
    auth_type: str = Field(..., description="Authentication standard: API_KEY, BEARER, BASIC, or OAUTH2")
    api_description: Optional[str] = Field(None, description="Short summary/description of the API configuration")
    status: str = Field("ACTIVE", description="Operating status (e.g., ACTIVE, INACTIVE)")

class APIConfigCreate(APIConfigBase):
    api_provider_password: Optional[str] = Field(None, description="Password associated with the provider")
    auth_key: Optional[str] = Field(None, description="API token, Key, or Bearer auth secret")

class APIConfigResponse(APIConfigBase):
    api_config_id: int = Field(..., description="Database Primary Key")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- ROUTE 1: Fetch all API Configurations with optional filtering ---
@configs_router.get("/", response_model=List[APIConfigResponse], summary="Fetch API Configurations")
async def get_api_configurations(
    status: Optional[str] = Query(None, description="Filter configurations by status (e.g., ACTIVE, INACTIVE)"),
    provider: Optional[str] = Query(None, description="Filter configurations by API provider name (case-insensitive)"),
    cursor = Depends(get_db_cursor)
):
    """
    Retrieves configurations from the `api_config` table in SQL Server.
    Allows filtering by status and searching by provider name.
    """
    logger.info("Fetching API configurations from 'api_config' table.")
    
    query = """
        SELECT 
            api_config_id, 
            api_provider, 
            api_provider_username, 
            base_url, 
            auth_type, 
            api_description, 
            status, 
            created_at, 
            updated_at 
        FROM api_config
    """
    
    where_clauses = []
    params = []
    
    if status:
        where_clauses.append("status = %s")
        params.append(status)
        
    if provider:
        where_clauses.append("api_provider LIKE %s")
        params.append(f"%{provider}%")

        
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
        
    query += " ORDER BY created_at DESC"
    
    try:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        
        configs = []
        for row in rows:
            row_dict = dict(zip(columns, row))
            configs.append(row_dict)
            
        logger.info(f"Retrieved {len(configs)} configuration records.")
        return configs
        
    except Exception as e:
        logger.error(f"Error querying 'api_config' table: {e}")
        err_msg = str(e)
        if "Invalid object name" in err_msg or "does not exist" in err_msg:
            raise HTTPException(
                status_code=404, 
                detail="Table 'api_config' not found in database. Please run the SQL schema creation script first."
            )
        raise HTTPException(
            status_code=500, 
            detail=f"Database query execution failed: {err_msg}"
        )

# Pydantic Schemas for SERP Rank Tracker request validation
class KeywordRankTrackerRequest(BaseModel):
    email: str = Field(..., description="Email address of the keyword tracker subscriber")
    domain: str = Field(..., description="Target domain link to search for (e.g., https://www.evtechinstitute.com)")
    keyword: List[str] = Field(..., description="List of keyword strings to monitor in Google Search")
    gl: Optional[str] = Field("in", description="Country code (e.g., 'in' for India, 'us' for US)")
    hl: Optional[str] = Field("en", description="Language code (e.g., 'en' for English)")
    google_domain: Optional[str] = Field("google.co.in", description="Google search domain (e.g., 'google.co.in', 'google.com')")
    location: Optional[str] = Field(None, description="Detailed physical location (e.g., 'Vasai,Maharashtra,India')")


# --- ROUTE 2: Track Keyword SERP rankings and update DB ---
@rankings_router.post("/serp-rankings", summary="Track SERP Rank via Keywords and Update Database")
async def track_keyword_serp_rankings(
    payload: List[KeywordRankTrackerRequest],
    cursor = Depends(get_db_cursor)
):
    """
    Receives a list of domain and keyword tracking requests.
    For each keyword:
      1. Queries the DB to load HasData credentials (or applies standard fallbacks).
      2. Dispatches a call to the HasData Google SERP API.
      3. Scans organic search results to check if the target domain exists in the first 50 results.
      4. Pulls previous historical position from the `serp_rank_tracker` table.
      5. Inserts a new record (prev=0) or updates the existing tracking record in the SQL Server database.
    """
    logger.info(f"Received bulk SERP rank tracking request for {len(payload)} domains.")
    
    # 1. Fetch active HasData credentials from the DB
    base_url = None
    auth_key = None
    try:
        query = """
            SELECT TOP 1 base_url, auth_key 
            FROM api_config 
            WHERE (api_provider LIKE '%HasData%' OR base_url LIKE '%hasdata%') AND status = 'ACTIVE'
            ORDER BY created_at DESC
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result:
            base_url = result[0]
            auth_key = result[1]
            logger.info("Found active HasData configuration in the database.")
        else:
            logger.warning("No active HasData configuration found in the database. Using fallback credentials.")
            
    except Exception as e:
        logger.error(f"Error querying HasData configuration from database: {e}")
        
    # Apply default fallbacks if database entry is not available
    if not base_url:
        base_url = "api.hasdata.com"
    if not auth_key:
        auth_key = "2dea73c2-6a8f-4b74-a45d-404d0f24a558"
        
    # Clean and parse hostname
    clean_url = base_url if "://" in base_url else f"https://{base_url}"
    parsed_url = urllib.parse.urlparse(clean_url)
    host = parsed_url.hostname or "api.hasdata.com"
    
    # Helper: Extract clean domain string to avoid www/non-www/protocol mismatches
    def extract_clean_domain(url_str: str) -> str:
        try:
            url_str = url_str.strip().lower()
            if not url_str.startswith(("http://", "https://")):
                url_str = "https://" + url_str
            parsed = urllib.parse.urlparse(url_str)
            netloc = parsed.netloc
            if netloc.startswith("www."):
                netloc = netloc[4:]
            return netloc
        except Exception:
            return url_str.lower()
            
    # Process requests
    overall_results = []
    
    for item in payload:
        target_email = item.email
        target_domain_raw = item.domain
        target_domain_clean = extract_clean_domain(target_domain_raw)
        keywords = item.keyword
        
        domain_results = []
        
        for kw in keywords:
            logger.info(f"Tracking keyword '{kw}' for domain '{target_domain_raw}' ({target_domain_clean})")
            
            # Formulate query params and path (dynamically localizing results via gl, hl, domain, and location)
            # (Note: we use num=50 to fetch the first 50 organic results as requested)
            params = {
                "q": kw,
                "domain": item.google_domain or "google.co.in",
                "gl": item.gl or "in",
                "hl": item.hl or "en",
                "deviceType": "desktop",
                "num": 50
            }
            if item.location:
                params["location"] = item.location
                
            encoded_params = urllib.parse.urlencode(params)
            request_path = f"/scrape/google/serp?{encoded_params}"
            
            headers = {
                'x-api-key': auth_key,
                'Content-Type': "application/json"
            }
            
            # Sync HTTP call wrapper for thread pool offloading
            def perform_api_call():
                conn = None
                try:
                    conn = http.client.HTTPSConnection(host, timeout=30)
                    conn.request("GET", request_path, headers=headers)
                    res = conn.getresponse()
                    status_code = res.status
                    body = res.read().decode("utf-8")
                    return status_code, body
                except Exception as api_err:
                    logger.error(f"Failed external API request for keyword '{kw}': {api_err}")
                    raise RuntimeError(f"External API communication failure: {api_err}")
                finally:
                    if conn:
                        conn.close()
            
            try:
                # Offload call to thread to prevent blocking event loop
                status, response_body = await asyncio.to_thread(perform_api_call)
                
                if status != 200:
                    logger.error(f"External API returned non-200 code: {status} for keyword '{kw}'")
                    domain_results.append({
                        "keyword": kw,
                        "status": "API_ERROR",
                        "details": f"External API returned HTTP status {status}"
                    })
                    continue
                    
                # Parse JSON
                serp_data = json.loads(response_body)
                organic_results = serp_data.get("organicResults", [])
                
                # Check if target domain is present in organic results (top 50 positions)
                found_position = 51 # Default to 51 (representing not found / rank > 50)
                matched_link = None
                
                for r in organic_results:
                    pos = r.get("position", 0)
                    link = r.get("link", "")
                    displayed_link = r.get("displayedLink", "")
                    
                    link_clean = extract_clean_domain(link)
                    displayed_clean = extract_clean_domain(displayed_link)
                    
                    # Match if target domain matches or is part of result domain
                    if (target_domain_clean in link_clean or 
                        target_domain_clean in displayed_clean or 
                        target_domain_clean in link.lower()):
                        found_position = pos
                        matched_link = link
                        break
                
                # 3. Handle DB persistence (Insert or Update serp_rank_tracker)
                previous_pos = 51 # Default to 51 if not found previously
                
                # Check if a tracker record already exists
                check_query = """
                    SELECT current_position 
                    FROM serp_rank_tracker 
                    WHERE domain = %s AND keyword = %s
                """
                cursor.execute(check_query, (target_domain_raw, kw))
                db_record = cursor.fetchone()
                
                if db_record:
                    # Update existing record
                    previous_pos = db_record[0]
                    # Ensure backward compatibility: convert any old 0 value to 51
                    if previous_pos == 0:
                        previous_pos = 51
                        
                    update_query = """
                        UPDATE serp_rank_tracker
                        SET previous_position = %s,
                            current_position = %s,
                            updated_at = GETDATE()
                        WHERE domain = %s AND keyword = %s
                    """
                    cursor.execute(update_query, (previous_pos, found_position, target_domain_raw, kw))
                    logger.info(f"Updated rank tracker for '{kw}': Prev={previous_pos}, Curr={found_position}")
                else:
                    # Insert new record (previous_position defaults to 51)
                    insert_query = """
                        INSERT INTO serp_rank_tracker (domain, keyword, current_position, previous_position)
                        VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (target_domain_raw, kw, found_position, 51))
                    logger.info(f"Inserted new rank tracker for '{kw}': Position={found_position}")
                
                domain_results.append({
                    "keyword": kw,
                    "status": "FOUND" if found_position <= 50 else "NOT_FOUND",
                    "current_position": found_position,
                    "previous_position": previous_pos,
                    "matched_url": matched_link
                })
                
            except Exception as kw_err:
                logger.error(f"Error processing keyword '{kw}': {kw_err}")
                domain_results.append({
                    "keyword": kw,
                    "status": "ERROR",
                    "details": str(kw_err)
                })
                
        overall_results.append({
            "email": target_email,
            "domain": target_domain_raw,
            "keyword_tracking": domain_results
        })
        
    return overall_results

