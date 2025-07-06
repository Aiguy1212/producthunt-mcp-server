#!/bin/bash

# Product Hunt MCP Server Deployment Script for Fly.io
# This script deploys your Product Hunt MCP server to work with N8N Cloud

echo "🚀 Deploying Product Hunt MCP Server to Fly.io"
echo "================================================"

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ Error: flyctl is not installed"
    echo "Please install flyctl: https://fly.io/docs/hands-on/install-flyctl/"
    exit 1
fi

# Check if user is logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "🔐 Please log in to Fly.io first:"
    flyctl auth login
fi

# Check if PRODUCT_HUNT_TOKEN is set
if [ -z "$PRODUCT_HUNT_TOKEN" ]; then
    echo "⚠️  PRODUCT_HUNT_TOKEN environment variable is not set"
    echo "Please set your Product Hunt API token:"
    echo "export PRODUCT_HUNT_TOKEN='your_token_here'"
    echo ""
    echo "You can get your token from: https://api.producthunt.com/v2/oauth/applications"
    echo ""
    read -p "Enter your Product Hunt token now: " token
    if [ -n "$token" ]; then
        export PRODUCT_HUNT_TOKEN="$token"
        echo "✅ Token set for this session"
    else
        echo "❌ No token provided. Exiting."
        exit 1
    fi
fi

# Set the Product Hunt token as a Fly.io secret
echo "🔑 Setting Product Hunt token as Fly.io secret..."
echo "$PRODUCT_HUNT_TOKEN" | flyctl secrets set PRODUCT_HUNT_TOKEN=-

# Deploy the application
echo "📦 Deploying application to Fly.io..."
flyctl deploy

# Check deployment status
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Deployment successful!"
    echo "================================================"
    echo "📡 Your Product Hunt MCP server is now running at:"
    echo "   https://ph-mcp.fly.dev"
    echo ""
    echo "🔗 N8N Integration endpoints:"
    echo "   SSE Endpoint: https://ph-mcp.fly.dev/sse/"
    echo "   Health Check: https://ph-mcp.fly.dev/health"
    echo "   Tools List:   https://ph-mcp.fly.dev/tools"
    echo ""
    echo "⚙️  Configure your N8N workflow to use:"
    echo "   SSE Endpoint: https://ph-mcp.fly.dev/sse/"
    echo ""
    echo "🔍 To check logs: flyctl logs"
    echo "📊 To check status: flyctl status"
    echo "================================================"
else
    echo "❌ Deployment failed!"
    echo "Check the logs with: flyctl logs"
    exit 1
fi 