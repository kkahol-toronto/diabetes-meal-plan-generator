from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr

class User(Dict[str, Any]):
    """
    User model that extends Dict to support both dictionary and object access patterns.
    This allows compatibility with both the Cosmos DB document model and FastAPI's dependency injection.
    """
    pass 