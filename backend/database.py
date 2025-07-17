import os
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from dotenv import load_dotenv
from datetime import datetime, timedelta
import uuid
import tiktoken
import json
import traceback
import logging
from openai import AzureOpenAI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Cosmos DB configuration
COSMOS_CONNECTION_STRING = os.getenv("COSMO_DB_CONNECTION_STRING")
INTERACTIONS_CONTAINER = os.getenv("INTERACTIONS_CONTAINER")
USER_INFORMATION_CONTAINER = os.getenv("USER_INFORMATION_CONTAINER")

print(f"[DATABASE] Environment variables:")
print(f"[DATABASE] INTERACTIONS_CONTAINER: {INTERACTIONS_CONTAINER}")
print(f"[DATABASE] USER_INFORMATION_CONTAINER: {USER_INFORMATION_CONTAINER}")

# Initialize Cosmos DB client
client = CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING)
database = client.get_database_client("diabetes_diet_manager")

# Get container clients
interactions_container = database.get_container_client(INTERACTIONS_CONTAINER)
user_container = database.get_container_client(USER_INFORMATION_CONTAINER)

# Initialize Azure OpenAI client
openai_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

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
        print(f"[get_user_by_email] Looking for user: {email}")
        print(f"[get_user_by_email] Using container: {user_container.id}")
        query = f"SELECT * FROM c WHERE c.type = 'user' AND c.id = '{email}'"
        print(f"[get_user_by_email] Query: {query}")
        items = list(user_container.query_items(query=query, enable_cross_partition_query=True))
        print(f"[get_user_by_email] Found {len(items)} items")
        if items:
            print(f"[get_user_by_email] First item: {items[0].get('email')} (admin: {items[0].get('is_admin')})")
        return items[0] if items else None
    except Exception as e:
        print(f"[get_user_by_email] Error: {str(e)}")
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
    
    # Validate that the meal plan is not empty or incomplete
    if not meal_plan_data:
        print(f"[save_meal_plan] Rejecting empty meal plan for user {user_id}")
        raise ValueError("Cannot save empty meal plan")
    
    # Validate required fields for a proper meal plan
    # Check if it has the new format (meals dict) or old format (breakfast, lunch, dinner, snacks arrays)
    has_new_format = "meals" in meal_plan_data and isinstance(meal_plan_data["meals"], dict)
    has_old_format = all(key in meal_plan_data for key in ["breakfast", "lunch", "dinner", "snacks"])
    
    if has_new_format:
        # New format validation
        meals = meal_plan_data["meals"]
        required_meal_types = ["breakfast", "lunch", "dinner"]
        
        # Check if meals dict has required meal types and they're not empty
        for meal_type in required_meal_types:
            if meal_type not in meals or not meals[meal_type] or meals[meal_type].strip() == "":
                print(f"[save_meal_plan] Rejecting meal plan with empty {meal_type} for user {user_id}")
                raise ValueError(f"Meal plan missing or empty {meal_type}")
        
        # Check if at least one meal is not just a placeholder
        all_meals = [meals.get("breakfast", ""), meals.get("lunch", ""), meals.get("dinner", ""), meals.get("snack", "")]
        placeholders = ["not specified", "not provided", "healthy meal option", "placeholder", "tbd", "to be determined"]
        
        if all(any(placeholder in meal.lower() for placeholder in placeholders) for meal in all_meals if meal):
            print(f"[save_meal_plan] Rejecting meal plan with only placeholder meals for user {user_id}")
            raise ValueError("Meal plan contains only placeholder meals")
    
    elif has_old_format:
        # Old format validation (arrays for breakfast, lunch, dinner, snacks)
        required_meal_types = ["breakfast", "lunch", "dinner", "snacks"]
        
        for meal_type in required_meal_types:
            meals_array = meal_plan_data.get(meal_type, [])
            if not meals_array or not isinstance(meals_array, list) or len(meals_array) == 0:
                print(f"[save_meal_plan] Rejecting meal plan with empty {meal_type} array for user {user_id}")
                raise ValueError(f"Meal plan missing or empty {meal_type} array")
            
            # RELAXED VALIDATION: Only check for completely empty meals, not AI-generated content
            # Only reject if ALL meals are truly empty (no content at all)
            if all(not meal or not meal.strip() for meal in meals_array):
                print(f"[save_meal_plan] Rejecting meal plan with completely empty {meal_type} for user {user_id}")
                raise ValueError(f"Meal plan contains completely empty {meal_type}")
            
            # Additional check: if this is NOT an adaptive meal plan, be more strict
            plan_type = meal_plan_data.get('plan_type', '')
            if plan_type != 'adaptive':
                # For non-adaptive plans, check for obvious placeholders
                obvious_placeholders = ["not specified", "not provided", "placeholder", "tbd", "to be determined"]
                if all(not meal or not meal.strip() or any(placeholder in meal.lower() for placeholder in obvious_placeholders) for meal in meals_array):
                    print(f"[save_meal_plan] Rejecting non-adaptive meal plan with placeholder meals in {meal_type} for user {user_id}")
                    raise ValueError(f"Meal plan contains only placeholder meals in {meal_type}")
    
    else:
        print(f"[save_meal_plan] Rejecting meal plan with invalid format for user {user_id}")
        raise ValueError("Meal plan must have either 'meals' dict or 'breakfast', 'lunch', 'dinner', 'snacks' arrays")
    
    # Check for duplicate meal plan prevention based on ID and timestamp
    meal_plan_id = meal_plan_data.get('id', str(uuid.uuid4()))
    
    # If this is an adaptive meal plan, check if we already have a similar one created recently
    # Only prevent duplicates if they have the exact same ID (indicating a true duplicate request)
    if meal_plan_data.get('plan_type') == 'adaptive':
        try:
            # Check for existing adaptive meal plans with the same ID created in the last 30 seconds
            recent_time = datetime.utcnow() - timedelta(seconds=30)
            query = f"""
            SELECT * FROM c 
            WHERE c.type = 'meal_plan' 
            AND c.user_id = '{user_id}' 
            AND c.id = '{meal_plan_id}'
            AND c.created_at >= '{recent_time.isoformat()}'
            """
            existing_plans = list(interactions_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            if existing_plans:
                print(f"[save_meal_plan] Found duplicate adaptive meal plan with same ID, returning existing")
                # Return the existing plan instead of creating a new one
                return existing_plans[0]
        except Exception as e:
            print(f"[save_meal_plan] Error checking for duplicate adaptive plans: {e}")
    
    # Rebuild the item dictionary explicitly to avoid potential CosmosDict issues
    item = {}
    for key, value in meal_plan_data.items():
        item[key] = value
        
    # Ensure partition key and required fields are included
    item['user_id'] = user_id  # Ensure user_id is set from the authenticated user
    item['id'] = meal_plan_id # Use existing ID or generate new one
    item['type'] = 'meal_plan' # Add a type discriminator
    item['_partitionKey'] = user_id # Explicitly set the partition key
    item['created_at'] = datetime.utcnow().isoformat() # Add timestamp
    
    print(f"[save_meal_plan] Attempting to save validated item: {item.get('id')}, type: {item.get('type')}, user_id: {item.get('user_id')}")
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

async def get_user_meal_plans(user_id: str, limit: int = None):
    """Get meal plans for a user with optional limit"""
    try:
        if not user_id:
            raise ValueError("User ID is required")

        # Build query with optional TOP clause for database-level limiting
        if limit:
            query = f"SELECT TOP {limit} * FROM c WHERE c.type = 'meal_plan' AND c.user_id = '{user_id}' ORDER BY c.created_at DESC"
        else:
            query = f"SELECT * FROM c WHERE c.type = 'meal_plan' AND c.user_id = '{user_id}' ORDER BY c.created_at DESC"
        
        meal_plans = list(interactions_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))

        # Validate each meal plan has required fields
        for plan in meal_plans:
            required_fields = ['breakfast', 'lunch', 'dinner', 'snacks', 'dailyCalories', 'macronutrients']
            missing_fields = [field for field in required_fields if field not in plan]

            # Auto-repair common issue where "snacks" field is missing so that warnings stop cluttering logs
            if 'snacks' in missing_fields:
                print(f"[auto-repair] Adding empty snacks array to meal plan {plan['id']} (was missing)")
                plan['snacks'] = []
                try:
                    interactions_container.upsert_item(body=plan)
                    missing_fields.remove('snacks')
                except Exception as e:
                    print(f"[auto-repair] Failed to patch meal plan {plan['id']}: {e}")

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

