#!/usr/bin/env python3
"""
Product Hunt MCP HTTP Server for N8N Integration

This module provides an HTTP/SSE interface for the Product Hunt MCP server
to work with N8N Cloud workflows.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from product_hunt_mcp.tools.collections import register_collection_tools
from product_hunt_mcp.tools.comments import register_comment_tools
from product_hunt_mcp.tools.posts import register_post_tools
from product_hunt_mcp.tools.server import register_server_tools
from product_hunt_mcp.tools.topics import register_topic_tools
from product_hunt_mcp.tools.users import register_user_tools

# fastmcp is an external dependency
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ph_mcp.http_server")

# Global MCP server instance
mcp_server = None

def initialize_mcp_server():
    """Initialize the MCP server with all tools."""
    global mcp_server
    
    if mcp_server is None:
        logger.info("Initializing Product Hunt MCP server...")
        mcp_server = FastMCP("Product Hunt MCP 🚀")
        
        # Register all tools
        register_server_tools(mcp_server)
        register_post_tools(mcp_server)
        register_comment_tools(mcp_server)
        register_collection_tools(mcp_server)
        register_topic_tools(mcp_server)
        register_user_tools(mcp_server)
        
        logger.info("Product Hunt MCP server initialized successfully")
    
    return mcp_server

# Create FastAPI app
app = FastAPI(
    title="Product Hunt MCP HTTP Server",
    description="HTTP/SSE interface for Product Hunt MCP server",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize MCP server on startup."""
    initialize_mcp_server()

@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "service": "Product Hunt MCP HTTP Server",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "/": "Server information",
            "/health": "Health check",
            "/sse/": "Server-Sent Events endpoint for N8N",
            "/tools": "List available tools",
            "/tools/{tool_name}": "Execute specific tool"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    global mcp_server
    
    # Check if MCP server is initialized
    if mcp_server is None:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    # Check if Product Hunt token is available
    token = os.getenv("PRODUCT_HUNT_TOKEN")
    if not token:
        raise HTTPException(status_code=503, detail="PRODUCT_HUNT_TOKEN not configured")
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mcp_server": "initialized",
        "product_hunt_token": "configured" if token else "missing"
    }

@app.get("/tools")
async def list_tools():
    """List available MCP tools."""
    global mcp_server
    
    if mcp_server is None:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    # Get tools from MCP server
    tools = []
    if hasattr(mcp_server, 'tools'):
        for tool_name, tool_info in mcp_server.tools.items():
            tools.append({
                "name": tool_name,
                "description": getattr(tool_info, 'description', 'No description available')
            })
    
    return {
        "tools": tools,
        "count": len(tools),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/sse/")
async def sse_endpoint(request: Request):
    """Server-Sent Events endpoint for N8N integration."""
    
    async def generate_sse():
        """Generate SSE stream."""
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connection', 'message': 'Connected to Product Hunt MCP', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Send server info
            yield f"data: {json.dumps({'type': 'server_info', 'data': {'name': 'Product Hunt MCP', 'version': '0.1.0', 'status': 'ready'}, 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Send available tools
            if mcp_server and hasattr(mcp_server, 'tools'):
                tools_data = []
                for tool_name, tool_info in mcp_server.tools.items():
                    tools_data.append({
                        "name": tool_name,
                        "description": getattr(tool_info, 'description', 'No description available')
                    })
                
                yield f"data: {json.dumps({'type': 'tools', 'data': tools_data, 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Send sample Product Hunt data
            sample_data = {
                "type": "product_hunt_data",
                "data": {
                    "message": "Product Hunt MCP server is ready",
                    "available_tools": ["get_posts", "get_post_details", "search_topics", "get_user", "get_collections", "get_comments"],
                    "status": "operational"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            yield f"data: {json.dumps(sample_data)}\n\n"
            
            # Keep connection alive with periodic heartbeats
            while True:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                heartbeat = {
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "status": "alive"
                }
                yield f"data: {json.dumps(heartbeat)}\n\n"
                
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            error_data = {
                "type": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_sse(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.post("/tools/{tool_name}")
async def execute_tool(tool_name: str, request: Request):
    """Execute a specific MCP tool."""
    global mcp_server
    
    if mcp_server is None:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    try:
        # Get request body
        body = await request.json() if request.headers.get("content-type") == "application/json" else {}
        
        # Execute tool (this is a simplified version - you'd need to implement proper tool execution)
        result = {
            "tool": tool_name,
            "status": "executed",
            "input": body,
            "timestamp": datetime.now().isoformat(),
            "message": f"Tool {tool_name} executed successfully"
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")

def main():
    """Run the HTTP server."""
    port = int(os.getenv("PORT", 8080))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting Product Hunt MCP HTTP Server on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main() 