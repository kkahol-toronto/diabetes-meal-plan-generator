# Diabetes Meal Planning Assistant

A comprehensive AI-powered diabetes management platform that provides personalized meal planning, nutrition tracking, and intelligent health coaching. Built with React TypeScript frontend and FastAPI Python backend, integrated with Azure OpenAI for intelligent recommendations.

## Project Overview

This application helps people with diabetes manage their condition through:
- **AI-powered meal planning** that adapts to individual health needs
- **Intelligent food logging** with image recognition and nutritional analysis
- **Personalized coaching** that provides real-time health insights
- **Comprehensive analytics** for tracking progress and health trends
- **HIPAA-compliant consent management** for health data protection

## How It Works

### User Journey
1. **Registration & Consent**: Users create accounts and provide informed consent for health data collection
2. **Health Profile Setup**: Input medical conditions, dietary preferences, and health goals
3. **Daily Interaction**: Log meals, chat with AI coach, and receive personalized recommendations
4. **Meal Planning**: AI generates custom meal plans based on consumption history and health data
5. **Progress Tracking**: Visual analytics show health trends and goal achievement

### AI Integration
- **Azure OpenAI GPT-4** powers all intelligent features
- **Natural language processing** for conversational interactions
- **Computer vision** for food image analysis and nutritional assessment
- **Machine learning** adapts recommendations based on user behavior

## Architecture

### Frontend (React TypeScript)
```
src/
├── components/           # Reusable UI components
│   ├── ConsentForm.tsx  # HIPAA-compliant consent management
│   ├── MealPlan.tsx     # Meal planning interface
│   ├── AICoach.tsx      # AI chat interface
│   ├── Analytics.tsx    # Health analytics dashboard
│   └── ...
├── pages/               # Application pages
├── contexts/            # React contexts for state management
├── utils/               # Utility functions and API calls
└── types/               # TypeScript type definitions
```

**Key Features:**
- Material-UI for professional, accessible design
- Real-time updates with WebSocket connections
- Responsive design for mobile and desktop
- Interactive charts for data visualization
- Image upload and processing for food logging

### Backend (FastAPI Python)
```
app/
├── main.py             # Application entry point
├── database.py         # Azure Cosmos DB integration
├── consumption_system.py # Food logging and analysis
├── routers/
│   └── coach.py        # AI coaching endpoints
├── tests/              # Comprehensive test suite
└── requirements.txt    # Dependencies
```

**Key Features:**
- FastAPI for high-performance async API
- Azure OpenAI integration for AI features
- Comprehensive error handling and logging
- JWT authentication for secure access
- CORS configuration for frontend integration

### Database (Azure Cosmos DB)
```
Collections:
├── user_information    # User profiles and health data
├── interactions       # Chat history and AI responses
├── consumption_logs   # Food intake records
├── meal_plans        # Generated meal plans
└── analytics_data    # Health metrics and trends
```

## Core Features

### 1. Intelligent Meal Planning
- **Personalized Generation**: AI creates meal plans based on user's health condition, dietary preferences, and consumption history
- **Adaptive Recommendations**: Plans adjust based on user feedback and changing health needs
- **Nutritional Optimization**: Ensures proper macronutrient balance for diabetes management
- **Shopping List Integration**: Automatically generates shopping lists from meal plans

### 2. AI-Powered Food Logging
- **Image Recognition**: Upload food photos for automatic identification and nutritional analysis
- **Smart Meal Detection**: AI detects meal types (breakfast, lunch, dinner, snack) from conversations
- **Nutritional Analysis**: Detailed breakdown of calories, carbs, proteins, and micronutrients
- **Diabetes Assessment**: AI evaluates food suitability for diabetes management

### 3. Conversational AI Coach
- **Natural Language Interface**: Chat with AI using everyday language
- **Context-Aware Responses**: AI remembers conversation history and user preferences
- **Health-Specific Advice**: Recommendations tailored to user's medical conditions
- **Real-Time Insights**: Immediate feedback on food choices and health decisions

### 4. Comprehensive Analytics
- **Progress Tracking**: Visual charts showing health trends over time
- **Goal Management**: Set and track nutrition and health objectives
- **Comparative Analysis**: Compare current performance with historical data
- **Predictive Insights**: AI predicts potential health issues and suggests preventive measures

### 5. HIPAA-Compliant Consent System
- **Informed Consent**: Detailed consent forms complying with PHIPA and HIPAA
- **Privacy Policy Integration**: Clickable privacy policy with comprehensive data usage explanation
- **Electronic Signatures**: Legally binding digital consent process
- **Data Rights Management**: Users can withdraw consent and request data deletion

## Technical Implementation

### Frontend Architecture
```typescript
// API Integration
const apiClient = {
  post: async (endpoint: string, data: any) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data)
    });
    return response.json();
  }
};

// State Management
const AppContext = createContext({
  user: null,
  mealPlans: [],
  consumptionHistory: [],
  updateUser: (userData: UserData) => {},
  addConsumption: (consumption: Consumption) => {}
});
```

### Backend Architecture
```python
# FastAPI Application
app = FastAPI(title="Diabetes Meal Planning Assistant")

# Database Connection
async def get_database():
    client = CosmosClient(CONNECTION_STRING)
    return client.get_database_client(DATABASE_NAME)

# AI Integration
async def get_ai_response(prompt: str, context: dict):
    client = AzureOpenAI(
        api_key=AZURE_OPENAI_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    
    response = await client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": "You are a diabetes nutrition expert..."},
            {"role": "user", "content": prompt}
        ],
        context=context
    )
    return response.choices[0].message.content
```

