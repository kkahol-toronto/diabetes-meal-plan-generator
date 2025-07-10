# Diabetes Meal Plan Generator - System Overview

## Architecture Overview

The system consists of a React TypeScript frontend and a FastAPI Python backend, designed specifically for diabetes management through personalized meal planning and AI-powered coaching.

### Core Components

1. **Frontend** (React TypeScript)
   - Modern, responsive UI built with React and TypeScript
   - Real-time chat interface with AI coach
   - Meal planning and tracking components
   - User profile management
   - Shopping list generation
   - Recipe management

2. **Backend** (FastAPI Python)
   - RESTful API with FastAPI
   - Azure OpenAI integration for AI coaching
   - Cosmos DB for data storage
   - JWT-based authentication
   - Image analysis for food recognition
   - PDF generation for meal plans

### Key Features

#### 🎯 **Comprehensive AI Chat Personalization** (Enhanced 2024)

The chat system now provides **truly personalized suggestions** based on the user's complete health profile:

**📊 Complete Profile Integration:**
- **Medical Information**: All health conditions, current medications, lab values, vital signs
- **Dietary Preferences**: Cuisine type, dietary restrictions, food preferences, allergies, dislikes
- **Physical Activity**: Work activity level, exercise frequency, exercise types, mobility issues
- **Lifestyle Factors**: Meal prep capability, available appliances, eating schedule
- **Personal Goals**: Primary health goals, weight loss preferences, readiness to change
- **Cultural Preferences**: Ethnicity-based food preferences, traditional cuisine types

**🧠 Enhanced Personalization Features:**
- **Cuisine-Aware Suggestions**: Honors preferred cuisine types (South Asian, Mediterranean, Western, etc.)
- **Appliance-Compatible Recipes**: Only suggests meals that can be prepared with available equipment
- **Activity-Level Appropriate**: Adjusts calorie and macro recommendations based on exercise routine
- **Cultural Food Integration**: Incorporates ethnicity and traditional food preferences
- **Medical Condition Considerations**: Tailors suggestions for diabetes, hypertension, PCOS, etc.
- **Lifestyle-Compatible Timing**: Considers work schedule and meal prep capabilities

**🛡️ Multi-Layer Safety System:**
- **Comprehensive Dietary Filters**: Multiple checks for vegetarian, vegan, gluten-free, allergen restrictions
- **Cuisine Alignment Verification**: Ensures suggestions match preferred cuisine types
- **Medical Compatibility**: Verifies recommendations align with all health conditions
- **Real-time Violation Detection**: Catches and corrects any dietary restriction violations

**💡 Example Personalization Scenarios:**

1. **Vegetarian + South Asian + Diabetes + Limited Appliances**
   - Suggests: Dal with rice, vegetable curry, chapati, paneer dishes
   - Avoids: All meat, considers appliance limitations, diabetes-friendly preparations
   - Uses traditional South Asian spices and cooking methods

2. **Vegan + Mediterranean + Heart Disease + High Activity Level**
   - Suggests: Quinoa tabbouleh, hummus with vegetables, grilled eggplant
   - Higher calories for activity level, heart-healthy olive oil and nuts
   - Traditional Mediterranean flavors and ingredients

3. **Gluten-Free + Western + PCOS + Busy Lifestyle**
   - Suggests: Grilled chicken salads, quinoa bowls, egg-based dishes
   - Quick preparation methods, hormone-balancing foods
   - Familiar Western flavors without gluten

#### 🍽️ AI-Powered Meal Planning
- Personalized meal plans based on health conditions, dietary restrictions, and preferences
- Recipe generation with nutritional analysis
- Smart shopping list creation with ingredient consolidation
- PDF export functionality for meal plans and shopping lists

#### 📊 Food Consumption Tracking
- Image-based food recognition and logging
- Nutritional analysis with medical suitability ratings
- Progress tracking and analytics
- Consumption history with trends analysis

#### 🤖 Intelligent AI Coach
- 24/7 conversational AI assistant specialized in diabetes management
- Contextual responses based on user's meal plans and consumption history
- Real-time feedback on food choices and portions
- Educational content about nutrition and diabetes management

#### 👩‍⚕️ Admin Panel
- Patient management system for healthcare providers
- Registration code generation and management
- Patient profile overview and monitoring
- Meal plan and progress review capabilities

### Technology Stack

#### Frontend
- **React 18** with TypeScript for type safety
- **Modern CSS** with responsive design
- **API Integration** with custom hooks and context management
- **Real-time Chat** with streaming responses

#### Backend
- **FastAPI** for high-performance API development
- **Azure OpenAI** for AI-powered responses and meal planning
- **Azure Cosmos DB** for scalable data storage
- **JWT Authentication** for secure user sessions
- **Image Processing** for food recognition and analysis

#### AI Integration
- **Azure OpenAI GPT-4** for conversational AI and meal planning
- **Computer Vision** for food image analysis and nutritional estimation
- **Custom Prompts** optimized for diabetes management and nutrition coaching

### Data Models

#### User Profile
Comprehensive health profile including:
- Demographics and basic information
- Medical conditions and medications
- Dietary restrictions and preferences
- Physical activity and lifestyle factors
- Goals and readiness for lifestyle changes

#### Meal Plans
Structured meal planning with:
- Daily meal suggestions (breakfast, lunch, dinner, snacks)
- Nutritional breakdown and calorie targets
- Recipe details with preparation instructions
- Shopping lists with consolidated ingredients

#### Consumption Tracking
Detailed food logging featuring:
- Meal identification and portion estimation
- Nutritional analysis and medical suitability ratings
- Timestamp and meal type categorization
- Progress analytics and trend analysis

### Security & Privacy

- **JWT-based Authentication** with secure token management
- **Data Encryption** for sensitive health information
- **GDPR Compliance** with data export and deletion capabilities
- **Access Controls** with role-based permissions for admin functions

### Deployment

The system is designed for cloud deployment with:
- **Azure Web Apps** for backend hosting
- **Static Web Hosting** for frontend deployment
- **Azure Cosmos DB** for data storage
- **Azure OpenAI** for AI services

### Getting Started

1. **Backend Setup**: Install dependencies, configure Azure services, run FastAPI server
2. **Frontend Setup**: Install packages, configure API endpoints, start React development server
3. **Admin Setup**: Create admin users, generate patient registration codes
4. **Patient Onboarding**: Register patients, complete health profiles, start meal planning

For detailed setup instructions, see the deployment documentation. 