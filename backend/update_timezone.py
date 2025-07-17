#!/usr/bin/env python3
"""
Script to update all user timezones to America/Toronto
"""

import os
import sys
import asyncio
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import user_container

async def update_all_users_timezone():
    """Update timezone to America/Toronto for all users"""
    try:
        print("Updating timezone for all users...")
        query = "SELECT * FROM c WHERE c.type = 'user'"
        items = list(user_container.query_items(query=query, enable_cross_partition_query=True))
        print(f"Found {len(items)} users.")
        updated_count = 0
        for user_doc in items:
            email = user_doc.get('email', user_doc.get('id', 'unknown'))
            current_tz = user_doc.get('profile', {}).get('timezone', 'Not set')
            if 'profile' not in user_doc:
                user_doc['profile'] = {}
            user_doc['profile']['timezone'] = "America/Toronto"
            user_doc['updated_at'] = datetime.utcnow().isoformat()
            user_doc['updated_by'] = 'timezone_update_script_all'
            user_container.replace_item(item=user_doc['id'], body=user_doc)
            print(f"✅ Updated {email}: {current_tz} -> America/Toronto")
            updated_count += 1
        print(f"Done. Updated {updated_count} users.")
    except Exception as e:
        print(f"Error updating timezones: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(update_all_users_timezone()) 