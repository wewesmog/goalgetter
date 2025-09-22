import os
import uvicorn
from app.mcp.db_tools_mcp import mcp

# Expose the FastAPI app for Railway deployment
app = mcp.app

if __name__ == "__main__":
    print("Starting Goalgetter MCP server...")
    
    # Always run as web server (HTTPS on Railway, HTTP locally)
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"Starting web server on {host}:{port}")
    print("MCP server will be available at:")
    print(f"  - Local: http://localhost:{port}")
    print(f"  - Railway: https://your-app.railway.app")
    print(f"  - API docs: http://localhost:{port}/docs")
    
    uvicorn.run(app, host=host, port=port)