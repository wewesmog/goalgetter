import os
import uvicorn
from fastapi import FastAPI
from app.mcp.db_tools_mcp import mcp

# Create FastAPI app and mount MCP server
app = FastAPI(title="Goalgetter MCP Server", version="1.0.0")

# Mount the MCP server
app.mount("/mcp", mcp.app)

@app.get("/")
async def root():
    return {
        "message": "Goalgetter MCP Server",
        "version": "1.0.0",
        "mcp_endpoint": "/mcp",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "goalgetter-mcp"}

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
    print(f"  - MCP endpoint: http://localhost:{port}/mcp")
    
    uvicorn.run(app, host=host, port=port)