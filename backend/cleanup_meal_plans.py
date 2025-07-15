import os
from azure.cosmos import CosmosClient, exceptions
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

    # Query all meal plans for the user
    query = f"SELECT * FROM c WHERE c.user_id = '{USER_EMAIL}' AND c.type = 'meal_plan'"
    docs = list(container.query_items(query=query, enable_cross_partition_query=True))
    print(f"Found {len(docs)} meal plan documents for user {USER_EMAIL}")
    deleted = 0
    for doc in docs:
        doc_id = doc.get('id')
        session_id = doc.get('session_id')
        print(f"Attempting to delete id: {doc_id}, session_id: {session_id}")
        deleted_flag = False
        # Try /session_id as partition key
        if session_id:
            try:
                container.delete_item(item=doc_id, partition_key=session_id)
                print(f"Deleted with partition_key=session_id: {session_id}")
                deleted += 1
                deleted_flag = True
            except exceptions.CosmosResourceNotFoundError:
                print(f"Not found with session_id partition key.")
            except Exception as e:
                print(f"Error deleting with session_id: {e}")
        # Try /id as partition key
        if not deleted_flag and doc_id:
            try:
                container.delete_item(item=doc_id, partition_key=doc_id)
                print(f"Deleted with partition_key=id: {doc_id}")
                deleted += 1
                deleted_flag = True
            except exceptions.CosmosResourceNotFoundError:
                print(f"Not found with id partition key.")
            except Exception as e:
                print(f"Error deleting with id: {e}")
        # Try with partition_key=None (for corrupted docs)
        if not deleted_flag and doc_id:
            try:
                container.delete_item(item=doc_id, partition_key=None)
                print(f"Deleted with partition_key=None for id: {doc_id}")
                deleted += 1
                deleted_flag = True
            except exceptions.CosmosResourceNotFoundError:
                print(f"Not found with partition_key=None.")
            except Exception as e:
                print(f"Error deleting with partition_key=None: {e}")
        if not deleted_flag:
            print(f"Could not delete meal plan: {doc_id} (tried session_id, id, and None)")
    print(f"Deleted {deleted} meal plans for user {USER_EMAIL}")

if __name__ == "__main__":
    main()