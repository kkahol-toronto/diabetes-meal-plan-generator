# Diabetes Diet Planner

A comprehensive web application for diabetes patients to manage their diet, generate meal plans, recipes, and shopping lists, and get personalized recommendations.

## Features

- User authentication and profile management
- Personalized meal plan generation with optional overlap from previous plan
- Recipe and shopping list generation
- Meal plan history and management
- PDF export for meal plans, recipes, and shopping lists
- Responsive Material-UI design

## Tech Stack

### Backend
- FastAPI (Python web framework)
- Azure Cosmos DB (Database)
- Azure OpenAI (AI chat and meal plan generation)
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

## Backend Dependencies

All backend dependencies are listed in `backend/requirements.txt`:

- fastapi>=0.109.0
- uvicorn>=0.27.0
- python-dotenv>=1.0.0
- openai>=1.3.0
- pydantic>=2.6.0
- python-multipart>=0.0.6
- sqlalchemy>=2.0.25
- pydantic-settings>=2.1.0
- python-jose[cryptography]>=3.3.0
- passlib[bcrypt]>=1.7.4
- twilio>=8.10.0
- email-validator>=2.1.0.post1
- alembic>=1.13.1
- azure-cosmos>=4.5.1
- reportlab>=4.0.8
- tiktoken==0.9.0

## Frontend Dependencies

All frontend dependencies are listed in `frontend/package.json`:

- @emotion/react
- @emotion/styled
- @mui/icons-material
- @mui/material
- @types/node
- @types/react
- @types/react-dom
- axios
- react
- react-dom
- react-markdown
- react-router-dom
- react-scripts
- typescript
- uuid
- web-vitals
- @types/uuid (dev)

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

# JWT
SECRET_KEY=your_jwt_secret

# Twilio (Optional)
SMS_API_SID=your_twilio_sid
SMS_KEY=your_twilio_token
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

1. Register a new account or login.
2. Complete your profile.
3. On the Meal Plan step, choose whether to use your most recent meal plan for overlap (about 70% overlap, 30% new meals) or start fresh using the toggle (now labeled 'Start Fresh').
4. Click "Generate Meal Plan Now" to create your plan.
5. Review and optionally edit your meal plan, then proceed to generate recipes and a shopping list.
6. When ready, click **Save Meal Plan and Go to Home** to save your plan, recipes, and shopping list to your history. **Meal plans are only saved to history after this step.**
7. View, export, or manage your meal plan history from the History page.

**Note:**
- If your session expires, you may be asked to log in again before saving or generating new plans.
- Duplicate or partial meal plans are no longer saved; only complete plans (with recipes and shopping list) are stored in your history.
- The UI/UX for meal plan editing and history has been improved for clarity and ease of use.
- The meal plan overlap toggle is now labeled 'Start Fresh' for clarity.

## Main API Endpoints

- `POST /login` - User login
- `POST /generate-meal-plan` - Generate a new meal plan (optionally with previous plan for overlap)
- `POST /generate-recipe` - Generate recipes for meals
- `POST /generate-shopping-list` - Generate a shopping list from recipes
- `POST /save-full-meal-plan` - Save the full meal plan, recipes, and shopping list to history
- `GET /meal_plans` - Get all meal plans for the current user
- `POST /meal_plans/bulk_delete` - Delete selected meal plans
- `POST /export/{type}` - Export meal plan, recipes, or shopping list as PDF

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 