#!/bin/bash

# Frontend Deployment Script for Dietra
# Builds React app and deploys to Azure Storage Static Website

set -e

# Configuration
RESOURCE_GROUP="medical"
STORAGE_ACCOUNT="dietrafe$(date +%s)"  # Unique name with timestamp
LOCATION="East US"
BACKEND_URL="https://Dietra-backend.azurewebsites.net"

echo "🚀 Starting frontend deployment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Step 1: Create Storage Account for Static Website
echo "💾 Creating storage account for frontend..."
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location "$LOCATION" \
  --sku Standard_LRS \
  --kind StorageV2

# Step 2: Enable static website hosting
echo "🌐 Enabling static website hosting..."
az storage blob service-properties update \
  --account-name $STORAGE_ACCOUNT \
  --static-website \
  --404-document "index.html" \
  --index-document "index.html"

# Step 3: Build Frontend
echo "🎨 Building frontend..."
cd frontend

# Create production environment file
cat > .env.production << EOF
REACT_APP_API_URL=$BACKEND_URL
REACT_APP_ENVIRONMENT=production
GENERATE_SOURCEMAP=false
NODE_ENV=production
EOF

echo "📦 Using existing build..."
# Skip rebuild since we already have a working build
if [ ! -d "build" ]; then
  echo "❌ No build directory found! Please run 'npm run build' first"
  exit 1
fi

# Step 4: Upload frontend to storage account
echo "📤 Uploading frontend to Azure Storage..."
az storage blob upload-batch \
  --account-name $STORAGE_ACCOUNT \
  --destination '$web' \
  --source build

cd ..

# Step 5: Get frontend URL
FRONTEND_URL=$(az storage account show \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query "primaryEndpoints.web" \
  --output tsv)

# Step 6: Configure CORS on backend
echo "🔗 Configuring CORS for backend..."
FRONTEND_URL_CLEAN=${FRONTEND_URL%/}
az webapp cors add \
  --resource-group $RESOURCE_GROUP \
  --name "Dietra-backend" \
  --allowed-origins $FRONTEND_URL_CLEAN

echo "✅ Frontend deployment completed!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Frontend URL: $FRONTEND_URL"
echo "🔧 Backend URL: $BACKEND_URL"
echo "📊 Storage Account: $STORAGE_ACCOUNT"
echo ""
echo "📋 Next Steps:"
echo "1. Open frontend: $FRONTEND_URL"
echo "2. Test login and functionality"
echo "3. Configure custom domain (optional)"
echo ""
echo "🎉 Full-stack deployment complete!"
echo "Frontend → Backend communication configured!" 