## Setup and Installation

### Prerequisites
- Node.js 18+
- Python 3.11+
- Azure Cosmos DB account
- Azure OpenAI service

### Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export AZURE_OPENAI_KEY="your-openai-key"
export AZURE_OPENAI_ENDPOINT="your-openai-endpoint"
export COSMO_DB_CONNECTION_STRING="your-cosmos-connection"
export JWT_SECRET="your-jwt-secret"

# Initialize database
python init_db.py

# Start server
uvicorn main:app --reload --port 8000
```

### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Set environment variables
echo "REACT_APP_API_URL=http://localhost:8000" > .env

# Start development server
npm start
```

### Database Setup
```sql
-- Cosmos DB Collections
CREATE COLLECTION user_information
CREATE COLLECTION interactions  
CREATE COLLECTION consumption_logs
CREATE COLLECTION meal_plans
CREATE COLLECTION analytics_data

-- Indexes for performance
CREATE INDEX ON user_information (email)
CREATE INDEX ON consumption_logs (user_id, date)
CREATE INDEX ON meal_plans (user_id, created_date)
```

## API Endpoints

### Authentication
- `POST /auth/register` - User registration with consent
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET /auth/profile` - Get user profile

### AI Coach
- `POST /coach/chat` - Chat with AI coach
- `POST /coach/meal-suggestion` - Get meal recommendations
- `GET /coach/daily-insights` - Daily health insights
- `POST /coach/analyze-food` - Analyze food from image

### Meal Planning
- `POST /generate-meal-plan` - Generate personalized meal plan
- `GET /meal-plans` - Get user's meal plans
- `POST /meal-plans/{id}/feedback` - Provide feedback on meal plan
- `GET /meal-plans/{id}/shopping-list` - Generate shopping list

### Food Logging
- `POST /consumption/log` - Log food consumption
- `GET /consumption/history` - Get consumption history
- `POST /consumption/analyze-image` - Analyze food from image
- `PATCH /consumption/{id}/meal-type` - Update meal type

### Analytics
- `GET /analytics/dashboard` - Dashboard data
- `GET /analytics/trends` - Health trends
- `GET /analytics/goals` - Goal progress
- `GET /analytics/insights` - AI-generated insights

## Usage Examples

### Logging Food
```typescript
// Upload food image
const logFood = async (imageFile: File, mealType: string) => {
  const formData = new FormData();
  formData.append('image', imageFile);
  formData.append('meal_type', mealType);
  
  const response = await fetch('/consumption/analyze-image', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  console.log('Food logged:', result);
};

// Chat with AI coach
const chatWithCoach = async (message: string) => {
  const response = await fetch('/coach/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message})
  });
  
  const result = await response.json();
  return result.response;
};
```

### Generating Meal Plans
```python
# Backend meal plan generation
@app.post("/generate-meal-plan")
async def generate_meal_plan(request: MealPlanRequest):
    # Get user profile and preferences
    user_profile = await get_user_profile(request.user_id)
    consumption_history = await get_consumption_history(request.user_id)
    
    # Generate AI-powered meal plan
    meal_plan = await ai_service.generate_meal_plan(
        user_profile=user_profile,
        consumption_history=consumption_history,
        preferences=request.preferences
    )
    
    # Save to database
    await save_meal_plan(meal_plan)
    
    return meal_plan
```

## Testing

### Backend Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_meal_planning.py

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

### Frontend Tests
```bash
# Run unit tests
npm test

# Run integration tests
npm run test:integration

# Run e2e tests
npm run test:e2e
```

## Security Features

### Data Protection
- **Encryption**: All data encrypted in transit (TLS) and at rest (AES-256)
- **Authentication**: JWT tokens with secure refresh mechanism
- **Authorization**: Role-based access control
- **Input Validation**: Comprehensive input sanitization

### Privacy Compliance
- **HIPAA Compliance**: Health data handling follows HIPAA guidelines
- **PHIPA Compliance**: Compliant with Ontario privacy laws
- **Consent Management**: Granular consent for data usage
- **Data Rights**: Users can access, correct, and delete their data

### Security Best Practices
- **CORS Configuration**: Proper cross-origin resource sharing
- **Rate Limiting**: API rate limiting to prevent abuse
- **Error Handling**: Secure error messages without data leakage
- **Logging**: Comprehensive audit logging for security monitoring

## Deployment

### Production Deployment
```bash
# Backend (Docker)
docker build -t diabetes-app-backend .
docker run -p 8000:8000 diabetes-app-backend

# Frontend (Static hosting)
npm run build
# Deploy build/ folder to hosting service

# Database
# Use Azure Cosmos DB in production
```

### Environment Configuration
```bash
# Production Environment Variables
ENVIRONMENT=production
AZURE_OPENAI_KEY=prod-key
COSMO_DB_CONNECTION_STRING=prod-connection
JWT_SECRET=secure-secret
CORS_ORIGINS=https://yourdomain.com
```

## Monitoring and Maintenance

### Health Checks
- API health endpoints for monitoring
- Database connection monitoring
- AI service availability checks
- Frontend performance monitoring

### Logging and Analytics
- Comprehensive application logging
- User interaction analytics
- Performance metrics tracking
- Error monitoring and alerting

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -m 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For technical support or questions:
- Email: support@mirakalous.com
- Phone: +1 (647) 292-3991

---

**Built with care for the diabetes community** 🏥

*Empowering individuals with diabetes through intelligent technology and personalized health management.* 