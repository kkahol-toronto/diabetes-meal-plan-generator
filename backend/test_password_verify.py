import os
import asyncio
from dotenv import load_dotenv
from database import get_user_by_email
from main import verify_password

# Load environment variables
load_dotenv()

async def test_admin_password():
    admin_email = "dev@mirakalous.com"
    password = "admin123"
    user = await get_user_by_email(admin_email)
    if not user:
        print("Admin user not found!")
        return
    hash = user.get("hashed_password")
    print(f"Hash in DB: {hash}")
    if verify_password(password, hash):
        print("✅ Password matches hash!")
    else:
        print("❌ Password does NOT match hash!")

if __name__ == "__main__":
    asyncio.run(test_admin_password()) 