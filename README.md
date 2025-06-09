# Diabetes Diet Planner

A comprehensive web application for diabetes patients to manage their diet, track meals, and get personalized recommendations with advanced admin management capabilities.

## Features

### Patient Features
- User authentication and profile management
- Real-time chat with AI assistant for diet advice
- Meal tracking and history
- PDF report generation
- Session management for chat history
- Responsive Material-UI design

### Admin Features ✨ **NEW**
- **Admin Panel Dashboard** - Comprehensive patient management interface
- **Patient Creation** - Create new patients with automatic registration code generation
- **Duplicate Prevention** - Automatic validation to prevent duplicate phone numbers and emails
- **Patient Profile Management** - View and edit detailed patient profiles
- **Patient Deletion** - Secure deletion with comprehensive data cleanup
- **SMS Integration** - Automatic registration code delivery via Twilio
- **User Registration Tracking** - Monitor which patients have completed registration

## Tech Stack

### Backend
- FastAPI (Python web framework)
- Azure Cosmos DB (Database)
- Azure OpenAI (AI chat)
- Twilio (SMS notifications)
- ReportLab (PDF generation)
- JWT Authentication with admin role support

### Frontend
- React with TypeScript
- Material-UI with enhanced admin components
- React Router with protected admin routes
- React Markdown

## Prerequisites

- Python 3.8+
- Node.js 16+
- Azure account with:
  - Cosmos DB
  - OpenAI service
- Twilio account (for SMS features)

## Backend Dependencies

All backend dependencies are listed in `backend/requirements.txt`:

### Core Framework & API
- fastapi==0.104.1 - Modern Python web framework
- uvicorn==0.24.0 - ASGI server
- python-dotenv==1.0.0 - Environment variable management

### Database & Cloud Services
- azure-cosmos==4.5.1 - Azure Cosmos DB client
- azure-identity==1.15.0 - Azure authentication
- azure-keyvault-secrets==4.7.0 - Azure Key Vault integration

### AI & Machine Learning
- openai==1.12.0 - OpenAI API client
- tiktoken==0.5.1 - Token counting for AI models

### Authentication & Security
- python-jose[cryptography]==3.3.0 - JWT token handling
- passlib[bcrypt]==1.7.4 - Password hashing
- python-multipart==0.0.6 - Form data handling

### Communication & Notifications
- twilio==8.10.0 - SMS notifications for registration codes

### Document Generation & Processing
- reportlab==4.0.7 - PDF generation
- python-docx==1.1.0 - Word document processing

### Data Validation & Utilities
- pydantic[email]==2.4.2 - Data validation with email support
- tenacity==9.1.2 - Retry logic for API calls
- pytz==2023.3 - Timezone handling
- requests==2.31.0 - HTTP client
- httpx==0.25.2 - Async HTTP client

### Production Deployment
- gunicorn==21.2.0 - Production WSGI server

## Frontend Dependencies

All frontend dependencies are listed in `frontend/package.json`:

- @emotion/react - CSS-in-JS styling
- @emotion/styled - Styled components
- @mui/icons-material - Material-UI icons (including delete icons)
- @mui/material - Material-UI components
- @types/node - Node.js type definitions
- @types/react - React type definitions
- @types/react-dom - React DOM type definitions
- axios - HTTP client
- react - React framework
- react-dom - React DOM rendering
- react-markdown - Markdown rendering
- react-router-dom - Client-side routing
- react-scripts - React build tools
- typescript - TypeScript compiler
- uuid - UUID generation
- web-vitals - Performance metrics
- @types/uuid (dev) - UUID type definitions

## Environment Variables

Create a `.env` file in the `backend` directory with the following (update values as needed):

