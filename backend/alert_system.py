from datetime import datetime, timedelta
from typing import List, Dict
import asyncio
from database import get_all_patients, get_patient_by_id
from outlier_detection import outlier_detector

class AlertSystem:
    """Real-time alert system for outlier detection"""
    
    def __init__(self):
        self.alert_thresholds = {
            "extreme_outlier": {"priority": "critical", "response_time_hours": 1},
            "multiple_high_outliers": {"priority": "high", "response_time_hours": 24},
            "concerning_pattern": {"priority": "medium", "response_time_hours": 72}
        }
    
    async def generate_patient_alerts(self, patient_id: str) -> List[Dict]:
        """Generate alerts for a specific patient"""
        try:
            patient = await get_patient_by_id(patient_id)
            if not patient:
                return []
            
            # Check if patient is registered
            from main import user_container
            query = f"SELECT * FROM c WHERE c.type = 'user' AND c.registration_code = '{patient['registration_code']}'"
            users = list(user_container.query_items(query=query, enable_cross_partition_query=True))
            
            if not users:
                return []
            
            user_email = users[0]["email"]
            outlier_data = await outlier_detector.detect_nutritional_outliers(user_email, days=7)
            
            alerts = []
            
            # Check for critical outliers
            extreme_outliers = [o for o in outlier_data.get("outliers", []) if o.get("severity") == "extreme"]
            if extreme_outliers:
                alerts.append({
                    "alert_id": f"critical_{patient_id}_{datetime.utcnow().isoformat()}",
                    "patient_id": patient_id,
                    "patient_name": patient["name"],
                    "alert_type": "extreme_outlier",
                    "priority": "critical",
                    "message": f"CRITICAL: {len(extreme_outliers)} extreme outliers detected",
                    "details": extreme_outliers,
                    "created_at": datetime.utcnow().isoformat(),
                    "requires_response_by": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                    "status": "active"
                })
            
            # Check for multiple high-severity outliers
            high_outliers = [o for o in outlier_data.get("outliers", []) if o.get("severity") == "high"]
            if len(high_outliers) >= 3:
                alerts.append({
                    "alert_id": f"multiple_{patient_id}_{datetime.utcnow().isoformat()}",
                    "patient_id": patient_id,
                    "patient_name": patient["name"],
                    "alert_type": "multiple_high_outliers",
                    "priority": "high",
                    "message": f"Multiple high-severity outliers: {len(high_outliers)} in 7 days",
                    "details": high_outliers,
                    "created_at": datetime.utcnow().isoformat(),
                    "requires_response_by": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
                    "status": "active"
                })
            
            # Check for concerning patterns
            if outlier_data.get("summary", {}).get("recommendations"):
                for rec in outlier_data["summary"]["recommendations"]:
                    if rec.get("priority") in ["high", "immediate"]:
                        alerts.append({
                            "alert_id": f"pattern_{patient_id}_{datetime.utcnow().isoformat()}",
                            "patient_id": patient_id,
                            "patient_name": patient["name"],
                            "alert_type": "concerning_pattern",
                            "priority": "medium",
                            "message": rec["message"],
                            "details": {"recommendation": rec},
                            "created_at": datetime.utcnow().isoformat(),
                            "requires_response_by": (datetime.utcnow() + timedelta(hours=72)).isoformat(),
                            "status": "active"
                        })
            
            return alerts
            
        except Exception as e:
            print(f"Error generating alerts for patient {patient_id}: {e}")
            return []
    
    async def generate_cohort_alerts(self) -> Dict:
        """Generate alerts for entire patient cohort"""
        try:
            all_patients = await get_all_patients()
            all_alerts = []
            
            # Generate alerts for each patient (limit to first 50 for performance)
            for patient in all_patients[:50]:
                try:
                    patient_alerts = await self.generate_patient_alerts(patient["id"])
                    all_alerts.extend(patient_alerts)
                except Exception as e:
                    print(f"Error generating alerts for patient {patient['id']}: {e}")
                    continue
            
            # Sort by priority and response time
            priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            all_alerts.sort(key=lambda x: (priority_order.get(x["priority"], 3), x["requires_response_by"]))
            
            # Generate summary
            alert_summary = {
                "total_alerts": len(all_alerts),
                "critical_alerts": len([a for a in all_alerts if a["priority"] == "critical"]),
                "high_priority_alerts": len([a for a in all_alerts if a["priority"] == "high"]),
                "medium_priority_alerts": len([a for a in all_alerts if a["priority"] == "medium"]),
                "overdue_alerts": len([
                    a for a in all_alerts 
                    if datetime.fromisoformat(a["requires_response_by"]) < datetime.utcnow()
                ]),
                "alerts": all_alerts[:20],  # Limit for frontend performance
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return alert_summary
            
        except Exception as e:
            print(f"Error generating cohort alerts: {e}")
            return {"error": str(e), "alerts": [], "total_alerts": 0}

# Initialize alert system
alert_system = AlertSystem() 