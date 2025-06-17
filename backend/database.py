import os
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosResourceExistsError
from dotenv import load_dotenv
from datetime import datetime
import uuid
import tiktoken
import json
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Optional, Dict, Any, List

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Cosmos DB configuration
COSMOS_CONNECTION_STRING = os.getenv("COSMO_DB_CONNECTION_STRING")
INTERACTIONS_CONTAINER = os.getenv("INTERACTIONS_CONTAINER")
USER_INFORMATION_CONTAINER = os.getenv("USER_INFORMATION_CONTAINER")

if not all([COSMOS_CONNECTION_STRING, INTERACTIONS_CONTAINER, USER_INFORMATION_CONTAINER]):
    raise ValueError("Missing required environment variables for Cosmos DB configuration")

# Initialize Cosmos DB client
try:
client = CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING)
database = client.get_database_client("diabetes_diet_manager")
interactions_container = database.get_container_client(INTERACTIONS_CONTAINER)
user_container = database.get_container_client(USER_INFORMATION_CONTAINER)
except Exception as e:
    logger.error(f"Failed to initialize Cosmos DB client: {str(e)}")
    raise

def generate_session_id():
    """Generate a unique session ID"""
    return str(uuid.uuid4())

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def create_user(user_data: dict):
    """Create a new user in the database"""
    try:
        # Validate required fields
        required_fields = ["email", "hashed_password"]
        missing_fields = [field for field in required_fields if field not in user_data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        # Add type field for querying and set partition key
        user_data["type"] = "user"
        user_data["id"] = user_data["email"]  # Use email as partition key
        user_data["created_at"] = datetime.utcnow().isoformat()
        
        # Add detailed logging
        logger.info(f"[CREATE_USER] Attempting to create user with email: {user_data.get('email')}")
        logger.info(f"[CREATE_USER] User data keys: {list(user_data.keys())}")
        logger.info(f"[CREATE_USER] User ID being set to: {user_data.get('id')}")
        
        # First, let's double-check if user already exists with a direct query
        existing_check_query = f"SELECT * FROM c WHERE c.id = '{user_data['email']}'"
        existing_items = list(user_container.query_items(query=existing_check_query, enable_cross_partition_query=True))
        logger.info(f"[CREATE_USER] Pre-creation check found {len(existing_items)} existing items")
        if existing_items:
            logger.error(f"[CREATE_USER] Found existing items: {existing_items}")
        
        result = user_container.create_item(body=user_data)
        logger.info(f"[CREATE_USER] Successfully created user: {user_data.get('email')}")
        return result
    except CosmosResourceExistsError as e:
        logger.error(f"[CREATE_USER] CosmosResourceExistsError for email {user_data.get('email')}: {str(e)}")
        logger.error(f"[CREATE_USER] Full Cosmos error details: {e}")
        raise ValueError(f"User with email {user_data.get('email')} already exists")
    except Exception as e:
        logger.error(f"[CREATE_USER] Failed to create user {user_data.get('email')}: {str(e)}")
        logger.error(f"[CREATE_USER] Exception type: {type(e)}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def get_user_by_email(email: str):
    """Get user by email"""
    try:
        if not email:
            raise ValueError("Email is required")

        query = f"SELECT * FROM c WHERE c.type = 'user' AND c.id = '{email}'"
        items = list(user_container.query_items(query=query, enable_cross_partition_query=True))
        return items[0] if items else None
    except Exception as e:
        logger.error(f"Failed to get user: {str(e)}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def save_patient_profile(user_id: str, profile_data: dict, is_admin_update: bool = False):
    """Save patient profile data"""
    try:
        print(f"[SAVE_PROFILE] Starting save for user_id: {user_id}")
        print(f"[SAVE_PROFILE] Input profile_data keys: {list(profile_data.keys())}")
        print(f"[SAVE_PROFILE] Is admin update: {is_admin_update}")
        
        if not user_id:
            raise ValueError("User ID is required")
        if not profile_data:
            raise ValueError("Profile data is required")

        # Make a copy to avoid modifying the original
        data_to_save = profile_data.copy()
        
        # 🚨 FIX: Use composite ID to prevent collision with user records
        # If user_id looks like an email, create a profile-specific ID
        if "@" in user_id:
            profile_id = f"profile_{user_id}"
        else:
            # For patient registration codes, use the code directly
            profile_id = user_id
        
        print(f"[SAVE_PROFILE] Using profile_id: {profile_id} (original user_id: {user_id})")
        
        # Add type and partition key
        data_to_save["type"] = "patient_profile"
        data_to_save["id"] = profile_id  # Use the collision-safe ID
        data_to_save["user_id"] = user_id  # Store the original user_id for lookups
        data_to_save["_partitionKey"] = profile_id
        data_to_save["updated_at"] = datetime.utcnow().isoformat()

        # Check for existing profile first
        existing_profile = None
        try:
            existing_profile = await get_patient_profile(user_id)
            print(f"[SAVE_PROFILE] Existing profile found: {existing_profile is not None}")
        except Exception as e:
            print(f"[SAVE_PROFILE] Error checking existing profile: {e}")
            # Continue with save attempt

        # For admin updates, always allow partial updates
        if is_admin_update:
            print(f"[SAVE_PROFILE] Admin update - allowing partial data")
            if existing_profile:
                # Merge with existing data
                merged_data = existing_profile.copy()
                print(f"[SAVE_PROFILE] Existing profile has {len(existing_profile)} fields")
                print(f"[SAVE_PROFILE] New profile_data has {len(profile_data)} fields")
                
                # Update fields from the new data, including empty strings and empty lists
                # Only skip None values (which indicate field wasn't sent)
                updated_fields = []
                for key, value in profile_data.items():
                    if value is not None:
                        old_value = merged_data.get(key)
                        merged_data[key] = value
                        updated_fields.append(key)
                        if old_value != value:
                            print(f"[SAVE_PROFILE] Field {key}: '{old_value}' -> '{value}'")
                        else:
                            print(f"[SAVE_PROFILE] Field {key}: unchanged ('{value}')")
                
                print(f"[SAVE_PROFILE] Updated {len(updated_fields)} fields: {updated_fields}")
                
                # Re-add required metadata with collision-safe IDs
                merged_data["type"] = "patient_profile"
                merged_data["id"] = profile_id
                merged_data["user_id"] = user_id
                merged_data["_partitionKey"] = profile_id
                merged_data["updated_at"] = datetime.utcnow().isoformat()
                
                data_to_save = merged_data
                print(f"[SAVE_PROFILE] Merged data keys: {list(data_to_save.keys())}")
        else:
            # For non-admin updates, validate required fields only for new profiles
            required_fields = ["fullName", "dateOfBirth", "sex"]
            missing_fields = []
            for field in required_fields:
                if field not in data_to_save or not data_to_save[field] or data_to_save[field] == "":
                    missing_fields.append(field)
            
            print(f"[SAVE_PROFILE] Missing fields: {missing_fields}")
            
            if missing_fields and not existing_profile:
                # New profile, require all fields
                print(f"[SAVE_PROFILE] New profile detected, all fields required")
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            elif missing_fields and existing_profile:
                # Existing profile, merge with existing data and only update non-empty fields
                print(f"[SAVE_PROFILE] Existing profile detected, allowing partial update")
                logger.warning(f"Updating profile with incomplete data. Missing: {', '.join(missing_fields)}")
                
                # Start with existing profile data
                merged_data = existing_profile.copy()
                
                # Update fields from the new data, including empty strings and empty lists
                # Only skip None values (which indicate field wasn't sent)
                for key, value in profile_data.items():
                    if value is not None:
                        merged_data[key] = value
                        print(f"[SAVE_PROFILE] Non-admin updating field {key} with value: {value}")
                
                # Re-add required metadata with collision-safe IDs
                merged_data["type"] = "patient_profile"
                merged_data["id"] = profile_id
                merged_data["user_id"] = user_id
                merged_data["_partitionKey"] = profile_id
                merged_data["updated_at"] = datetime.utcnow().isoformat()
                
                data_to_save = merged_data
                print(f"[SAVE_PROFILE] Merged data keys: {list(data_to_save.keys())}")

        print(f"[SAVE_PROFILE] Final data_to_save keys: {list(data_to_save.keys())}")
        print(f"[SAVE_PROFILE] Calling upsert_item with profile_id: {profile_id}")
        
        result = user_container.upsert_item(body=data_to_save)
        print(f"[SAVE_PROFILE] Successfully saved profile for user: {user_id}")
        return result
        
    except Exception as e:
        print(f"[SAVE_PROFILE] Error in save_patient_profile: {str(e)}")
        logger.error(f"Failed to save patient profile: {str(e)}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def get_patient_profile(user_id: str):
    """Get patient profile data"""
    try:
        if not user_id:
            raise ValueError("User ID is required")

        # 🚨 FIX: Handle the composite ID strategy
        if "@" in user_id:
            profile_id = f"profile_{user_id}"
            query = f"SELECT * FROM c WHERE c.type = 'patient_profile' AND c.id = '{profile_id}'"
        else:
            # For patient registration codes, first try the code directly, then try user_id lookup
            query = f"SELECT * FROM c WHERE c.type = 'patient_profile' AND (c.id = '{user_id}' OR c.user_id = '{user_id}')"
        
        print(f"[GET_PROFILE] Query: {query}")
        items = list(user_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        if items:
            profile = items[0]
            print(f"[GET_PROFILE] Found profile with {len(profile)} fields")
            print(f"[GET_PROFILE] Profile ID: {profile.get('id')}, User ID: {profile.get('user_id')}")
            return profile
        else:
            print(f"[GET_PROFILE] No profile found for user_id: {user_id}")
            return None
    except Exception as e:
        logger.error(f"Failed to get patient profile: {str(e)}")
        raise

async def create_patient(patient_data: dict):
    """Create a new patient record"""
    try:
        # Check for duplicate phone number
        existing_patient_phone = await get_patient_by_phone(patient_data["phone"])
        if existing_patient_phone:
            raise Exception(f"A patient with phone number {patient_data['phone']} already exists: {existing_patient_phone.get('name', 'Unknown')}")
        
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

async def get_user_email_by_patient_id(patient_id: str):
    """Get user email by patient ID (registration code)"""
    try:
        print(f"[GET_USER_EMAIL] Looking for patient_id: {patient_id}")
        query = f"SELECT * FROM c WHERE c.type = 'user' AND c.patient_id = '{patient_id}'"
        print(f"[GET_USER_EMAIL] Query: {query}")
        items = list(user_container.query_items(query=query, enable_cross_partition_query=True))
        print(f"[GET_USER_EMAIL] Found {len(items)} items")
        if items:
            print(f"[GET_USER_EMAIL] First item: {items[0]}")
            return items[0].get('email')
        return None
    except Exception as e:
        print(f"[GET_USER_EMAIL] Exception: {str(e)}")
        raise Exception(f"Failed to get user email by patient ID: {str(e)}")

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

async def get_patient_by_email(email: str):
    """Get patient by email - check if they have registered"""
    try:
        # First check if there's a user with this email
        user = await get_user_by_email(email)
        if user:
            # Check if this user has a patient_id (registration code)
            patient_id = user.get('patient_id')
            if patient_id:
                # Get the patient record
                return await get_patient_by_registration_code(patient_id)
        return None
    except Exception as e:
        raise Exception(f"Failed to get patient by email: {str(e)}")

async def get_patient_by_phone(phone: str):
    """Get patient by phone number"""
    try:
        query = f"SELECT * FROM c WHERE c.type = 'patient' AND c.phone = '{phone}'"
        items = list(user_container.query_items(query=query, enable_cross_partition_query=True))
        return items[0] if items else None
    except Exception as e:
        raise Exception(f"Failed to get patient by phone: {str(e)}")

async def delete_patient(patient_id: str):
    """Delete a patient and all associated data"""
    try:
        # First get the patient to verify it exists
        patient = await get_patient_by_registration_code(patient_id)
        if not patient:
            raise Exception(f"Patient with ID {patient_id} not found")
        
        # Delete the patient record
        user_container.delete_item(item=patient_id, partition_key=patient_id)
        
        # Also delete any associated profile data
        try:
            profile_query = f"SELECT * FROM c WHERE c.type = 'patient_profile' AND (c.id = '{patient_id}' OR c.user_id = '{patient_id}')"
            profile_items = list(user_container.query_items(query=profile_query, enable_cross_partition_query=True))
            for profile in profile_items:
                user_container.delete_item(item=profile['id'], partition_key=profile['id'])
        except Exception as profile_error:
            print(f"Warning: Could not delete profile for patient {patient_id}: {profile_error}")
        
        # If patient has registered (has email), also delete user account
        try:
            # Check if there's a user account linked to this patient
            user_query = f"SELECT * FROM c WHERE c.type = 'user' AND c.patient_id = '{patient_id}'"
            user_items = list(user_container.query_items(query=user_query, enable_cross_partition_query=True))
            for user in user_items:
                user_container.delete_item(item=user['id'], partition_key=user['id'])
        except Exception as user_error:
            print(f"Warning: Could not delete user account for patient {patient_id}: {user_error}")
        
        return True
    except Exception as e:
        raise Exception(f"Failed to delete patient: {str(e)}") 