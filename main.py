import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
from app.mcp.db_tools_mcp import mcp

# Create FastAPI app 
app = FastAPI(title="Goalgetter MCP Server", version="1.0.0")

@app.get("/")
async def root():
    return {
        "message": "Goalgetter MCP Server",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "goalgetter-mcp"}

# Add MCP tools as FastAPI endpoints
@app.post("/tools/{tool_name}")
async def call_mcp_tool(tool_name: str, payload: Dict[str, Any]):
    """Call MCP tools via HTTP endpoints."""
    try:
        # Get the tool from the MCP server
        tools = mcp.list_tools()
        
        # Find the requested tool
        tool_func = None
        for tool in tools:
            if tool.name == tool_name:
                tool_func = getattr(mcp, tool_name, None)
                break
        
        if not tool_func:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        # Call the tool with the payload
        result = await tool_func(**payload)
        return {"success": True, "result": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools")
async def list_tools():
    """List available MCP tools."""
    try:
        tools = mcp.list_tools()
        return {"tools": [{"name": tool.name, "description": tool.description} for tool in tools]}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("Starting Goalgetter MCP server... v3.0")
    
    # Always run as web server (HTTPS on Railway, HTTP locally)
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"Starting web server on {host}:{port}")
    print("MCP server will be available at:")
    print(f"  - Local: http://localhost:{port}")
    print(f"  - Railway: https://your-app.railway.app")
    print(f"  - API docs: http://localhost:{port}/docs")
    print(f"  - Tools endpoint: http://localhost:{port}/tools")
    
    uvicorn.run(app, host=host, port=port)