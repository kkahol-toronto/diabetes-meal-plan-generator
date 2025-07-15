from database import create_user, get_user_by_email, user_container
from main import get_password_hash
from init_db import init_database

async def reset_admin():
    """Reset admin user - delete existing and create new one"""
    # First ensure database and containers exist
    if not init_database():
        print("Failed to initialize database. Cannot reset admin user.")
        return

    admin_email = "dev@mirakalous.com"
    admin_password = "admin123"
    
    print(f"Resetting admin user: {admin_email}")
    
    # Check if admin user already exists and delete it
    existing_admin = await get_user_by_email(admin_email)
    if existing_admin:
        print(f"Found existing admin user. Deleting...")
        try:
            # Delete the existing admin user
            user_container.delete_item(item=admin_email, partition_key=admin_email)
            print("Existing admin user deleted successfully!")
        except Exception as e:
            print(f"Failed to delete existing admin user: {str(e)}")
            return
    else:
        print("No existing admin user found.")
    
    # Create new admin user
    hashed_password = get_password_hash(admin_password)
    
    admin_user = {
        "username": admin_email,
        "email": admin_email,
        "hashed_password": hashed_password,
        "disabled": False,
        "is_admin": True
    }
    
    try:
        await create_user(admin_user)
        print(f"✅ Admin user created successfully!")
        print(f"Email: {admin_email}")
        print(f"Password: {admin_password}")
        print("You can now login to /admin with these credentials.")
    except Exception as e:
        print(f"❌ Failed to create admin user: {str(e)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(reset_admin()) 