# Diabetes Meal Plan Generator - Backend Setup Guide

## ✅ Issues Fixed

1. **Pydantic V2 Compatibility Warning** - Fixed `schema_extra` → `json_schema_extra` in Patient model
2. **Environment Configuration** - Created comprehensive environment template file

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Azure OpenAI account
- Azure Cosmos DB account
- Twilio account (for SMS functionality)

### 1. Install Dependencies

```bash
cd diabetes-meal-plan-generator/backend
pip install -r requirements.txt
```

### 2. Environment Setup

1. Copy the environment template:
   ```bash
   cp env.template .env
   ```

2. Edit `.env` file with your actual values:
   ```bash
   # Azure OpenAI Configuration
   AZURE_OPENAI_KEY=your_actual_api_key
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_API_VERSION=2023-05-15
   AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name
   
   # Cosmos DB Configuration
   COSMO_DB_CONNECTION_STRING=your_cosmos_connection_string
   INTERACTIONS_CONTAINER=interactions
   USER_INFORMATION_CONTAINER=user_information
   
   # Twilio SMS Configuration
   SMS_API_SID=your_twilio_sid
   SMS_KEY=your_twilio_auth_token
   TWILIO_PHONE_NUMBER=+1234567890
   
   # JWT Security
   SECRET_KEY=your_super_secret_jwt_key_here
   ```

### 3. Database Setup

Run the database initialization script:
```bash
python init_db.py
```

### 4. Start the Application

```bash
# Development
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🔧 Configuration Details

### Azure OpenAI Setup

1. Create an Azure OpenAI resource in Azure Portal
2. Deploy a GPT model (recommended: gpt-4 or gpt-3.5-turbo)
3. Get your API key from the "Keys and Endpoint" section
4. Use the endpoint URL and deployment name in your `.env` file

### Cosmos DB Setup

1. Create a Cosmos DB account in Azure Portal
2. Create a database (e.g., "diabetes-meal-plan")
3. Create containers:
   - `interactions` - for user interactions and meal plans
   - `user_information` - for user profiles and authentication
4. Get the connection string from "Keys" section

### Twilio Setup (Optional)

1. Sign up for a Twilio account
2. Get your Account SID and Auth Token from the dashboard
3. Purchase a phone number for SMS functionality
4. Add these to your `.env` file

### JWT Security

Generate a secure secret key:
```bash
openssl rand -hex 32
```

## 📁 Project Structure

```
diabetes-meal-plan-generator/backend/
├── main.py                 # Main FastAPI application
├── database.py            # Database operations
├── consumption_system.py  # Food consumption tracking
├── consumption_endpoints.py # Consumption API endpoints
├── requirements.txt       # Python dependencies
├── env.template          # Environment template
├── init_db.py            # Database initialization
├── tests/                # Test files
└── storage/              # File storage
```

## 🔌 API Endpoints

### Authentication
- `POST /login` - User login
- `POST /register` - User registration
- `POST /admin/login` - Admin login
- `POST /admin/create-patient` - Create patient

### Meal Planning
- `POST /generate-meal-plan` - Generate personalized meal plan
- `POST /generate-recipes` - Generate recipes for meals
- `POST /generate-shopping-list` - Generate shopping list
- `GET /meal_plans` - Get user's meal plans
- `DELETE /meal_plans/{id}` - Delete meal plan

### AI Health Coach
- `POST /chat/message` - Chat with AI health coach
- `POST /chat/analyze-image` - Analyze food images
- `GET /coach/daily-insights` - Get daily health insights
- `POST /coach/quick-log` - Quick log food consumption

### User Management
- `GET /users/me` - Get current user info
- `POST /user/profile` - Save user profile
- `GET /user/profile` - Get user profile

## 🧪 Testing

Run tests:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest --cov=. tests/
```

## 🚀 Production Deployment

### Using Docker (Recommended)

Create a `Dockerfile`:
```dockerfile
FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### Using Systemd

Create a service file `/etc/systemd/system/diabetes-meal-plan.service`:
```ini
[Unit]
Description=Diabetes Meal Plan Generator
After=network.target

[Service]
Type=exec
User=your_user
Group=your_group
WorkingDirectory=/path/to/diabetes-meal-plan-generator/backend
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📊 Monitoring

The application includes:
- Health check endpoint at `/` 
- Prometheus metrics (if configured)
- Comprehensive logging with structured logs
- Error tracking and exception handling

## 🛡️ Security Features

- JWT-based authentication
- Password hashing with bcrypt
- CORS configuration
- Input validation with Pydantic
- Rate limiting (configurable)
- Data privacy and consent management

## 🔍 Troubleshooting

### Common Issues

1. **Environment Variables Missing**
   - Check your `.env` file
   - Ensure all required variables are set

2. **Database Connection Issues**
   - Verify Cosmos DB connection string
   - Check firewall settings

3. **Azure OpenAI API Issues**
   - Verify API key and endpoint
   - Check deployment name
   - Ensure sufficient quota

4. **Import Errors**
   - Install all dependencies: `pip install -r requirements.txt`
   - Check Python version compatibility

### Logs

Check application logs for detailed error information:
```bash
# If running directly
python main.py

# If using systemd
journalctl -u diabetes-meal-plan.service -f
```

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📞 Support

For support or questions, please create an issue in the repository. 