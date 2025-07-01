# Admin Portal

This is a separate admin portal website for the Diabetes Diet Manager application. It provides a dedicated interface for administrators to manage users and their profiles.

## Features

- Secure admin login with JWT authentication
- View and manage all users
- Edit user profiles and health information
- Create new users
- Resend registration codes
- Monitor user account status and consent

## Setup

1. Make sure you have Python 3.11+ installed
2. Install the required dependencies:
   ```bash
   pip install fastapi uvicorn jinja2 python-jose[cryptography] passlib[bcrypt] python-multipart aiofiles
   ```

3. Set up environment variables:
   ```bash
   # Required for JWT authentication
   export SECRET_KEY="your-secret-key-here"  # Use the same key as the main application
   ```

## Running the Admin Portal

1. Navigate to the admin portal directory:
   ```bash
   cd admin_portal
   ```

2. Start the server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8001 --reload
   ```

3. Access the admin portal at `http://localhost:8001`

## Security

- The admin portal uses the same authentication system as the main application
- Only users with admin privileges can access the portal
- All sensitive operations require authentication
- Session management is implemented for better security
- The portal runs on a separate port to isolate it from the main application

## Database

The admin portal uses the same database as the main application, ensuring data consistency. It imports and reuses:

- Database connections
- Models
- Authentication utilities

## Development

- The portal is built with FastAPI for high performance
- Templates use Jinja2 for server-side rendering
- Bootstrap 5 is used for responsive design
- Custom CSS is provided for consistent styling 