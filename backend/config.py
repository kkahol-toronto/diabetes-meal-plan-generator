import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import AzureOpenAI
from twilio.rest import Client

# Load environment variables
load_dotenv(override=True)

# Print environment variables for debugging
print(os.getenv("AZURE_OPENAI_KEY"))
print(os.getenv("AZURE_OPENAI_ENDPOINT"))
print(os.getenv("AZURE_OPENAI_API_VERSION"))
print(os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"))
print(os.getenv("AZURE_OPENAI_MODEL_NAME"))
print(os.getenv("AZURE_OPENAI_MODEL_VERSION"))
print(os.getenv("INTERACTIONS_CONTAINER"))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Suppress Azure CosmosDB HTTP logs
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(title="Diabetes Diet Manager API")
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app

def get_openai_client() -> AzureOpenAI:
    """Configure and return OpenAI client for APIM Gateway"""
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_KEY"),  # This will be used as Ocp-Apim-Subscription-Key
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        default_headers={
            "Ocp-Apim-Subscription-Key": os.getenv("AZURE_OPENAI_KEY")
        }
    )

def get_twilio_client() -> Client:
    """Configure and return Twilio client"""
    return Client(os.getenv("SMS_API_SID"), os.getenv("SMS_KEY"))

# Create instances
app = create_app()
client = get_openai_client()
twilio_client = get_twilio_client() 