import os
import asyncio
from dotenv import load_dotenv
from database import user_container, get_user_by_email
from main import get_password_hash

# Load environment variables
load_dotenv()

async def reset_admin_password():
    """Reset admin user password to admin123"""
    try:
        print("Resetting admin password...")
        print("=" * 50)
        
        admin_email = "dev@mirakalous.com"
        new_password = "admin123"
        
        # Get the admin user
        admin_user = await get_user_by_email(admin_email)
        
        if not admin_user:
            print(f"❌ Admin user {admin_email} not found!")
            return
        
        print(f"✅ Found admin user: {admin_email}")
        
        # Generate new password hash
        new_hashed_password = get_password_hash(new_password)
        print(f"Generated new password hash")
        
        # Update the admin user with new password
        admin_user["hashed_password"] = new_hashed_password
        admin_user["updated_at"] = "2025-07-17T05:24:00.000Z"
        
        # Save the updated user
        user_container.upsert_item(body=admin_user)
        
        print(f"✅ Admin password reset successfully!")
        print(f"Email: {admin_email}")
        print(f"Password: {new_password}")
        print("You can now login with these credentials.")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(reset_admin_password()) 