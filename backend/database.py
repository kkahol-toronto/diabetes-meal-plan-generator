import os
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from dotenv import load_dotenv
from datetime import datetime
import uuid
import tiktoken
import json

# Load environment variables
load_dotenv()

# Cosmos DB configuration
COSMOS_CONNECTION_STRING = os.getenv("COSMO_DB_CONNECTION_STRING")
INTERACTIONS_CONTAINER = os.getenv("INTERACTIONS_CONTAINER")
USER_INFORMATION_CONTAINER = os.getenv("USER_INFORMATION_CONTAINER")

# Initialize Cosmos DB client
client = CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING)
database = client.get_database_client("diabetes_diet_manager")

# Get container clients
interactions_container = database.get_container_client(INTERACTIONS_CONTAINER)
user_container = database.get_container_client(USER_INFORMATION_CONTAINER)

def generate_session_id():
    """Generate a unique session ID"""
    return str(uuid.uuid4())

async def create_user(user_data: dict):
    """Create a new user in the database"""
    try:
        # Add type field for querying and set partition key
        user_data["type"] = "user"
        user_data["id"] = user_data["email"]  # Use email as partition key
        return user_container.create_item(body=user_data)
    except Exception as e:
        raise Exception(f"Failed to create user: {str(e)}")

async def get_user_by_email(email: str):
    """Get user by email"""
    try:
        query = f"SELECT * FROM c WHERE c.type = 'user' AND c.id = '{email}'"
        items = list(user_container.query_items(query=query, enable_cross_partition_query=True))
        return items[0] if items else None
    except Exception as e:
        raise Exception(f"Failed to get user: {str(e)}")

async def create_patient(patient_data: dict):
    """Create a new patient record"""
    try:
        # Add type field for querying and set partition key
        patient_data["type"] = "patient"
        patient_data["id"] = patient_data["registration_code"]  # Use registration code as partition key
        return user_container.create_item(body=patient_data)
    except Exception as e:
        raise Exception(f"Failed to create patient: {str(e)}")

async def get_patient_by_registration_code(code: str):
    """Get patient by registration code"""
    try:
        query = f"SELECT * FROM c WHERE c.type = 'patient' AND c.id = '{code}'"
        items = list(user_container.query_items(query=query, enable_cross_partition_query=True))
        return items[0] if items else None
    except Exception as e:
        raise Exception(f"Failed to get patient: {str(e)}")

async def get_all_patients():
    """Get all patients"""
    try:
        query = "SELECT * FROM c WHERE c.type = 'patient'"
        return list(user_container.query_items(query=query, enable_cross_partition_query=True))
    except Exception as e:
        raise Exception(f"Failed to get patients: {str(e)}")

async def get_patient_by_id(patient_id: str):
    """Get patient by ID"""
    try:
        query = f"SELECT * FROM c WHERE c.type = 'patient' AND c.id = '{patient_id}'"
        items = list(user_container.query_items(query=query, enable_cross_partition_query=True))
        return items[0] if items else None
    except Exception as e:
        raise Exception(f"Failed to get patient: {str(e)}")

