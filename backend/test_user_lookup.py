import os
import asyncio
from dotenv import load_dotenv
from database import get_user_by_email
import json

# Load environment variables
load_dotenv()

async def test_user_lookup():
    """Test if we can find the user kanavtoronto@gmail.com and print admin user details"""
    try:
        print("Testing user lookup for kanavtoronto@gmail.com")
        print("=" * 50)
        
        # Test the user lookup
        user = await get_user_by_email("kanavtoronto@gmail.com")
        
        if user:
            print("✅ User found!")
            print(f"Email: {user.get('email')}")
            print(f"Username: {user.get('username')}")
            print(f"Admin: {user.get('is_admin', False)}")
            print(f"Disabled: {user.get('disabled', False)}")
            print(f"Has profile: {'profile' in user}")
        else:
            print("❌ User not found!")
            
        # Also test the admin user
        print("\n" + "=" * 50)
        print("Testing admin user lookup for dev@mirakalous.com")
        
        admin_user = await get_user_by_email("dev@mirakalous.com")
        
        if admin_user:
            print("✅ Admin user found!")
            print(json.dumps(admin_user, indent=2))
        else:
            print("❌ Admin user not found!")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_user_lookup()) 