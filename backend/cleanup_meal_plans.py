import os
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

load_dotenv()

COSMOS_CONNECTION_STRING = os.getenv("COSMO_DB_CONNECTION_STRING")
INTERACTIONS_CONTAINER = os.getenv("INTERACTIONS_CONTAINER")
DATABASE_NAME = "diabetes_diet_manager"
USER_EMAIL = "kapilbapa@gmail.com"

def main():
    client = CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING)
    database = client.get_database_client(DATABASE_NAME)
    container = database.get_container_client(INTERACTIONS_CONTAINER)

    # Query for all meal plans for this user (any id format)
    query = f"SELECT * FROM c WHERE c.type = 'meal_plan' AND c.user_id = '{USER_EMAIL}'"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    print(f"Found {len(items)} meal plans for user {USER_EMAIL}")

    deleted = 0
    for item in items:
        item_id = item.get("id")
        partition_key = item.get("_partitionKey")  # Use the _partitionKey field!
        if not item_id or not partition_key:
            print(f"Skipping item with missing id or _partitionKey: {item}")
            continue
        try:
            container.delete_item(item=item_id, partition_key=partition_key)
            print(f"Deleted meal plan: {item_id}")
            deleted += 1
        except Exception as e:
            print(f"Failed to delete {item_id}: {e}")

    print(f"Deleted {deleted} meal plans for user {USER_EMAIL}")

if __name__ == '__main__':
    main()