async def save_meal_plan(user_id: str, meal_plan_data: dict):
    """Saves a user's meal plan to Cosmos DB."""
    
    # Rebuild the item dictionary explicitly to avoid potential CosmosDict issues
    item = {}
    for key, value in meal_plan_data.items():
        item[key] = value
        
    # Ensure partition key and required fields are included
    item['user_id'] = user_id  # Ensure user_id is set from the authenticated user
    item['id'] = meal_plan_data.get('id', str(uuid.uuid4())) # Use existing ID or generate new one
    item['type'] = 'meal_plan' # Add a type discriminator
    item['_partitionKey'] = user_id # Explicitly set the partition key
    item['created_at'] = datetime.utcnow().isoformat() # Add timestamp
    
    print(f"[save_meal_plan] Attempting to save item: {item.get('id')}, type: {item.get('type')}, user_id: {item.get('user_id')}")
    print(f"[save_meal_plan] Full item data (partial): {list(item.keys())}")
    
    try:
        # Use upsert_item to create or replace the item
        print(f"[save_meal_plan] Type of interactions_container: {type(interactions_container)}")
        print(f"[save_meal_plan] Type of item: {type(item)}")
        
        # Capture the result of upsert_item and convert it
        saved_item = interactions_container.upsert_item(body=item)
        print(f"[save_meal_plan] Successfully saved item: {saved_item.get('id')}")

        # Explicitly convert the saved item returned by upsert_item to a plain dictionary
        try:
            # json is already imported at the top of database.py
            plain_saved_item = json.loads(json.dumps(saved_item))
            print("[save_meal_plan] Converted saved_item returned by SDK to plain dict before returning")
            return plain_saved_item # Return the converted item
        except Exception as convert_error:
            print(f"[save_meal_plan] Failed to convert saved_item returned by SDK to plain dict: {convert_error}")
            # If conversion fails, return the original saved_item - the error might occur again
            return saved_item

    except Exception as e:
        print(f"[save_meal_plan] Error saving item {item.get('id')}: {e}")
        raise

async def get_user_meal_plans(user_id: str):
    """Get all meal plans for a user"""
    try:
        if not user_id:
            raise ValueError("User ID is required")

        query = f"SELECT * FROM c WHERE c.type = 'meal_plan' AND c.user_id = '{user_id}' ORDER BY c.created_at DESC"
        meal_plans = list(interactions_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))

        # Validate each meal plan has required fields
        for plan in meal_plans:
            required_fields = ['breakfast', 'lunch', 'dinner', 'snacks', 'dailyCalories', 'macronutrients']
            missing_fields = [field for field in required_fields if field not in plan]
            if missing_fields:
                print(f"Warning: Meal plan {plan['id']} is missing fields: {', '.join(missing_fields)}")

        return meal_plans
    except ValueError as e:
        raise ValueError(f"Invalid request: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to get meal plans: {str(e)}")

async def get_meal_plan_by_id(plan_id: str, user_id: str):
    """Get a specific meal plan by ID"""
    try:
        if not plan_id:
            raise ValueError("Plan ID is required")
        if not user_id:
            raise ValueError("User ID is required")

        query = f"SELECT * FROM c WHERE c.type = 'meal_plan' AND c.id = '{plan_id}' AND c.user_id = '{user_id}'"
        items = list(interactions_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))

        if not items:
            return None

        meal_plan = items[0]
        
        # Validate meal plan has required fields
        required_fields = ['breakfast', 'lunch', 'dinner', 'snacks', 'dailyCalories', 'macronutrients']
        missing_fields = [field for field in required_fields if field not in meal_plan]
        if missing_fields:
            print(f"Warning: Meal plan {plan_id} is missing fields: {', '.join(missing_fields)}")

        return meal_plan
    except ValueError as e:
        raise ValueError(f"Invalid request: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to get meal plan: {str(e)}")

