import os
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Cosmos DB configuration
COSMOS_CONNECTION_STRING = os.getenv("COSMO_DB_CONNECTION_STRING")
INTERACTIONS_CONTAINER = os.getenv("INTERACTIONS_CONTAINER", "interactions")
USER_INFORMATION_CONTAINER = os.getenv("USER_INFORMATION_CONTAINER", "user_information")
DATABASE_NAME = "diabetes_diet_manager"

def cleanup_all_data():
    """Delete all user data and interactions while keeping admin user"""
    try:
        client = CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING)
        database = client.get_database_client(DATABASE_NAME)
        
        # Get container clients
        interactions_container = database.get_container_client(INTERACTIONS_CONTAINER)
        user_container = database.get_container_client(USER_INFORMATION_CONTAINER)
        
        print(f"Starting cleanup of containers: {INTERACTIONS_CONTAINER} and {USER_INFORMATION_CONTAINER}")
        
        # Clean up interactions container (meal plans, consumption, chat, etc.)
        print("\n=== Cleaning Interactions Container ===")
        interaction_types = [
            "meal_plan",
            "consumption_record", 
            "chat_message",
            "shopping_list",
            "recipe",
            "ai_suggestion"
        ]
        
        total_interactions_deleted = 0
        for doc_type in interaction_types:
            query = f"SELECT * FROM c WHERE c.type = '{doc_type}'"
            items = list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
            
            print(f"Found {len(items)} {doc_type} records")
            
            for item in items:
                try:
                    interactions_container.delete_item(
                        item=item["id"], 
                        partition_key=item.get("session_id", item.get("user_id", item["id"]))
                    )
                    total_interactions_deleted += 1
                except Exception as e:
                    print(f"Error deleting {doc_type} {item.get('id')}: {str(e)}")
        
        print(f"Deleted {total_interactions_deleted} interaction records")
        
        # Clean up user container (keep admin user)
        print("\n=== Cleaning User Container ===")
        admin_email = "dev@mirakalous.com"
        
        # Delete all users except admin
        query = f"SELECT * FROM c WHERE c.type = 'user' AND c.email != '{admin_email}'"
        users = list(user_container.query_items(query=query, enable_cross_partition_query=True))
        
        print(f"Found {len(users)} non-admin users to delete")
        
        total_users_deleted = 0
        for user in users:
            try:
                user_container.delete_item(item=user["email"], partition_key=user["email"])
                total_users_deleted += 1
                print(f"Deleted user: {user.get('email', 'unknown')}")
            except Exception as e:
                print(f"Error deleting user {user.get('email')}: {str(e)}")
        
        # Delete all patient records
        query = "SELECT * FROM c WHERE c.type = 'patient'"
        patients = list(user_container.query_items(query=query, enable_cross_partition_query=True))
        
        print(f"Found {len(patients)} patient records to delete")
        
        total_patients_deleted = 0
        for patient in patients:
            try:
                user_container.delete_item(item=patient["id"], partition_key=patient["id"])
                total_patients_deleted += 1
                print(f"Deleted patient: {patient.get('name', 'unknown')} ({patient.get('registration_code', 'no code')})")
            except Exception as e:
                print(f"Error deleting patient {patient.get('registration_code')}: {str(e)}")
        
        # Delete all user profiles except admin
        query = f"SELECT * FROM c WHERE c.type = 'user_profile' AND c.user_id != '{admin_email}'"
        profiles = list(user_container.query_items(query=query, enable_cross_partition_query=True))
        
        print(f"Found {len(profiles)} user profiles to delete")
        
        total_profiles_deleted = 0
        for profile in profiles:
            try:
                user_container.delete_item(item=profile["id"], partition_key=profile["id"])
                total_profiles_deleted += 1
            except Exception as e:
                print(f"Error deleting profile {profile.get('id')}: {str(e)}")
        
        print(f"\n=== Cleanup Summary ===")
        print(f"✅ Interactions deleted: {total_interactions_deleted}")
        print(f"✅ Users deleted: {total_users_deleted}")
        print(f"✅ Patients deleted: {total_patients_deleted}")
        print(f"✅ Profiles deleted: {total_profiles_deleted}")
        print(f"✅ Admin user preserved: {admin_email}")
        print(f"\n🎉 Database cleanup completed successfully!")
        print(f"Your database is now fresh and ready for user testing!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚨 WARNING: This will delete ALL user data and interactions!")
    print("Only the admin user (dev@mirakalous.com) will be preserved.")
    print("This action cannot be undone!")
    
    confirm = input("\nType 'YES' to confirm you want to proceed: ")
    
    if confirm == "YES":
        cleanup_all_data()
    else:
        print("Cleanup cancelled.") 