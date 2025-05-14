from database import create_user, get_user_by_email
from main import get_password_hash
from init_db import init_database

async def init_admin():
    # First ensure database and containers exist
    if not init_database():
        print("Failed to initialize database. Cannot create admin user.")
        return

    admin_email = "dev@mirakalous.com"
    admin_password = "admin123"  # This is the password we're using
    hashed_password = get_password_hash(admin_password)
    
    # Check if admin user already exists
    existing_admin = await get_user_by_email(admin_email)
    if existing_admin:
        print(f"Admin user {admin_email} already exists")
        return
    
    admin_user = {
        "username": admin_email,
        "email": admin_email,
        "hashed_password": hashed_password,
        "disabled": False,
        "is_admin": True
    }
    
    try:
        await create_user(admin_user)
        print("Admin user created successfully!")
    except Exception as e:
        print(f"Failed to create admin user: {str(e)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_admin()) 