async def delete_meal_plan_by_id(plan_id: str, user_id: str):
    """Deletes a meal plan by its ID and user ID."""
    print(f"[delete_meal_plan_by_id] Attempting to delete plan_id: {plan_id} for user_id: {user_id}")
    try:
        if not plan_id:
            raise ValueError("Plan ID is required")
        if not user_id:
            raise ValueError("User ID is required")

        # Ensure plan_id has the correct prefix
        if not plan_id.startswith('meal_plan_'):
            plan_id = f'meal_plan_{plan_id}'

        # First, verify the meal plan belongs to the user and get its partition key
        query = f"SELECT c.id, c.user_id, c.created_at, c.dailyCalories, c.macronutrients FROM c WHERE c.type = 'meal_plan' AND c.id = '{plan_id}' AND c.user_id = '{user_id}'"
        print(f"[delete_meal_plan_by_id] Verification query: {query}")
        items = list(interactions_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))

        if not items:
            print(f"[delete_meal_plan_by_id] Plan {plan_id} not found for user {user_id}")
            return False

        # Validate the meal plan has required fields
        meal_plan = items[0]
        required_fields = ['created_at', 'dailyCalories', 'macronutrients']
        missing_fields = [field for field in required_fields if field not in meal_plan]
        
        if missing_fields:
            print(f"[delete_meal_plan_by_id] Plan {plan_id} is missing required fields: {', '.join(missing_fields)}")
            # Still delete the corrupted plan
            partition_key = meal_plan.get('user_id')
            if partition_key:
                interactions_container.delete_item(item=plan_id, partition_key=partition_key)
                print(f"[delete_meal_plan_by_id] Deleted corrupted plan {plan_id}")
                return True
            return False

        # Get partition key from the fetched item
        partition_key = meal_plan.get('user_id')
        if not partition_key:
            print(f"[delete_meal_plan_by_id] Fetched item for {plan_id} is missing user_id (partition key)")
            return False

        print(f"[delete_meal_plan_by_id] Found valid plan with id: {plan_id}. Attempting deletion.")
        interactions_container.delete_item(item=plan_id, partition_key=partition_key)
        print(f"[delete_meal_plan_by_id] Deletion successful for plan_id: {plan_id}")
        return True

    except CosmosResourceNotFoundError:
        print(f"[delete_meal_plan_by_id] CosmosResourceNotFoundError for plan_id: {plan_id}")
        return False
    except Exception as e:
        print(f"[delete_meal_plan_by_id] Error deleting meal plan {plan_id} for user {user_id}: {e}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Failed to delete meal plan: {str(e)}")

async def delete_all_user_meal_plans(user_id: str):
    """Deletes all meal plans for a specific user."""
    print(f"[delete_all_user_meal_plans] Attempting to delete all plans for user_id: {user_id}")
    try:
        if not user_id:
             print("[delete_all_user_meal_plans] User ID is missing.")
             return 0 # Or raise an error, depending on desired behavior

        # Find all meal plans for the user, including their partition key (user_id)
        query = f"SELECT c.id, c.user_id FROM c WHERE c.type = 'meal_plan' AND c.user_id = '{user_id}'"
        print(f"[delete_all_user_meal_plans] Query for items: {query}")
        items = interactions_container.query_items(
            query=query,
            enable_cross_partition_query=True
        )

        deleted_count = 0
        failed_deletions = []

        # Assuming user_id is the partition key
        # partition_key = user_id # We will now get partition key from each item
        
        for item in items:
            item_id = item.get('id')
            item_partition_key = item.get('user_id') # Assuming user_id is the partition key

            if not item_id or not item_partition_key:
                 print(f"[delete_all_user_meal_plans] Skipping item due to missing id or partition key: {item}")
                 continue # Skip items that don't have necessary info

            try:
                print(f"[delete_all_user_meal_plans] Attempting to delete item id: {item_id} with partition key: {item_partition_key}")
                interactions_container.delete_item(item=item_id, partition_key=item_partition_key)
                print(f"[delete_all_user_meal_plans] Successfully deleted item id: {item_id}")
                deleted_count += 1
            except CosmosResourceNotFoundError:
                print(f"[delete_all_user_meal_plans] Item id {item_id} not found during deletion (might be already deleted).")
                # Item already deleted, continue
                pass
            except Exception as delete_error:
                print(f"[delete_all_user_meal_plans] Error deleting item {item_id} for user {user_id}: {delete_error}")
                failed_deletions.append(item_id)
                # Decide if you want to stop on error or continue
                pass # Continue deleting other items
        
        if failed_deletions:
             print(f"[delete_all_user_meal_plans] Finished deletion with failed items: {failed_deletions}")

        print(f"[delete_all_user_meal_plans] Total deleted count: {deleted_count}")
        return deleted_count

    except Exception as e:
        print(f"[delete_all_user_meal_plans] Error deleting all meal plans for user {user_id}: {e}")
        # Log the full traceback for better debugging
        import traceback
        traceback.print_exc()
        raise Exception(f"Failed to delete all meal plans: {str(e)}")

