#!/usr/bin/env python3
"""
Script to update user timezone in the database
"""
import os
import sys
import asyncio
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError

# Add backend to path
sys.path.append('backend')

# Import database functions
from backend.database import user_container

async def update_user_timezone(email: str, timezone: str):
    """Update user's timezone in the database"""
    try:
        # Get user document
        query = f"SELECT * FROM c WHERE c.type = 'user' AND c.email = '{email}'"
        items = list(user_container.query_items(query=query, enable_cross_partition_query=True))
        
        if not items:
            print(f"User {email} not found")
            return False
            
        user_doc = items[0]
        print(f"Found user: {user_doc.get('email')}")
        
        # Update timezone in profile
        if 'profile' not in user_doc:
            user_doc['profile'] = {}
        
        user_doc['profile']['timezone'] = timezone
        user_doc['updated_at'] = '2025-01-17T06:00:00.000000'
        user_doc['updated_by'] = 'timezone_update_script'
        
        # Save updated document
        user_container.replace_item(item=user_doc['id'], body=user_doc)
        print(f"Successfully updated timezone to: {timezone}")
        return True
        
    except Exception as e:
        print(f"Error updating timezone: {e}")
        return False

async def main():
    """Main function"""
    email = "kanavtoronto@gmail.com"
    
    # Common timezones - you can change this
    timezone = "America/Toronto"  # Change this to your timezone
    
    print(f"Updating timezone for {email} to {timezone}")
    success = await update_user_timezone(email, timezone)
    
    if success:
        print("Timezone updated successfully!")
        print("Please refresh your dashboard to see the changes.")
    else:
        print("Failed to update timezone")

if __name__ == "__main__":
    asyncio.run(main()) 