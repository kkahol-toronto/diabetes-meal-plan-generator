#!/bin/bash

# Backend Deployment Script for Dietra
# Builds Docker image, pushes to ACR, and restarts Azure App Service

set -e

# Configuration
ACR_NAME="point32acr"
ACR_URL="point32acr.azurecr.io"
IMAGE_NAME="dietra-backend"
TAG="latest"
RESOURCE_GROUP="medical"
APP_NAME="Dietra-backend"

echo "🚀 Starting backend deployment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Step 1: Login to ACR
echo "🔐 Logging into Azure Container Registry..."
az acr login --name $ACR_NAME

# Step 2: Build Docker image for linux/amd64
echo "🏗️  Building Docker image..."
docker build --platform linux/amd64 -t $ACR_URL/$IMAGE_NAME:$TAG .

# Step 3: Push to ACR
echo "📤 Pushing image to ACR..."
docker push $ACR_URL/$IMAGE_NAME:$TAG

# Step 4: Restart Azure App Service
echo "🔄 Restarting Azure App Service..."
az webapp restart --resource-group $RESOURCE_GROUP --name $APP_NAME

# Step 5: Get app URL
APP_URL="https://$APP_NAME.azurewebsites.net"
echo "✅ Deployment completed!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Backend URL: $APP_URL"
echo "🏥 Health Check: $APP_URL/health"
echo ""
echo "📋 Next Steps:"
echo "1. Wait 2-3 minutes for container to start"
echo "2. Test health endpoint: curl $APP_URL/health"
echo "3. Check logs if needed: az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo "🎉 Backend deployment complete!" 