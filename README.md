# 🍽️ Diabetes Diet Manager

A comprehensive, production-ready web application designed to help diabetes patients manage their diet through AI-powered meal planning, recipe generation, and nutrition tracking. Built with modern technologies and enhanced for real-world deployment.

[![Made with React](https://img.shields.io/badge/React-18.2.0-blue.svg)](https://reactjs.org/)
[![Made with FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-4.9.5-blue.svg)](https://www.typescriptlang.org/)
[![Material-UI](https://img.shields.io/badge/Material--UI-5.17.1-blue.svg)](https://mui.com/)

## ✨ Key Features

### 🎯 Core Functionality
- **🔐 Secure Authentication** - JWT-based auth with enhanced session management
- **🤖 AI-Powered Meal Planning** - Azure OpenAI integration for intelligent meal generation
- **👨‍🍳 Smart Recipe Generation** - Detailed diabetes-friendly recipes with nutritional info
- **🛒 Automatic Shopping Lists** - Generated from your meal plans with smart organization
- **📄 Professional PDF Export** - Export meal plans, recipes, and shopping lists
- **📋 Consolidated PDF Storage** - Automatically save complete meal plan PDFs in history
- **📱 Mobile-Responsive Design** - Modern animated UI that works on all devices

### 🏥 Health Management
- **👤 Comprehensive User Profiles** - Detailed health information and dietary preferences
  - **🔧 Enhanced "Other" Options** - Add custom entries for all profile sections with visual feedback
  - **💾 Smart Data Management** - Custom entries are preserved and easily manageable
  - **⌨️ Keyboard Shortcuts** - Press Enter to quickly add custom values
  - **🏷️ Visual Feedback** - See your custom entries as deletable chips immediately
- **📊 Consumption Tracking** - Upload food images for AI-powered nutrition analysis
- **📈 Analytics Dashboard** - Track macronutrient intake and dietary patterns
- **🕐 Timezone-Aware Display** - Accurate timestamps for all your activities
- **💬 AI Health Assistant** - 24/7 chat support for nutrition questions

### 🔧 Advanced Features
- **📚 Meal Plan History** - View, manage, and reuse previous meal plans
- **🔄 Smart Plan Building** - Create new plans based on previous ones (70% similar, 30% new)
- **🗑️ Persistent Data Management** - Deleted items stay hidden with localStorage persistence
- **⚡ Real-time Progress** - Live progress tracking during generation processes
- **🎛️ Bulk Operations** - Select and manage multiple items at once
- **🔔 Error Boundaries** - Production-grade error handling with recovery options
- **🎨 Enhanced UX** - Intuitive profile forms with improved "Other" option handling

### 🚀 Production-Ready Enhancements
- **🛡️ Enhanced Security** - Token validation, secure headers, CORS configuration
- **🔄 Auto-Recovery** - API retry logic with exponential backoff
- **📱 Toast Notifications** - User-friendly feedback system
- **🌐 Environment Management** - Separate dev/staging/production configurations
- **📊 Performance Monitoring** - Health checks and comprehensive logging
- **🐳 Docker Support** - Containerized deployment ready

## 🆕 Latest Updates (December 2024)

### ✅ Enhanced Profile Form Experience
- **Complete "Other" Functionality Overhaul** - All "Other" options now work perfectly across:
  - 🌍 **Ethnicity** (Autocomplete with custom entries)
  - 🏥 **Medical Conditions** (Multi-select with custom conditions)
  - 💊 **Current Medications** (Multi-select with custom medications)
  - 🍽️ **Diet Type** (Autocomplete with custom diet types)
  - 🏃 **Exercise Types** (Multi-select with custom exercise types)
  - 🏠 **Available Appliances** (Multi-select with custom appliances)
  - 🎯 **Primary Goals** (Multi-select with custom goals)
  - ⏰ **Eating Schedule** (Radio with custom schedule options)
  - 🎯 **Calorie Target** (Radio with custom calorie targets)

### 🎨 User Experience Improvements
- **Visual Feedback System** - Custom entries appear as chips with delete functionality
- **Keyboard Shortcuts** - Press Enter to add custom values without clicking
- **Consistent Behavior** - All "Other" sections work identically for intuitive use
- **Error Prevention** - Proper validation prevents empty or invalid entries
- **Data Persistence** - Custom entries are properly saved and managed

### 🛠️ Technical Enhancements
- **Improved State Management** - Better handling of profile form data
- **Enhanced Type Safety** - Proper TypeScript interfaces for all profile fields
- **Optimized Rendering** - Efficient component updates for better performance
- **Better Error Handling** - Graceful fallbacks for all edge cases

## 🏗️ Tech Stack

### Backend Architecture
- **FastAPI** - High-performance Python web framework with automatic API docs
- **Azure Cosmos DB** - Globally distributed NoSQL database
- **Azure OpenAI GPT-4** - Advanced AI for meal planning and recipes
- **JWT Authentication** - Secure token-based authentication with refresh logic
- **ReportLab** - Professional PDF generation
- **Pillow** - Image processing for food consumption tracking
- **Gunicorn** - Production WSGI server

### Frontend Architecture
- **React 18** - Modern React with TypeScript and hooks
- **Material-UI v5** - Google's Material Design system with enhanced form components
- **React Router v6** - Client-side routing with protected routes
- **TypeScript** - Type-safe development with comprehensive interfaces
- **Emotion/Styled** - CSS-in-JS styling with smooth animations
- **Context API** - Global state management for user profiles and app state

### DevOps & Infrastructure
- **Docker & Docker Compose** - Containerized deployment
- **GitHub Actions** - CI/CD pipeline
- **Nginx** - Reverse proxy and load balancing
- **Redis** - Session storage and caching
- **Prometheus** - Monitoring and metrics

## 📋 Prerequisites

### Required
- **Python 3.8+** (3.11+ recommended)
- **Node.js 16+** (18+ recommended)
- **Azure Account** with:
  - Cosmos DB instance
  - Azure OpenAI service (GPT-4 model)

### Optional
- **Docker & Docker Compose** (for containerized deployment)
- **Redis** (for enhanced session management)
- **Twilio Account** (for SMS notifications)

## 🚀 Quick Start

### Using Docker (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd diabetes-meal-plan-generator

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit .env files with your credentials
# Then start with Docker Compose
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

#### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your Azure credentials

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build:prod
```

## ⚙️ Environment Configuration

### Backend (.env)
```env
# Azure Cosmos DB
COSMO_DB_CONNECTION_STRING=your_cosmos_connection_string
INTERACTIONS_CONTAINER=interactions
USER_INFORMATION_CONTAINER=user_information

# Azure OpenAI
AZURE_OPENAI_KEY=your_openai_key
AZURE_OPENAI_ENDPOINT=your_openai_endpoint
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your_gpt4_deployment

# Security
SECRET_KEY=your_secure_jwt_secret_key_256_bits
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Optional: Twilio for SMS
SMS_API_SID=your_twilio_sid
SMS_KEY=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone

# Optional: Redis for sessions
REDIS_URL=redis://localhost:6379

# Environment
ENVIRONMENT=development  # development|staging|production
```

### Frontend (.env)
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development
REACT_APP_VERSION=1.0.0
```

## 📖 Usage Guide

### Getting Started
1. **Register Account** - Create your secure account
2. **Complete Profile** - Fill in health information and dietary preferences
   - ✨ **Use "Other" Options** - Add custom entries for any field not listed
   - 💡 **Pro Tip** - Press Enter or click "Add" to save custom values
   - 🏷️ **Manage Entries** - Delete custom entries by clicking the × on chips
3. **Choose Generation Mode**:
   - 🆕 **Fresh Start** - Create completely new meal plan
   - 🔄 **Build on Previous** - Use your last plan as base (70% similar, 30% new)

### Enhanced Profile Management
- **Smart Form Handling** - All profile sections support custom "Other" entries
- **Visual Feedback** - See your custom entries immediately as chips
- **Easy Management** - Add, view, and delete custom entries with ease
- **Data Persistence** - Your custom entries are properly saved and maintained

### Meal Planning Workflow
1. **Generate Meal Plan** - AI creates personalized weekly plan
2. **Review & Edit** - Modify any meals to your preference
3. **Generate Recipes** - Get detailed cooking instructions
4. **Create Shopping List** - Automatic ingredient compilation
5. **Save to History** - Store for future reference with auto-generated PDF
6. **Export PDFs** - Download professional documents anytime

### Advanced Features
- **History Management** - View, reuse, or delete previous plans
- **Consumption Tracking** - Upload food photos for nutrition analysis
- **AI Chat Assistant** - Ask questions about diabetes nutrition
- **Bulk Operations** - Manage multiple meal plans efficiently
- **Profile Customization** - Extensive customization with "Other" options

## 🔌 API Documentation

The backend provides comprehensive API documentation at `/docs` when running. Key endpoints include:

### Authentication
- `POST /register` - User registration
- `POST /login` - User authentication
- `GET /user/profile` - Profile management

### Meal Planning
- `POST /generate-meal-plan` - AI meal plan generation
- `GET /meal_plans` - Retrieve user's meal plans
- `POST /save-full-meal-plan` - Save complete meal plan

### AI Features  
- `POST /generate-recipe` - Recipe generation
- `POST /generate-shopping-list` - Shopping list creation
- `POST /consumption-analysis` - Food image analysis

### Export & Utilities
- `POST /export/*` - Various PDF export options
- `POST /save-consolidated-pdf` - Generate and store consolidated PDF
- `GET /download-saved-pdf/{filename}` - Download previously saved PDFs
- `GET /health` - System health check

## 🧪 Testing

### Frontend Testing
```bash
cd frontend
npm test                    # Run tests
npm run test:coverage      # Coverage report
npm run lint               # Code linting
npm run type-check         # TypeScript validation
```

### Backend Testing
```bash
cd backend
pytest                     # Run tests
pytest --cov=app          # Coverage report
black .                   # Code formatting
isort .                   # Import sorting
```

## 📦 Deployment

### Production Deployment
1. **Review** `DEPLOYMENT.md` for comprehensive deployment guide
2. **Configure** environment variables for production
3. **Deploy** using Docker Compose or cloud platforms
4. **Monitor** using health checks and logging

### Supported Platforms
- **Docker/Kubernetes** - Containerized deployment
- **Azure App Service** - Native Azure deployment  
- **AWS/GCP** - Cloud platform deployment
- **Traditional VPS** - Manual server deployment

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation** - Check `/docs` endpoint for API documentation
- **Issues** - Report bugs via GitHub issues
- **Health Checks** - Monitor `/health` endpoint for system status

## 🎯 Roadmap

- [x] Enhanced "Other" functionality in profile forms ✅
- [ ] Mobile app development (React Native)
- [ ] Advanced meal plan customization
- [ ] Integration with fitness trackers
- [ ] Multilingual support
- [ ] Advanced analytics dashboard
- [ ] Nutritionist collaboration features

## 🏆 Recent Achievements

- **✅ Complete Profile Form Overhaul** - All "Other" options now work perfectly
- **✅ Enhanced User Experience** - Visual feedback and keyboard shortcuts
- **✅ Production-Ready Security** - Comprehensive authentication and error handling
- **✅ Timezone Management** - Accurate time display for all users
- **✅ PDF Management System** - Complete meal plan storage and retrieval

---

**Made with ❤️ for the diabetes community**

*Transform your health journey with AI-powered nutrition guidance designed specifically for diabetes management.* 