```env
# Azure Cosmos DB
COSMO_DB_CONNECTION_STRING=your_cosmos_connection_string
INTERACTIONS_CONTAINER=interactions
USER_INFORMATION_CONTAINER=user_information

# Azure OpenAI
AZURE_OPENAI_KEY=your_openai_key
AZURE_OPENAI_ENDPOINT=your_openai_endpoint
AZURE_OPENAI_API_VERSION=2023-05-15
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name

# JWT Authentication
SECRET_KEY=your_jwt_secret
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Twilio SMS (Required for admin patient creation)
SMS_API_SID=your_twilio_sid
SMS_KEY=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_phone

# Admin Configuration
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=secure_admin_password
```

## Setup

### Backend Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Start the backend server:
```bash
python main.py
# Or alternatively: uvicorn main:app --reload
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The frontend will be available at `http://localhost:3000`

## Usage

### For Patients
1. Receive registration code from admin via SMS
2. Register a new account using the registration code
3. Use the chat interface to get diet advice
4. Track your meals and view history
5. Generate PDF reports of your diet plan
6. Switch between different chat sessions

### For Administrators ✨ **NEW**
1. **Access Admin Panel**: Navigate to `/admin` and login with admin credentials
2. **Create Patients**: Click "Create New Patient" to add new patients
   - Automatic registration code generation
   - SMS delivery of registration codes
   - Duplicate prevention for phone numbers
3. **Manage Patients**: View all patients with registration status
4. **Edit Profiles**: Click on registered patients to view/edit their profiles
5. **Delete Patients**: Use the delete button (🗑️) to remove patients
   - Comprehensive data cleanup
   - Confirmation dialog with detailed information
6. **Monitor Registration**: Track which patients have completed registration

## API Endpoints

### Authentication
- `POST /login` - Patient login
- `POST /register` - Patient registration with code
- `POST /admin/login` - Admin login

### Patient Management (Admin Only)
- `GET /admin/patients` - Get all patients with email status
- `POST /admin/create-patient` - Create new patient with duplicate prevention
- `DELETE /admin/patients/{patient_id}` - Delete patient and all associated data
- `GET /admin/profile/{user_id}` - Get patient profile for admin editing
- `POST /admin/profile/{user_id}` - Save patient profile from admin panel

### Chat & AI
- `POST /chat/message` - Send chat message
- `GET /chat/history` - Get chat history
- `GET /chat/sessions` - Get chat sessions
- `DELETE /chat/history` - Clear chat history

### Profile & Data
- `POST /api/profile/save` - Save patient profile
- `GET /api/profile/get` - Get patient profile
- `POST /generate-meal-plan` - Generate AI meal plan
- `POST /generate-recipes` - Generate recipes
- `POST /generate-shopping-list` - Generate shopping list

### Document Generation
- `POST /export/{type}` - Generate PDF reports
- `POST /export/consolidated-meal-plan` - Export meal plan

## Security Features

- **JWT Authentication** with role-based access control
- **Admin-only endpoints** protected with authentication middleware
- **Duplicate prevention** at both frontend and backend levels
- **Secure deletion** with comprehensive data cleanup
- **Input validation** using Pydantic models
- **Password hashing** using bcrypt

## Data Management

### Patient Data Structure
- **Patient Records**: Basic information (name, phone, condition, registration code)
- **User Accounts**: Email, password, and authentication data
- **Patient Profiles**: Comprehensive health and dietary information
- **Meal Plans**: Generated meal plans and recipes
- **Chat History**: AI conversation history and sessions

### Data Relationships
- Patients can have associated user accounts (after registration)
- User accounts link to detailed patient profiles
- All data is properly linked and cleaned up during deletion

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request

## Recent Updates ✨

### Admin Panel Enhancements (Latest)
- **Complete Patient Management**: Create, view, edit, and delete patients
- **Duplicate Prevention**: Automatic validation for phone numbers and emails
- **Enhanced UI**: Modern Material-UI components with confirmation dialogs
- **Comprehensive Deletion**: Safe removal of all associated patient data
- **Better User Experience**: Improved feedback, tooltips, and error handling

## License

This project is licensed under the MIT License - see the LICENSE file for details. 