async def get_user_shopping_lists(user_id: str, limit: int = None):
    """Get shopping lists for a user with optional limit"""
    try:
        # Build query with optional TOP clause for database-level limiting
        if limit:
            query = f"SELECT TOP {limit} * FROM c WHERE c.type = 'shopping_list' AND c.user_id = '{user_id}' ORDER BY c.id DESC"
        else:
            query = f"SELECT * FROM c WHERE c.type = 'shopping_list' AND c.user_id = '{user_id}' ORDER BY c.id DESC"
        
        return list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
    except Exception as e:
        raise Exception(f"Failed to get shopping lists: {str(e)}")

async def save_chat_message(user_id: str, message: str, is_user: bool, session_id: str = None, image_url: str = None):
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
            "id": f"chat_{session_id}_{datetime.utcnow().timestamp()}",
            "image_url": image_url
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

async def get_user_recipes(user_id: str, limit: int = None):
    """Get recipes for a user with optional limit"""
    try:
        # Build query with optional TOP clause for database-level limiting
        if limit:
            query = f"SELECT TOP {limit} * FROM c WHERE c.type = 'recipes' AND c.user_id = '{user_id}' ORDER BY c.id DESC"
        else:
            query = f"SELECT * FROM c WHERE c.type = 'recipes' AND c.user_id = '{user_id}' ORDER BY c.id DESC"
        
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
    """View all meal plans for a user - returns simple view without recipes/shopping"""
    try:
        if not user_id:
            raise ValueError("User ID is required")

        query = f"SELECT c.id, c.created_at, c.dailyCalories, c.macronutrients FROM c WHERE c.type = 'meal_plan' AND c.user_id = '{user_id}' ORDER BY c.created_at DESC"
        meal_plans = list(interactions_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))

        return meal_plans
    except ValueError as e:
        raise ValueError(f"Invalid request: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to view meal plans: {str(e)}")

