#!/bin/bash

# Frontend Deployment Script for Dietra - Deploy to Existing Azure Static Web Apps
# Deploys React app to existing Azure Static Web Apps URL

set -e

# Configuration
RESOURCE_GROUP="medical"
EXISTING_STORAGE_ACCOUNT="dietrafe1752733227"  # Extract from your existing URL
LOCATION="East US"
BACKEND_URL="https://Dietra-backend.azurewebsites.net"

echo "🚀 Starting frontend deployment to existing Azure Static Web Apps..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📍 Target URL: https://${EXISTING_STORAGE_ACCOUNT}.z13.web.core.windows.net/"

# Step 1: Verify storage account exists
echo "🔍 Verifying existing storage account..."
if ! az storage account show --name $EXISTING_STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP > /dev/null 2>&1; then
    echo "❌ Storage account $EXISTING_STORAGE_ACCOUNT not found in resource group $RESOURCE_GROUP"
    echo "💡 Please check the storage account name or resource group"
    exit 1
fi

echo "✅ Found existing storage account: $EXISTING_STORAGE_ACCOUNT"

# Step 2: Build Frontend
echo "🎨 Building frontend..."
cd frontend

# Create production environment file
cat > .env.production << EOF
REACT_APP_API_URL=$BACKEND_URL
REACT_APP_ENVIRONMENT=production
GENERATE_SOURCEMAP=false
NODE_ENV=production
EOF

# Build the frontend
echo "📦 Building React app..."
npm run build

if [ ! -d "build" ]; then
  echo "❌ Build failed! No build directory created"
  exit 1
fi

echo "✅ Build completed successfully"

# Step 3: Upload frontend to existing storage account
echo "📤 Uploading frontend to existing Azure Storage..."
az storage blob upload-batch \
  --account-name $EXISTING_STORAGE_ACCOUNT \
  --destination '$web' \
  --source build \
  --overwrite

cd ..

# Step 4: Get frontend URL
FRONTEND_URL="https://${EXISTING_STORAGE_ACCOUNT}.z13.web.core.windows.net/"

# Step 5: Configure CORS on backend (if needed)
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
echo "📊 Storage Account: $EXISTING_STORAGE_ACCOUNT"
echo ""
echo "📋 Next Steps:"
echo "1. Open frontend: $FRONTEND_URL"
echo "2. Test login and functionality"
echo "3. Verify meal plan display is clean (no repetitive text)"
echo ""
echo "🎉 Deployment to existing Azure Static Web Apps complete!"
echo "Frontend → Backend communication configured!" 