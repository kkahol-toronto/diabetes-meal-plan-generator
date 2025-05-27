import os
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from dotenv import load_dotenv
from datetime import datetime
import uuid
import tiktoken

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

async def save_meal_plan(user_id: str, meal_plan: dict):
    """Save a meal plan for a user"""
    try:
        session_id = generate_session_id()
        meal_plan["type"] = "meal_plan"
        meal_plan["user_id"] = user_id
        meal_plan["session_id"] = session_id
        meal_plan["id"] = f"meal_plan_{session_id}"
        print("Saving to container:", interactions_container.container_link)
        print("Meal plan session_id:", meal_plan["session_id"])
        return interactions_container.create_item(body=meal_plan)
    except Exception as e:
        raise Exception(f"Failed to save meal plan: {str(e)}")

async def get_user_meal_plans(user_id: str):
    """Get all meal plans for a user"""
    try:
        query = f"SELECT * FROM c WHERE c.type = 'meal_plan' AND c.user_id = '{user_id}'"
        return list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
    except Exception as e:
        raise Exception(f"Failed to get meal plans: {str(e)}")

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