def log_debug(msg):
    print(f"[DEBUG] {msg}") 

async def save_consumption_record(user_id: str, consumption_data: dict, meal_type: str | None = None):
    """Save a consumption history record to the database"""
    try:
        print(f"[save_consumption_record] Starting save for user {user_id}")
        print(f"[save_consumption_record] Consumption data: {consumption_data}")
        
        # Generate a unique session ID for this consumption record
        session_id = f"consumption_{user_id}_{datetime.utcnow().timestamp()}"
        
        # Determine meal type if not provided
        if not meal_type:
            meal_type = consumption_data.get("meal_type", "")
        
        # If meal_type is still empty, determine based on current time
        if not meal_type or meal_type == "":
            # Use local time for meal type determination
            # For now, we'll use a simple offset approach since we don't have timezone info here
            # TODO: Pass timezone information to this function
            current_time = datetime.utcnow()
            
            # Assume most users are in US timezones (EST/PST), so subtract 5-8 hours from UTC
            # This is a rough approximation - in a production system, we'd store user timezone
            import pytz
            try:
                # Default to US Eastern timezone as a reasonable assumption
                eastern = pytz.timezone('America/New_York')
                utc_time = current_time.replace(tzinfo=pytz.utc)
                local_time = utc_time.astimezone(eastern)
                hour = local_time.hour
            except:
                # Fallback to UTC if timezone conversion fails
                hour = current_time.hour
            
            if 5 <= hour < 11:
                meal_type = "breakfast"
            elif 11 <= hour < 16:
                meal_type = "lunch"
            elif 16 <= hour < 22:
                meal_type = "dinner"
            else:
                meal_type = "snack"
        
        print(f"[save_consumption_record] Determined meal type: {meal_type}")
        
        consumption_record = {
            "type": "consumption_record",
            "user_id": user_id,
            "id": session_id,
            "session_id": session_id,  # This is the partition key
            "timestamp": datetime.utcnow().isoformat(),
            "food_name": consumption_data.get("food_name"),
            "estimated_portion": consumption_data.get("estimated_portion"),
            "nutritional_info": consumption_data.get("nutritional_info", {}),
            "medical_rating": consumption_data.get("medical_rating", {}),
            "image_analysis": consumption_data.get("image_analysis"),
            "image_url": consumption_data.get("image_url"),
            "meal_type": meal_type
        }
        
        print(f"[save_consumption_record] Created record with ID: {consumption_record['id']}")
        print(f"[save_consumption_record] Full record: {consumption_record}")
        
        result = interactions_container.upsert_item(body=consumption_record)
        print(f"[save_consumption_record] Successfully saved record with ID: {result['id']}")
        return result
    except Exception as e:
        print(f"[save_consumption_record] Error saving record: {str(e)}")
        print(f"[save_consumption_record] Full error details:", traceback.format_exc())
        raise Exception(f"Failed to save consumption record: {str(e)}")

