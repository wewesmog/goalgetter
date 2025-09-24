import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
from app.mcp.db_tools_mcp import run_server

#

if __name__ == "__main__":
    print("Starting Goalgetter MCP server... v3.0")
    run_server()
    
    # # Check if running in Railway (production) or locally
    # if os.getenv("RAILWAY_ENVIRONMENT"):
    #     # Production: Run as web server
    #     port = int(os.getenv("PORT", 8000))
    #     host = "0.0.0.0"
        
    #     print(f"🚀 Production mode: Starting web server on {host}:{port}")
    #     print(f"  - API docs: http://localhost:{port}/docs")
    #     print(f"  - Tools endpoint: http://localhost:{port}/tools")
        
    #     uvicorn.run(app, host=host, port=port)
    # else:
    #     # Local development: Run in stdio mode
    #     print("🏠 Local development mode: Starting stdio MCP server")
    #     print("  - Available for stdio connections")
        
    #     # Run the MCP server in stdio mode
    #     run_server()