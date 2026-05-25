import logging
from connection import db_manager, logger

def run_diagnostics():
    """
    Tests the connection to SQL Server and outputs diagnostic information.
    """
    print("\n" + "="*60)
    print("      SQL SERVER CONNECTION DIAGNOSTICS & TEST")
    print("="*60)
    
    print(f"\n[1] Configuration Summary:")
    print(f"  - Target Server:      {db_manager.server}")
    print(f"  - Target Port:        {db_manager.port}")
    print(f"  - Target Database:    {db_manager.database}")
    print(f"  - Windows Auth Mode:  {db_manager.use_windows_auth}")
    print(f"  - Username:           {db_manager.username if not db_manager.use_windows_auth else 'N/A (Windows Auth)'}")
    print(f"  - Detected Driver:    {db_manager.driver}")
    print(f"  - Encrypt:            {db_manager.encrypt}")
    print(f"  - Trust Certificate:  {db_manager.trust_server_certificate}")
    
    print(f"\n[2] Attempting to connect to SQL Server...")
    
    try:
        # Get connection and cursor via context manager
        with db_manager.get_cursor() as cursor:
            print("  [SUCCESS] Successfully connected to SQL Server!")
            
            # Execute simple standard diagnostic query
            print("\n[3] Running diagnostic query (SELECT @@VERSION)...")
            cursor.execute("SELECT @@VERSION;")
            db_version = cursor.fetchone()
            
            print(f"\n[RESULT] SQL Server Version Information:")
            print("-" * 60)
            print(db_version[0])
            print("-" * 60)
            
            # Check current database name to verify context
            cursor.execute("SELECT DB_NAME();")
            current_db = cursor.fetchone()[0]
            print(f"  - Current database context: {current_db}")
            
    except Exception as e:
        print(f"\n[ERROR] Connection or Query execution failed!")
        print(f"Details: {e}")
        print("\nTroubleshooting Steps:")
        print("  1. Verify the SQL Server service is running and accepting remote connections.")
        print("  2. Check if your Server Name, Database Name, and Credentials in `.env` are correct.")
        print("  3. Check if your network/firewall allows access to port 1433 (or custom port).")
        print("  4. If using SQL Authentication, verify the SQL Server authentication mode is 'Mixed Mode'.")
        print("  5. If you see 'SSL Provider: The certificate chain was issued by an authority that is not trusted',")
        print("     ensure DB_TRUST_SERVER_CERTIFICATE=yes is set in your `.env` file.")
        
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    # Temporarily set logs to INFO to show driver auto-detect status
    logger.setLevel(logging.INFO)
    run_diagnostics()
