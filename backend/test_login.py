import os
import asyncio
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_login():
    """Test the login process for kanavtoronto@gmail.com"""
    try:
        print("Testing login for kanavtoronto@gmail.com")
        print("=" * 50)
        
        # Test login endpoint
        url = "http://localhost:8000/login"
        
        # You'll need to provide the actual password
        # For now, let's just test the endpoint structure
        form_data = {
            'username': 'kanavtoronto@gmail.com',
            'password': 'YOUR_PASSWORD_HERE'  # Replace with actual password
        }
        
        print(f"Testing login endpoint: {url}")
        print(f"Username: {form_data['username']}")
        print("Note: You need to replace 'YOUR_PASSWORD_HERE' with the actual password")
        
        # Uncomment the following lines when you have the password:
        # response = requests.post(url, data=form_data)
        # print(f"Response status: {response.status_code}")
        # print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_login() 