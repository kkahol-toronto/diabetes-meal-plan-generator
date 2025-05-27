# Diabetes Diet Planner

A comprehensive web application for diabetes patients to manage their diet, track meals, and get personalized recommendations.

## Features

- User authentication and profile management
- Real-time chat with AI assistant for diet advice
- Meal tracking and history
- PDF report generation
- Session management for chat history
- Responsive Material-UI design

## Tech Stack

### Backend
- FastAPI (Python web framework)
- Azure Cosmos DB (Database)
- Azure OpenAI (AI chat)
- Twilio (SMS notifications)
- ReportLab (PDF generation)

### Frontend
- React with TypeScript
- Material-UI
- React Router
- React Markdown

## Prerequisites

- Python 3.8+
- Node.js 16+
- Azure account with:
  - Cosmos DB
  - OpenAI service
- Twilio account (for SMS features)

## Environment Variables

Create a `.env` file in the backend directory:

```env
# Azure Cosmos DB
AZURE_COSMOS_ENDPOINT=your_cosmos_endpoint
AZURE_COSMOS_KEY=your_cosmos_key
AZURE_COSMOS_DATABASE_NAME=diabetes_diet_manager

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_openai_key
AZURE_OPENAI_ENDPOINT=your_openai_endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name

# JWT
JWT_SECRET=your_jwt_secret
JWT_ALGORITHM=HS256

# Twilio (Optional)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_phone
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
pip install -r requirements.txt
```

3. Start the backend server:
```bash
uvicorn main:app --reload
```

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

## Usage

1. Register a new account or login
2. Use the chat interface to get diet advice
3. Track your meals and view history
4. Generate PDF reports of your diet plan
5. Switch between different chat sessions

## API Endpoints

- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `POST /chat/message` - Send chat message
- `GET /chat/history` - Get chat history
- `GET /chat/sessions` - Get chat sessions
- `POST /chat/clear` - Clear chat history
- `GET /report/generate` - Generate PDF report

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 