"""
Pending Consumption System
Handles temporary food analysis records before user accepts/edits/deletes them
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import asyncio
from dataclasses import dataclass, asdict
import json

@dataclass
class PendingConsumption:
    """Represents a pending consumption record awaiting user action"""
    id: str
    user_email: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    food_name: str
    estimated_portion: str
    nutritional_info: Dict[str, Any]
    medical_rating: Dict[str, Any]
    analysis_notes: str
    image_url: Optional[str] = None
    meal_type: Optional[str] = None
    analysis_mode: str = "analysis"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['expires_at'] = self.expires_at.isoformat()
        return data
    
    def is_expired(self) -> bool:
        """Check if the pending record has expired"""
        return datetime.utcnow() > self.expires_at

class PendingConsumptionManager:
    """Manages pending consumption records in memory"""
    
    def __init__(self, expiry_minutes: int = 30):
        self._pending_records: Dict[str, PendingConsumption] = {}
        self._expiry_minutes = expiry_minutes
        # Start cleanup task
        asyncio.create_task(self._cleanup_expired_records())
    
    async def create_pending_record(
        self,
        user_email: str,
        user_id: str,
        analysis_data: Dict[str, Any],
        image_url: Optional[str] = None,
        meal_type: Optional[str] = None,
        analysis_mode: str = "analysis"
    ) -> str:
        """Create a new pending consumption record"""
        
        pending_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(minutes=self._expiry_minutes)
        
        pending_record = PendingConsumption(
            id=pending_id,
            user_email=user_email,
            user_id=user_id,
            created_at=created_at,
            expires_at=expires_at,
            food_name=analysis_data.get("food_name", "Unknown food"),
            estimated_portion=analysis_data.get("estimated_portion", "Unknown portion"),
            nutritional_info=analysis_data.get("nutritional_info", {}),
            medical_rating=analysis_data.get("medical_rating", {}),
            analysis_notes=analysis_data.get("analysis_notes", ""),
            image_url=image_url,
            meal_type=meal_type,
            analysis_mode=analysis_mode
        )
        
        self._pending_records[pending_id] = pending_record
        
        print(f"[PendingConsumption] Created pending record {pending_id} for user {user_email}")
        return pending_id
    
    def get_pending_record(self, pending_id: str) -> Optional[PendingConsumption]:
        """Get a pending record by ID"""
        print(f"[PendingConsumptionManager] Attempting to get pending record with ID: {pending_id}")
        record = self._pending_records.get(pending_id)
        
        if record:
            print(f"[PendingConsumptionManager] Found record for ID: {pending_id}. Expires at: {record.expires_at.isoformat()}. Current UTC: {datetime.utcnow().isoformat()}")
            if record.is_expired():
                # Remove expired record
                self._pending_records.pop(pending_id, None)
                print(f"[PendingConsumptionManager] Removed expired record {pending_id} due to expiry.")
                return None
                
            print(f"[PendingConsumptionManager] Record {pending_id} is valid and not expired.")
            return record
        
        print(f"[PendingConsumptionManager] Record with ID: {pending_id} not found.")
        return record
    
    def update_pending_record(
        self,
        pending_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update a pending record with new data"""
        record = self.get_pending_record(pending_id)
        if not record:
            return False
        
        # Update allowed fields
        if 'food_name' in updates:
            record.food_name = updates['food_name']
        if 'estimated_portion' in updates:
            record.estimated_portion = updates['estimated_portion']
        if 'nutritional_info' in updates:
            record.nutritional_info = updates['nutritional_info']
        if 'meal_type' in updates:
            record.meal_type = updates['meal_type']
        if 'analysis_notes' in updates:
            record.analysis_notes = updates['analysis_notes']
            
        print(f"[PendingConsumption] Updated pending record {pending_id}")
        return True
    
    def delete_pending_record(self, pending_id: str) -> bool:
        """Delete a pending record"""
        if pending_id in self._pending_records:
            del self._pending_records[pending_id]
            print(f"[PendingConsumption] Deleted pending record {pending_id}")
            return True
        return False
    
    def get_user_pending_records(self, user_email: str) -> list[PendingConsumption]:
        """Get all pending records for a user"""
        records = []
        for record in self._pending_records.values():
            if record.user_email == user_email and not record.is_expired():
                records.append(record)
        return records
    
    async def _cleanup_expired_records(self):
        """Background task to clean up expired records"""
        while True:
            try:
                current_time = datetime.utcnow()
                expired_ids = [
                    record_id for record_id, record in self._pending_records.items()
                    if record.expires_at <= current_time
                ]
                
                for record_id in expired_ids:
                    del self._pending_records[record_id]
                    print(f"[PendingConsumption] Cleaned up expired record {record_id}")
                
                # Sleep for 5 minutes before next cleanup
                await asyncio.sleep(300)
            except Exception as e:
                print(f"[PendingConsumption] Error in cleanup task: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute on error

# Global instance
pending_consumption_manager = PendingConsumptionManager() 