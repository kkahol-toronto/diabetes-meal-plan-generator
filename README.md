# Diabetes Meal Plan Generator

A comprehensive web application for diabetes patients to manage their diet, generate personalized meal plans, recipes, and shopping lists with AI-powered recommendations.

## 🌟 Features

### Core Functionality
- **User Authentication** - Secure JWT-based login and profile management
- **Smart Meal Planning** - AI-powered meal plan generation with Azure OpenAI
- **Recipe Generation** - Detailed recipes for each meal with nutritional information
- **Shopping Lists** - Automatic generation of shopping lists from meal plans
- **PDF Export** - Export meal plans, recipes, and shopping lists as professional PDFs

### Advanced Features
- **Previous Plan Integration** - Toggle to create new plans based on previous ones (70% similar, 30% new)
- **Meal Plan History** - View, manage, and delete previous meal plans
- **Persistent Deletion** - Deleted meal plans stay hidden across sessions using localStorage
- **Bulk Operations** - Select and delete multiple meal plans at once
- **Real-time Progress** - Live progress tracking during recipe generation
- **Responsive Design** - Modern Material-UI interface that works on all devices

### Recent Improvements (Latest Update)
- ✅ **Fixed Bulk Delete System** - Now works perfectly with localStorage persistence
- ✅ **Enhanced Previous Plan Toggle** - 70% similar + 30% new meal functionality restored
- ✅ **Improved Error Handling** - Better error messages and debugging for recipe generation
- ✅ **UI/UX Enhancements** - Cleaner navigation, better defaults, removed duplicate elements
- ✅ **Persistent History Management** - Deleted items stay hidden permanently across sessions

## 🛠 Tech Stack

### Backend
- **FastAPI** - Modern Python web framework with automatic API documentation
- **Azure Cosmos DB** - NoSQL database for scalable data storage
- **Azure OpenAI** - GPT-4 integration for intelligent meal plan generation
- **JWT Authentication** - Secure token-based authentication
- **ReportLab** - Professional PDF generation
- **Twilio** - SMS notifications (optional)

### Frontend
- **React 18** - Modern React with hooks and TypeScript
- **Material-UI v5** - Google's Material Design components
- **React Router v6** - Client-side routing
- **TypeScript** - Type-safe JavaScript development
- **localStorage** - Client-side persistence for user preferences

## 📋 Prerequisites

- **Python 3.8+**
- **Node.js 16+**
- **Azure Account** with:
  - Cosmos DB instance
  - Azure OpenAI service
- **Twilio Account** (optional, for SMS features)

## 🚀 Backend Setup

### 1. Environment Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file in the `backend` directory:

```env
# Azure Cosmos DB
COSMO_DB_CONNECTION_STRING=your_cosmos_connection_string
INTERACTIONS_CONTAINER=interactions
USER_INFORMATION_CONTAINER=user_information

# Azure OpenAI
AZURE_OPENAI_KEY=your_openai_key
AZURE_OPENAI_ENDPOINT=your_openai_endpoint
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name

# JWT Authentication
SECRET_KEY=your_secure_jwt_secret_key

# Twilio (Optional)
SMS_API_SID=your_twilio_sid
SMS_KEY=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
```

### 3. Start Backend Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🎨 Frontend Setup

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Development Server
```bash
npm start
```

The application will open at `http://localhost:3000`

## 📖 Usage Guide

### Getting Started
1. **Register/Login** - Create a new account or sign in
2. **Complete Profile** - Fill in your health information and dietary preferences
3. **Generate Meal Plan** - Choose between:
   - 🆕 **Start Fresh** - Create a completely new meal plan
   - ✅ **Use Previous Plan** - Base new plan on your most recent one (70% similar, 30% new)

### Meal Plan Generation
1. Click "Generate Meal Plan Now"
2. Review and edit your meal plan if needed
3. Generate recipes for your meals
4. Create a shopping list automatically
5. Save everything to your history

### History Management
- **View History** - See all your previous meal plans
- **Bulk Delete** - Select multiple plans and delete them
- **Clear All** - Remove all meal plans at once
- **Persistent Deletion** - Deleted plans stay hidden permanently
- **Export** - Download PDFs of any meal plan

## 🔧 Backend Dependencies

```
# Core FastAPI and web framework
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-dotenv>=1.0.0
pydantic>=2.6.0
starlette>=0.36.3

# AI and OpenAI integration
openai>=1.3.0
tiktoken>=0.5.0

# Database and storage
azure-cosmos>=4.5.1
sqlalchemy>=2.0.25

# Authentication and security
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
bcrypt>=4.0.1

# PDF generation and utilities
reportlab>=4.0.8
aiofiles>=23.2.1
requests>=2.31.0
```

## 🎯 Frontend Dependencies

```json
{
  "@emotion/react": "^11.11.1",
  "@emotion/styled": "^11.11.0",
  "@mui/icons-material": "^5.14.20",
  "@mui/material": "^5.14.20",
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "react-router-dom": "^6.20.1",
  "typescript": "^4.9.5",
  "uuid": "^9.0.1"
}
```

## 🔌 API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User login
- `GET /user/profile` - Get user profile

### Meal Plan Management
- `POST /generate-meal-plan` - Generate new meal plan (with optional previous plan)
- `GET /meal_plans` - Get all user meal plans
- `GET /meal_plans/{plan_id}` - Get specific meal plan
- `POST /meal_plans/bulk_delete` - Delete selected meal plans
- `DELETE /meal_plans/all` - Clear all meal plans

### Recipe & Shopping
- `POST /generate-recipe` - Generate recipe for specific meal
- `POST /generate-shopping-list` - Generate shopping list from recipes
- `POST /save-full-meal-plan` - Save complete meal plan to history

### Export
- `POST /export/meal-plan` - Export meal plan as PDF
- `POST /export/recipes` - Export recipes as PDF
- `POST /export/consolidated-meal-plan` - Export everything as PDF

## 🗄️ Database Schema

### Cosmos DB Structure
- **Container**: `interactions` (partitioned by `/user_id`)
- **Container**: `user_information` (partitioned by `/id`)

### Document Types
- **meal_plan** - Meal plan data with recipes and nutritional info
- **user_profile** - User health information and preferences
- **recipe** - Individual recipe data
- **shopping_list** - Shopping list items

## 🛠️ Troubleshooting

### Common Issues

**Recipe Generation Fails**
- Check Azure OpenAI API key and endpoint
- Verify deployment name matches environment variable
- Check rate limits and quotas

**Meal Plan History Not Loading**
- Clear localStorage: `localStorage.clear()`
- Check browser console for authentication errors
- Verify backend connection

**PDF Export Issues**
- Ensure ReportLab is properly installed
- Check file permissions in backend directory

### Database Partition Key Errors
If you see partition key errors:
- Use correct partition key (`user_id` for meal plans)
- Check `backend/database.py` for examples
- Ensure partition key matches document structure

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 🔒 Security

- JWT tokens for secure authentication
- Input validation and sanitization
- Environment variable protection
- HTTPS recommended for production

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ for diabetes management and healthy living** 