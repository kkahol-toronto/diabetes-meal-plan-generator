import os
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Cosmos DB configuration
COSMOS_CONNECTION_STRING = os.getenv("COSMO_DB_CONNECTION_STRING")
DATABASE_NAME = "diabetes_diet_manager"

def check_containers():
    """Check what containers exist and what users are in them"""
    try:
        # Initialize Cosmos DB client
        client = CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING)
        database = client.get_database_client(DATABASE_NAME)
        
        print(f"Checking database: {DATABASE_NAME}")
        print("=" * 50)
        
        # List all containers
        containers = list(database.list_containers())
        print(f"Found {len(containers)} containers:")
        for container in containers:
            print(f"  - {container['id']}")
        
        print("\n" + "=" * 50)
        
        # Check each container for users
        for container_info in containers:
            container_name = container_info['id']
            print(f"\nChecking container: {container_name}")
            print("-" * 30)
            
            try:
                container = database.get_container_client(container_name)
                
                # Check for users in this container
                user_query = "SELECT * FROM c WHERE c.type = 'user'"
                users = list(container.query_items(query=user_query, enable_cross_partition_query=True))
                
                if users:
                    print(f"Found {len(users)} users:")
                    for user in users:
                        email = user.get('email', 'No email')
                        username = user.get('username', 'No username')
                        is_admin = user.get('is_admin', False)
                        admin_status = " (ADMIN)" if is_admin else ""
                        print(f"  - {email} / {username}{admin_status}")
                else:
                    print("No users found")
                
                # Check for patients in this container
                patient_query = "SELECT * FROM c WHERE c.type = 'patient'"
                patients = list(container.query_items(query=patient_query, enable_cross_partition_query=True))
                
                if patients:
                    print(f"Found {len(patients)} patients:")
                    for patient in patients:
                        name = patient.get('name', 'No name')
                        code = patient.get('registration_code', 'No code')
                        print(f"  - {name} (Code: {code})")
                
            except Exception as e:
                print(f"Error checking container {container_name}: {str(e)}")
        
        print("\n" + "=" * 50)
        print("Container check completed!")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_containers() 