async def get_user_consumption_history(user_id: str, limit: int = 50):
    """Get consumption history for a user"""
    try:
        if not user_id:
            raise ValueError("User ID is required")

        print(f"[get_user_consumption_history] Querying consumption records for user {user_id}")
        # Build query with optional TOP clause for database-level limiting
        if limit:
            query = (
                f"SELECT TOP {limit} c.id, c.timestamp, c.food_name, c.estimated_portion, "
                "c.nutritional_info, c.medical_rating, c.image_analysis, c.image_url, c.meal_type "
                "FROM c WHERE c.type = 'consumption_record' "
                f"AND c.user_id = '{user_id}' "
                "ORDER BY c.timestamp DESC"
            )
        else:
            query = (
                "SELECT c.id, c.timestamp, c.food_name, c.estimated_portion, "
                "c.nutritional_info, c.medical_rating, c.image_analysis, c.image_url, c.meal_type "
                "FROM c WHERE c.type = 'consumption_record' "
                f"AND c.user_id = '{user_id}' "
                "ORDER BY c.timestamp DESC"
            )
        print(f"[get_user_consumption_history] Query: {query}")
        
        try:
            # Use cross-partition query since records are partitioned by session_id
            consumption_records = list(interactions_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            print(f"[get_user_consumption_history] Query executed successfully")
        except Exception as query_error:
            print(f"[get_user_consumption_history] Error executing query: {str(query_error)}")
            print(f"[get_user_consumption_history] Query error details:", traceback.format_exc())
            raise
        
        print(f"[get_user_consumption_history] Retrieved {len(consumption_records)} records from database")
        if consumption_records:
            print(f"[get_user_consumption_history] First record: {consumption_records[0]}")
            print(f"[get_user_consumption_history] First record type: {type(consumption_records[0])}")
            print(f"[get_user_consumption_history] First record keys: {list(consumption_records[0].keys())}")
        else:
            print("[get_user_consumption_history] No records found")
        
        print(f"[get_user_consumption_history] Returning {len(consumption_records)} records")
        return consumption_records
        
    except ValueError as e:
        print(f"[get_user_consumption_history] ValueError: {str(e)}")
        raise ValueError(f"Invalid request: {str(e)}")
    except Exception as e:
        print(f"[get_user_consumption_history] Exception: {str(e)}")
        print(f"[get_user_consumption_history] Full error details:", traceback.format_exc())
        raise Exception(f"Failed to get consumption history: {str(e)}")

async def get_consumption_analytics(user_id: str, days: int = 7, user_timezone: str = "UTC"):
    """Get comprehensive consumption analytics for a user over specified days"""
    try:
        if not user_id:
            raise ValueError("User ID is required")
            
        # Calculate date threshold using user's timezone
        from datetime import datetime, timedelta
        from collections import defaultdict
        import re
        import pytz
        
        # Get user's timezone boundaries
        user_tz = pytz.timezone(user_timezone)
        utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
        user_now = utc_now.astimezone(user_tz)
        
        # Calculate threshold date in user's timezone
        threshold_date_user = user_now - timedelta(days=days)
        threshold_date_utc = threshold_date_user.astimezone(pytz.utc).replace(tzinfo=None)
        
        print(f"[get_consumption_analytics] User timezone: {user_timezone}")
        print(f"[get_consumption_analytics] User local time: {user_now}")
        print(f"[get_consumption_analytics] Threshold date (user timezone): {threshold_date_user}")
        print(f"[get_consumption_analytics] Threshold date (UTC): {threshold_date_utc}")
        
        threshold_date = threshold_date_utc.isoformat()
        
        query = f"SELECT * FROM c WHERE c.type = 'consumption_record' AND c.user_id = '{user_id}' AND c.timestamp >= '{threshold_date}' ORDER BY c.timestamp DESC"
        
        consumption_records = list(interactions_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        if not consumption_records:
            # Return empty analytics structure
            return {
                "total_meals": 0,
                "date_range": {
                    "start_date": threshold_date,
                    "end_date": datetime.utcnow().isoformat()
                },
                "daily_averages": {
                    "calories": 0,
                    "protein": 0,
                    "carbohydrates": 0,
                    "fat": 0,
                    "fiber": 0,
                    "sugar": 0,
                    "sodium": 0
                },
                "weekly_trends": {
                    "calories": [0] * 7,
                    "protein": [0] * 7,
                    "carbohydrates": [0] * 7,
                    "fat": [0] * 7
                },
                "meal_distribution": {
                    "breakfast": 0,
                    "lunch": 0,
                    "dinner": 0,
                    "snack": 0
                },
                "top_foods": [],
                "adherence_stats": {
                    "diabetes_suitable_percentage": 0,
                    "calorie_goal_adherence": 0,
                    "protein_goal_adherence": 0,
                    "carb_goal_adherence": 0
                },
                "daily_nutrition_history": []
            }
        
        # Initialize tracking variables
        daily_totals = defaultdict(lambda: {
            "calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0, 
            "fiber": 0, "sugar": 0, "sodium": 0, "meals_count": 0
        })
        food_frequency = defaultdict(lambda: {"frequency": 0, "total_calories": 0})
        meal_type_counts = {"breakfast": 0, "lunch": 0, "dinner": 0, "snack": 0}
        diabetes_suitable_count = 0
        
        # Default daily goals (these should ideally come from user profile)
        daily_goals = {
            "calories": 2000,
            "protein": 100,
            "carbohydrates": 250,
            "fat": 70
        }
        
        # Process each consumption record
        for record in consumption_records:
            nutritional_info = record.get("nutritional_info", {})
            medical_rating = record.get("medical_rating", {})
            food_name = record.get("food_name", "Unknown Food")
            timestamp = record.get("timestamp", "")
            
            # Extract date for daily grouping
            try:
                record_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).date().isoformat()
            except:
                record_date = datetime.utcnow().date().isoformat()
            
            # Extract nutrition values
            calories = nutritional_info.get("calories", 0)
            protein = nutritional_info.get("protein", 0)
            carbohydrates = nutritional_info.get("carbohydrates", nutritional_info.get("carbs", 0))
            fat = nutritional_info.get("fat", 0)
            fiber = nutritional_info.get("fiber", 0)
            sugar = nutritional_info.get("sugar", 0)
            sodium = nutritional_info.get("sodium", 0)
            
            # Update daily totals
            daily_totals[record_date]["calories"] += calories
            daily_totals[record_date]["protein"] += protein
            daily_totals[record_date]["carbohydrates"] += carbohydrates
            daily_totals[record_date]["fat"] += fat
            daily_totals[record_date]["fiber"] += fiber
            daily_totals[record_date]["sugar"] += sugar
            daily_totals[record_date]["sodium"] += sodium
            daily_totals[record_date]["meals_count"] += 1
            
            # Track food frequency
            food_frequency[food_name]["frequency"] += 1
            food_frequency[food_name]["total_calories"] += calories
            
            # Use the stored meal_type from the database first
            meal_type = record.get("meal_type", "")
            
            # If meal_type is empty or missing, determine based on time or food name
            if not meal_type or meal_type == "":
                try:
                    record_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    hour = record_time.hour
                    if 5 <= hour < 11:
                        meal_type = "breakfast"
                    elif 11 <= hour < 16:
                        meal_type = "lunch"
                    elif 16 <= hour < 22:
                        meal_type = "dinner"
                    else:
                        meal_type = "snack"
                except:
                    # Fallback: try to guess from food name
                    food_lower = food_name.lower()
                    if any(word in food_lower for word in ["breakfast", "cereal", "oatmeal", "toast"]):
                        meal_type = "breakfast"
                    elif any(word in food_lower for word in ["lunch", "sandwich", "salad"]):
                        meal_type = "lunch"
                    elif any(word in food_lower for word in ["dinner", "pasta", "rice", "chicken"]):
                        meal_type = "dinner"
                    else:
                        meal_type = "snack"
            
            meal_type_counts[meal_type] += 1
            
            # Check diabetes suitability
            diabetes_suitability = medical_rating.get("diabetes_suitability", "").lower()
            if diabetes_suitability in ["high", "good", "suitable", "excellent"]:
                diabetes_suitable_count += 1
        
        total_records = len(consumption_records)
        
        # Calculate averages
        total_calories = sum(day["calories"] for day in daily_totals.values())
        total_protein = sum(day["protein"] for day in daily_totals.values())
        total_carbohydrates = sum(day["carbohydrates"] for day in daily_totals.values())
        total_fat = sum(day["fat"] for day in daily_totals.values())
        total_fiber = sum(day["fiber"] for day in daily_totals.values())
        total_sugar = sum(day["sugar"] for day in daily_totals.values())
        total_sodium = sum(day["sodium"] for day in daily_totals.values())
        
        # Calculate adherence percentages
        avg_daily_calories = total_calories / days if days > 0 else 0
        avg_daily_protein = total_protein / days if days > 0 else 0
        avg_daily_carbohydrates = total_carbohydrates / days if days > 0 else 0
        
        calorie_adherence = min(100, (avg_daily_calories / daily_goals["calories"]) * 100) if daily_goals["calories"] > 0 else 0
        protein_adherence = min(100, (avg_daily_protein / daily_goals["protein"]) * 100) if daily_goals["protein"] > 0 else 0
        carb_adherence = min(100, (avg_daily_carbohydrates / daily_goals["carbohydrates"]) * 100) if daily_goals["carbohydrates"] > 0 else 0
        
        # Prepare top foods list
        top_foods = [
            {
                "food": food,
                "frequency": data["frequency"],
                "total_calories": data["total_calories"]
            }
            for food, data in sorted(food_frequency.items(), key=lambda x: x[1]["frequency"], reverse=True)
        ][:10]
        
        # Prepare daily nutrition history
        daily_nutrition_history = []
        for date_str, totals in sorted(daily_totals.items()):
            daily_nutrition_history.append({
                "date": date_str,
                "calories": totals["calories"],
                "protein": totals["protein"],
                "carbohydrates": totals["carbohydrates"],
                "fat": totals["fat"],
                "fiber": totals["fiber"],
                "sugar": totals["sugar"],
                "sodium": totals["sodium"],
                "meals_count": totals["meals_count"]
            })
        
        # Calculate weekly trends (last 7 days)
        recent_days = sorted(daily_totals.items())[-7:]
        weekly_trends = {
            "calories": [day[1]["calories"] for day in recent_days] + [0] * (7 - len(recent_days)),
            "protein": [day[1]["protein"] for day in recent_days] + [0] * (7 - len(recent_days)),
            "carbohydrates": [day[1]["carbohydrates"] for day in recent_days] + [0] * (7 - len(recent_days)),
            "fat": [day[1]["fat"] for day in recent_days] + [0] * (7 - len(recent_days))
        }
        
        analytics = {
            "total_meals": total_records,
            "date_range": {
                "start_date": threshold_date,
                "end_date": datetime.utcnow().isoformat()
            },
            "daily_averages": {
                "calories": avg_daily_calories,
                "protein": avg_daily_protein,
                "carbohydrates": avg_daily_carbohydrates,
                "fat": total_fat / days if days > 0 else 0,
                "fiber": total_fiber / days if days > 0 else 0,
                "sugar": total_sugar / days if days > 0 else 0,
                "sodium": total_sodium / days if days > 0 else 0
            },
            "weekly_trends": weekly_trends,
            "meal_distribution": meal_type_counts,
            "top_foods": top_foods,
            "adherence_stats": {
                "diabetes_suitable_percentage": (diabetes_suitable_count / total_records * 100) if total_records > 0 else 0,
                "calorie_goal_adherence": calorie_adherence,
                "protein_goal_adherence": protein_adherence,
                "carb_goal_adherence": carb_adherence
            },
            "daily_nutrition_history": daily_nutrition_history
        }
        
        return analytics
        
    except ValueError as e:
        raise ValueError(f"Invalid request: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to get consumption analytics: {str(e)}") 

async def get_user_meal_history(user_id: str, limit: int = 20):
    """
    Get user's meal history with consumption records
    Args:
        user_id (str): The user's ID
        limit (int): Maximum number of records to return
    Returns:
        List of meal history records with consumption details
    """
    try:
        if not user_id:
            raise ValueError("User ID is required")

        # Query both meal plans and consumption records
        query = f"""
        SELECT TOP {limit} *
        FROM c
        WHERE c.user_id = '{user_id}'
        AND (c.type = 'consumption_record' OR c.type = 'meal_plan')
        ORDER BY c.created_at DESC
        """

        items = list(interactions_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))

        # Process and format the records
        meal_history = []
        for item in items:
            if item['type'] == 'consumption_record':
                meal_history.append({
                    'food_name': item.get('food_name', ''),
                    'meal_type': item.get('meal_type', ''),
                    'timestamp': item.get('created_at', ''),
                    'nutritional_info': {
                        'calories': item.get('calories', 0),
                        'protein': item.get('protein', 0),
                        'carbohydrates': item.get('carbohydrates', 0),
                        'fat': item.get('fat', 0)
                    }
                })

        return meal_history
    except ValueError as e:
        raise ValueError(f"Invalid request: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to get meal history: {str(e)}") 

