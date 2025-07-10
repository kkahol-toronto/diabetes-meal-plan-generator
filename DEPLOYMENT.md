# Diabetes Meal Plan Generator - Deployment Guide

## Quick Start

### Prerequisites
1. Azure subscription with OpenAI service
2. Azure Cosmos DB account
3. Node.js (v18 or higher)
4. Python 3.9+

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export AZURE_OPENAI_ENDPOINT="your-endpoint"
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_DEPLOYMENT_NAME="your-model-deployment"
export COSMOS_ENDPOINT="your-cosmos-endpoint"
export COSMOS_KEY="your-cosmos-key"
export JWT_SECRET_KEY="your-jwt-secret"
```

4. Run the backend:
```bash
uvicorn main:app --reload --port 8000
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Configure API endpoint in `src/config/environment.ts`:
```typescript
export const config = {
  API_URL: "http://localhost:8000"
};
```

4. Start the frontend:
```bash
npm start
```

## Recent Updates

### Enhanced Dietary Restriction Enforcement (Latest)

**Issue Resolved**: Chat system was suggesting non-vegetarian meals to vegetarian users despite having access to dietary restrictions.

**Solution**: Implemented multi-layer enforcement system:

1. **Enhanced System Prompts**: Added explicit dietary warnings with strong language
   - Example: `⚠️ STRICTLY VEGETARIAN - NO MEAT, POULTRY, FISH, OR SEAFOOD`
   - Made dietary compliance the #1 coaching priority

2. **Safety Filters**: Real-time scanning of AI responses for dietary violations
   - Automatically appends warning messages when violations detected
   - Applied to both `/chat/message` and `/chat/message-with-image` endpoints

3. **Comprehensive Coverage**: 
   - Vegetarian restrictions
   - Vegan restrictions  
   - Egg allergies/restrictions
   - Dairy allergies/restrictions
   - Nut allergies
   - Gluten-free requirements

**Files Modified**:
- `backend/main.py` (lines 2499-2530, 2648-2675, 3769-3785, 4214-4220)

**Testing**: 
- Create a user with vegetarian dietary restrictions
- Ask the chat system for meal suggestions
- Verify no non-vegetarian foods are suggested
- If violations occur, safety filter should add warning messages

## Deployment

### Production Environment

1. Set production environment variables
2. Build frontend: `npm run build`
3. Deploy backend to Azure App Service
4. Deploy frontend to Azure Static Web Apps
5. Configure custom domains and SSL certificates

### Environment Variables for Production

```bash
AZURE_OPENAI_ENDPOINT=https://your-instance.openai.azure.com/
AZURE_OPENAI_API_KEY=your-production-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
COSMOS_ENDPOINT=https://your-cosmos.documents.azure.com:443/
COSMOS_KEY=your-cosmos-key
JWT_SECRET_KEY=your-production-jwt-secret
ENVIRONMENT=production
```

### Health Checks

- Backend health: `GET /health`
- Frontend: Check if app loads correctly
- Database: Verify Cosmos DB connectivity
- AI: Test meal plan generation

### Monitoring

- Azure Application Insights for backend monitoring
- Azure Monitor for infrastructure monitoring
- Custom logging for dietary restriction enforcement
- User feedback collection for chat quality

## Troubleshooting

### Common Issues

1. **Chat not respecting dietary restrictions**:
   - Check user profile has dietary restrictions set
   - Verify safety filters are enabled
   - Check logs for `[DIETARY_SAFETY_FILTER]` messages

2. **Backend connection issues**:
   - Verify environment variables
   - Check Cosmos DB connectivity
   - Validate OpenAI API credentials

3. **Frontend build errors**:
   - Clear node_modules and reinstall
   - Check TypeScript compilation
   - Verify environment configuration

### Support

For issues or questions:
1. Check application logs
2. Verify environment configuration
3. Test with minimal reproduction case
4. Document error messages and steps to reproduce 