async def save_shopping_list(user_id: str, shopping_list: dict):
    """Save a shopping list for a user"""
    try:
        session_id = generate_session_id()
        shopping_list["type"] = "shopping_list"
        shopping_list["user_id"] = user_id
        shopping_list["session_id"] = session_id
        shopping_list["id"] = f"shopping_list_{session_id}"
        return interactions_container.create_item(body=shopping_list)
    except Exception as e:
        raise Exception(f"Failed to save shopping list: {str(e)}")

async def get_user_shopping_lists(user_id: str):
    """Get all shopping lists for a user"""
    try:
        query = f"SELECT * FROM c WHERE c.type = 'shopping_list' AND c.user_id = '{user_id}'"
        return list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
    except Exception as e:
        raise Exception(f"Failed to get shopping lists: {str(e)}")

async def save_chat_message(user_id: str, message: str, is_user: bool, session_id: str = None):
    """Save a chat message to the database"""
    try:
        if not session_id:
            session_id = generate_session_id()
        
        chat_data = {
            "type": "chat_message",
            "user_id": user_id,
            "message_content": message,
            "is_user": is_user,
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "id": f"chat_{session_id}_{datetime.utcnow().timestamp()}"
        }
        return interactions_container.create_item(body=chat_data)
    except Exception as e:
        raise Exception(f"Failed to save chat message: {str(e)}")