async def log_meal_suggestion(user_id: str, meal_type: str, suggestion: str, context: dict = None):
    """
    Log a meal suggestion for future reference and analysis
    Args:
        user_id (str): The user's ID
        meal_type (str): Type of meal (breakfast, lunch, dinner, snack)
        suggestion (str): The suggested meal
        context (dict): Additional context about the suggestion
    """
    try:
        if not user_id:
            raise ValueError("User ID is required")

        log_item = {
            'id': str(uuid.uuid4()),
            'type': 'meal_suggestion',
            'user_id': user_id,
            'meal_type': meal_type,
            'suggestion': suggestion,
            'context': context or {},
            'created_at': datetime.utcnow().isoformat(),
            '_partitionKey': user_id
        }

        return interactions_container.create_item(body=log_item)
    except ValueError as e:
        raise ValueError(f"Invalid request: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to log meal suggestion: {str(e)}") 

async def get_ai_suggestion(prompt: str) -> str:
    """
    Get an AI-powered suggestion using Azure OpenAI with retry logic
    Args:
        prompt (str): The prompt to send to the AI model
    Returns:
        str: The AI-generated suggestion
    """
    try:
        # Import the robust wrapper from main
        from main import robust_openai_call
        
        # Call Azure OpenAI API with robust retry logic
        api_result = await robust_openai_call(
            messages=[
                {"role": "system", "content": "You are a knowledgeable nutritionist and meal planning expert, specializing in diabetes management."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800,
            max_retries=3,
            timeout=60,
            context="ai_suggestion"
        )
        
        if api_result["success"]:
            return api_result["content"].strip()
        else:
            logger.error(f"OpenAI API failed: {api_result['error']}")
            raise Exception(f"Failed to get AI suggestion: {api_result['error']}")
            
    except Exception as e:
        logger.error(f"Error getting AI suggestion: {str(e)}")
        raise Exception("Failed to get AI suggestion") 

async def update_consumption_meal_type(user_id: str, record_id: str, meal_type: str):
    """Update meal_type for a specific consumption record."""
    try:
        if not user_id or not record_id:
            raise ValueError("user_id and record_id are required")

        # Fetch the record first
        existing = interactions_container.read_item(item=record_id, partition_key=record_id)

        if existing.get("user_id") != user_id:
            raise PermissionError("Unauthorized")

        existing["meal_type"] = meal_type

        interactions_container.upsert_item(body=existing)
        return True
    except Exception as e:
        print(f"[update_consumption_meal_type] Error: {e}")
        raise 
