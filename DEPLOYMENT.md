# Product Hunt MCP Server - Fly.io Deployment for N8N Cloud

This guide explains how to deploy your Product Hunt MCP server to Fly.io so it works with N8N Cloud workflows via HTTP/SSE.

## 🎯 Overview

Your Product Hunt MCP server has been configured with:
- **HTTP/SSE interface** for N8N Cloud integration
- **FastAPI** web server with uvicorn
- **Server-Sent Events (SSE)** endpoint at `/sse/`
- **Health checks** and proper Fly.io configuration
- **CORS support** for cross-origin requests

## 🚀 Quick Deployment

### Prerequisites
1. **Fly.io account**: Sign up at [fly.io](https://fly.io)
2. **flyctl installed**: Follow [installation guide](https://fly.io/docs/hands-on/install-flyctl/)
3. **Product Hunt API token**: Get from [Product Hunt API](https://api.producthunt.com/v2/oauth/applications)

### Deploy Steps

1. **Navigate to your repository**:
   ```bash
   cd producthunt-mcp-server
   ```

2. **Run the deployment script**:
   ```bash
   ./deploy.sh
   ```

   The script will:
   - Check if you're logged into Fly.io
   - Prompt for your Product Hunt API token
   - Set the token as a Fly.io secret
   - Deploy your application
   - Show you the endpoints for N8N integration

### Manual Deployment

If you prefer manual deployment:

1. **Login to Fly.io**:
   ```bash
   flyctl auth login
   ```

2. **Set your Product Hunt token**:
   ```bash
   flyctl secrets set PRODUCT_HUNT_TOKEN=your_token_here
   ```

3. **Deploy**:
   ```bash
   flyctl deploy
   ```

## 🔗 N8N Cloud Integration

After successful deployment, configure your N8N workflow:

### MCP Product Hunt Node Configuration
- **SSE Endpoint**: `https://ph-mcp.fly.dev/sse/`
- **Authentication**: None (token is handled server-side)
- **Tools to Include**: All

### Available Endpoints
- **Root**: `https://ph-mcp.fly.dev/` - Server information
- **Health**: `https://ph-mcp.fly.dev/health` - Health check
- **SSE**: `https://ph-mcp.fly.dev/sse/` - Server-Sent Events for N8N
- **Tools**: `https://ph-mcp.fly.dev/tools` - List available tools

## 🛠️ Configuration Details

### Fly.io Configuration (`fly.toml`)
```toml
app = 'ph-mcp'
primary_region = 'jnb'

[env]
  PORT = "8080"
  HOST = "0.0.0.0"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = 'stop'
  auto_start_machines = true
  min_machines_running = 0

  [[http_service.checks]]
    interval = "15s"
    timeout = "2s"
    grace_period = "5s"
    method = "GET"
    path = "/health"
```

### Environment Variables
- `PORT`: Server port (8080 for Fly.io)
- `HOST`: Server host (0.0.0.0 for Fly.io)
- `PRODUCT_HUNT_TOKEN`: Your Product Hunt API token (set as Fly.io secret)

## 🔍 Monitoring & Troubleshooting

### Check Deployment Status
```bash
flyctl status
```

### View Logs
```bash
flyctl logs
```

### Test Endpoints
```bash
# Health check
curl https://ph-mcp.fly.dev/health

# Server info
curl https://ph-mcp.fly.dev/

# Available tools
curl https://ph-mcp.fly.dev/tools

# SSE endpoint (will stream data)
curl https://ph-mcp.fly.dev/sse/
```

### Common Issues

1. **502 Bad Gateway**
   - Check logs: `flyctl logs`
   - Verify PRODUCT_HUNT_TOKEN is set: `flyctl secrets list`
   - Ensure app is listening on port 8080

2. **Health Check Failing**
   - Verify `/health` endpoint returns 200
   - Check if PRODUCT_HUNT_TOKEN secret is configured

3. **N8N Connection Issues**
   - Verify SSE endpoint is accessible: `curl https://ph-mcp.fly.dev/sse/`
   - Check CORS headers are properly set
   - Ensure N8N is using the correct endpoint URL

## 📊 Architecture

```
N8N Cloud Workflow
       ↓ (HTTPS/SSE)
https://ph-mcp.fly.dev/sse/
       ↓
Fly.io Container (FastAPI + uvicorn)
       ↓
Product Hunt MCP Server (FastMCP)
       ↓
Product Hunt API
```

## 🔄 Updates & Maintenance

### Update Deployment
```bash
flyctl deploy
```

### Update Secrets
```bash
flyctl secrets set PRODUCT_HUNT_TOKEN=new_token_here
```

### Scale Resources (if needed)
```bash
flyctl scale memory 512  # Increase memory to 512MB
```

## 📝 Notes

- The server automatically handles CORS for cross-origin requests
- SSE connection includes heartbeats every 30 seconds
- Health checks run every 15 seconds
- The app auto-starts/stops based on traffic to save costs
- All Product Hunt MCP tools are available via the HTTP interface 