#!/usr/bin/env python3
"""
Script to update timezone to America/Toronto for all users in the database
"""
import os
import sys
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

# Add backend to path
sys.path.append('backend')

# Import user_container from backend.database
from backend.database import user_container

def update_all_users_timezone(timezone: str = "America/Toronto"):
    query = "SELECT * FROM c WHERE c.type = 'user'"
    users = list(user_container.query_items(query=query, enable_cross_partition_query=True))
    print(f"Found {len(users)} users.")
    updated = 0
    for user_doc in users:
        if 'profile' not in user_doc:
            user_doc['profile'] = {}
        user_doc['profile']['timezone'] = timezone
        user_doc['updated_at'] = '2025-01-17T06:00:00.000000'
        user_doc['updated_by'] = 'timezone_update_script_all'
        user_container.replace_item(item=user_doc['id'], body=user_doc)
        updated += 1
        print(f"Updated {user_doc.get('email', user_doc.get('id'))} to timezone {timezone}")
    print(f"Successfully updated timezone for {updated} users.")

if __name__ == "__main__":
    update_all_users_timezone() 