async def get_recent_chat_history(user_id: str, session_id: str = None, limit: int = 10):
    """Get the most recent chat history for a user"""
    try:
        if session_id:
            query = f"""
            SELECT TOP {limit} *
            FROM c
            WHERE c.type = 'chat_message'
            AND c.user_id = '{user_id}'
            AND c.session_id = '{session_id}'
            ORDER BY c.timestamp DESC
            """
        else:
            query = f"""
            SELECT TOP {limit} *
            FROM c
            WHERE c.type = 'chat_message'
            AND c.user_id = '{user_id}'
            ORDER BY c.timestamp DESC
            """
        
        messages = list(interactions_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        # Return messages in chronological order
        return sorted(messages, key=lambda x: x["timestamp"])
    except Exception as e:
        raise Exception(f"Failed to get chat history: {str(e)}")

async def format_chat_history_for_prompt(user_id: str, session_id: str = None):
    """Format chat history for use in the prompt"""
    try:
        messages = await get_recent_chat_history(user_id, session_id)
        if not messages:
            return ""
        
        formatted_history = "Previous conversation:\n"
        for msg in messages:
            role = "User" if msg["is_user"] else "Assistant"
            formatted_history += f"{role}: {msg['message_content']}\n"
        
        return formatted_history
    except Exception as e:
        raise Exception(f"Failed to format chat history: {str(e)}")

async def clear_chat_history(user_id: str, session_id: str = None):
    """Clear chat history for a user"""
    try:
        if session_id:
            query = f"""
            SELECT *
            FROM c
            WHERE c.type = 'chat_message'
            AND c.user_id = '{user_id}'
            AND c.session_id = '{session_id}'
            """
        else:
            query = f"""
            SELECT *
            FROM c
            WHERE c.type = 'chat_message'
            AND c.user_id = '{user_id}'
            """
        
        messages = list(interactions_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        for message in messages:
            interactions_container.delete_item(
                item=message["id"],
                partition_key=message["session_id"]
            )
        
        return True
    except Exception as e:
        raise Exception(f"Failed to clear chat history: {str(e)}")

async def get_user_sessions(user_id: str):
    """Get all sessions for a user"""
    try:
        query = f"""
        SELECT DISTINCT c.session_id, c.timestamp
        FROM c
        WHERE c.type = 'chat_message'
        AND c.user_id = '{user_id}'
        ORDER BY c.timestamp DESC
        """
        return list(interactions_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
    except Exception as e:
        raise Exception(f"Failed to get user sessions: {str(e)}")

async def save_recipes(user_id: str, recipes: list):
    """Save a list of recipes for a user"""
    try:
        session_id = generate_session_id()
        recipes_doc = {
            "type": "recipes",
            "user_id": user_id,
            "session_id": session_id,
            "id": f"recipes_{session_id}",
            "recipes": recipes
        }
        return interactions_container.create_item(body=recipes_doc)
    except Exception as e:
        raise Exception(f"Failed to save recipes: {str(e)}")

async def get_user_recipes(user_id: str):
    """Get all recipes for a user"""
    try:
        query = f"SELECT * FROM c WHERE c.type = 'recipes' AND c.user_id = '{user_id}'"
        return list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
    except Exception as e:
        raise Exception(f"Failed to get recipes: {str(e)}")

def count_tokens(text, model="gpt-3.5-turbo"):
    try:
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(text))
    except Exception:
        # Fallback: rough word count
        return len(text.split())

async def get_context_history(
    user_id: str,
    session_id: str,
    max_pairs: int = 10, # Max historical pairs to consider from DB initially
    max_tokens: int = 2048,
    model: str = "gpt-3.5-turbo"
):
    """
    Fetch chat history from DB and trim to meet token limits.
    Assumes the latest user message has already been saved to the DB
    and will be part of the fetched history.
    Prioritizes keeping the newest messages.
    Trims by removing the oldest messages first.
    """
    if not session_id:
        print("Warning: get_context_history called without a session_id. Returning empty context.")
        return []

    try:
        # 1. Fetch historical messages from DB for the given session_id
        #    Order by timestamp ASC to get them chronologically (oldest first).
        #    This will include the latest user message which was saved just before this call.
        query = (
            "SELECT c.is_user, c.message_content, c.timestamp FROM c "
            "WHERE c.type = 'chat_message' "
            f"AND c.user_id = '{user_id}' "
            f"AND c.session_id = '{session_id}' "
            "ORDER BY c.timestamp ASC"
        )
        db_docs = list(interactions_container.query_items(query=query, enable_cross_partition_query=True))

        current_messages_for_llm = []
        for doc in db_docs:
            role = "user" if doc.get("is_user") else "assistant"
            content = doc.get("message_content")
            if content is not None:
                current_messages_for_llm.append({"role": role, "content": content})
        
        # Optional: Limit to the last N pairs (max_pairs * 2 messages) from history if too many raw messages fetched
        # This is a preliminary cut before token counting.
        if len(current_messages_for_llm) > max_pairs * 2 and max_pairs > 0:
            current_messages_for_llm = current_messages_for_llm[-(max_pairs * 2):]
        
        if not current_messages_for_llm:
            return []

        # 2. Trim from the OLDEST messages to fit token limit.
        total_tokens = sum(count_tokens(msg["content"], model) for msg in current_messages_for_llm)

        while total_tokens > max_tokens and len(current_messages_for_llm) > 0:
            if len(current_messages_for_llm) == 1:
                if total_tokens > max_tokens:
                     print(f"Warning: Single remaining message ({total_tokens} tokens) exceeds max_tokens ({max_tokens}). Sending as is.")
                break 
            
            removed_message = current_messages_for_llm.pop(0) # Remove the oldest
            total_tokens -= count_tokens(removed_message["content"], model)

        if not current_messages_for_llm:
            print("Warning: Message list became empty after trimming. This is unusual unless max_tokens is very restrictive.")
            return []
            
        return current_messages_for_llm

    except Exception as e:
        print(f"ERROR in get_context_history for session {session_id}, user {user_id}: {e}")
        return [] # Fallback to empty list on error 

async def view_meal_plans(user_id: str):
    """View all meal plans for a user directly from Cosmos DB"""
    try:
        query = f"""
        SELECT c.id, c.created_at, c.breakfast, c.lunch, c.dinner, c.snacks, 
               c.dailyCalories, c.macronutrients
        FROM c
        WHERE c.type = 'meal_plan'
        AND c.user_id = '{user_id}'
        ORDER BY c.created_at DESC
        """
        return list(interactions_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
    except Exception as e:
        raise Exception(f"Failed to view meal plans: {str(e)}") 