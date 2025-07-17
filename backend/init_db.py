import os
from azure.cosmos import CosmosClient, PartitionKey
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Cosmos DB configuration
COSMOS_CONNECTION_STRING = os.getenv("COSMO_DB_CONNECTION_STRING")
DATABASE_NAME = "diabetes_diet_manager"
USER_INFORMATION_CONTAINER = "user_information"
INTERACTIONS_CONTAINER = "interactions"

def init_database():
    try:
        # Initialize Cosmos DB client
        client = CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING)
        
        # Create database if it doesn't exist
        try:
            database = client.create_database(DATABASE_NAME)
            print(f"Created database: {DATABASE_NAME}")
        except Exception as e:
            if "Conflict" in str(e):
                database = client.get_database_client(DATABASE_NAME)
                print(f"Database {DATABASE_NAME} already exists")
            else:
                raise e

        # Create user information container
        try:
            user_container = database.create_container(
                id=USER_INFORMATION_CONTAINER,
                partition_key=PartitionKey(path="/id")
            )
            print(f"Created container: {USER_INFORMATION_CONTAINER}")
        except Exception as e:
            if "Conflict" in str(e):
                print(f"Container {USER_INFORMATION_CONTAINER} already exists")
            else:
                raise e

        # Create interactions container
        try:
            interactions_container = database.create_container(
                id=INTERACTIONS_CONTAINER,
                partition_key=PartitionKey(path="/session_id")
            )
            print(f"Created container: {INTERACTIONS_CONTAINER}")
        except Exception as e:
            if "Conflict" in str(e):
                print(f"Container {INTERACTIONS_CONTAINER} already exists")
            else:
                raise e

        print("Database initialization completed successfully!")
        return True
    except Exception as e:
        print(f"Failed to initialize database: {str(e)}")
        return False

if __name__ == "__main__":
    init_database() 