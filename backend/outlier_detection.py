import numpy as np
from scipy import stats
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
from typing import List, Dict, Any
from database import get_all_patients, get_patient_by_id
from consumption_system import get_user_consumption_history
from main import group_patients_by_criteria

class OutlierDetector:
    """Advanced outlier detection for nutrition and behavior patterns"""
    
    def __init__(self):
        self.outlier_thresholds = {
            "calories": {"min": 500, "max": 4000, "iqr_multiplier": 2.5},
            "protein": {"min": 10, "max": 300, "iqr_multiplier": 2.0},
            "carbohydrates": {"min": 20, "max": 600, "iqr_multiplier": 2.0},
            "fat": {"min": 10, "max": 200, "iqr_multiplier": 2.0},
            "fiber": {"min": 0, "max": 80, "iqr_multiplier": 2.0},
            "sodium": {"min": 500, "max": 8000, "iqr_multiplier": 2.5},
            "sugar": {"min": 0, "max": 150, "iqr_multiplier": 2.0}
        }
        
        self.behavioral_thresholds = {
            "meals_per_day": {"min": 1, "max": 8},
            "eating_window_hours": {"min": 6, "max": 18},
            "late_night_eating": {"threshold_hour": 22},
            "binge_eating_calories": 1500,  # Single meal threshold
            "under_eating_daily": 800  # Daily total threshold
        }

    async def detect_nutritional_outliers(self, user_email: str, days: int = 30) -> dict:
        """Detect nutritional outliers for individual patient"""
        try:
            # Get consumption history
            consumption_history = await get_user_consumption_history(user_email, limit=300)
            
            # Filter to date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            recent_records = [
                record for record in consumption_history
                if datetime.fromisoformat(record["date"].replace('Z', '+00:00')) >= start_date
            ]
            
            if not recent_records:
                return {"user_email": user_email, "outliers": [], "summary": "No data available"}
            
            # Extract daily totals
            daily_totals = defaultdict(lambda: {
                "calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0,
                "fiber": 0, "sodium": 0, "sugar": 0, "meal_count": 0, "records": []
            })
            
            for record in recent_records:
                date = record["date"][:10]
                nutritional_info = record.get("nutritional_info", {})
                
                daily_totals[date]["calories"] += nutritional_info.get("calories", 0)
                daily_totals[date]["protein"] += nutritional_info.get("protein", 0)
                daily_totals[date]["carbohydrates"] += nutritional_info.get("carbohydrates", 0)
                daily_totals[date]["fat"] += nutritional_info.get("fat", 0)
                daily_totals[date]["fiber"] += nutritional_info.get("fiber", 0)
                daily_totals[date]["sodium"] += nutritional_info.get("sodium", 0)
                daily_totals[date]["sugar"] += nutritional_info.get("sugar", 0)
                daily_totals[date]["meal_count"] += 1
                daily_totals[date]["records"].append(record)
            
            # Detect outliers
            outliers = []
            
            # 1. Daily nutritional outliers
            for nutrient, thresholds in self.outlier_thresholds.items():
                values = [day[nutrient] for day in daily_totals.values() if day[nutrient] > 0]
                
                if len(values) < 3:  # Need minimum data points
                    continue
                
                # Calculate IQR-based outliers
                q1, q3 = np.percentile(values, [25, 75])
                iqr = q3 - q1
                lower_bound = q1 - (thresholds["iqr_multiplier"] * iqr)
                upper_bound = q3 + (thresholds["iqr_multiplier"] * iqr)
                
                # Apply absolute thresholds
                lower_bound = max(lower_bound, thresholds["min"])
                upper_bound = min(upper_bound, thresholds["max"])
                
                for date, day_data in daily_totals.items():
                    value = day_data[nutrient]
                    if value < lower_bound or value > upper_bound:
                        outliers.append({
                            "type": "nutritional_outlier",
                            "date": date,
                            "nutrient": nutrient,
                            "value": value,
                            "expected_range": f"{lower_bound:.1f} - {upper_bound:.1f}",
                            "severity": "extreme" if (value < thresholds["min"] or value > thresholds["max"]) else "moderate",
                            "direction": "low" if value < lower_bound else "high",
                            "meal_records": day_data["records"]
                        })
            
            # 2. Individual meal outliers (binge eating detection)
            for record in recent_records:
                meal_calories = record.get("nutritional_info", {}).get("calories", 0)
                if meal_calories > self.behavioral_thresholds["binge_eating_calories"]:
                    outliers.append({
                        "type": "binge_eating",
                        "date": record["date"][:10],
                        "time": record["date"][11:16],
                        "food_name": record["food_name"],
                        "calories": meal_calories,
                        "severity": "high",
                        "meal_record": record
                    })
            
            # 3. Behavioral pattern outliers
            for date, day_data in daily_totals.items():
                # Under-eating detection
                if day_data["calories"] < self.behavioral_thresholds["under_eating_daily"]:
                    outliers.append({
                        "type": "under_eating",
                        "date": date,
                        "calories": day_data["calories"],
                        "severity": "high" if day_data["calories"] < 600 else "moderate",
                        "meal_count": day_data["meal_count"]
                    })
                
                # Excessive meal frequency
                if day_data["meal_count"] > self.behavioral_thresholds["meals_per_day"]["max"]:
                    outliers.append({
                        "type": "excessive_meal_frequency",
                        "date": date,
                        "meal_count": day_data["meal_count"],
                        "severity": "moderate"
                    })
                
                # Late night eating analysis
                late_night_meals = [
                    record for record in day_data["records"]
                    if datetime.fromisoformat(record["date"]).hour >= self.behavioral_thresholds["late_night_eating"]["threshold_hour"]
                ]
                
                if len(late_night_meals) > 0:
                    late_night_calories = sum(
                        record.get("nutritional_info", {}).get("calories", 0) 
                        for record in late_night_meals
                    )
                    outliers.append({
                        "type": "late_night_eating",
                        "date": date,
                        "meals": len(late_night_meals),
                        "calories": late_night_calories,
                        "severity": "moderate" if late_night_calories < 500 else "high",
                        "meal_records": late_night_meals
                    })
            
            # Generate summary statistics
            outlier_summary = {
                "total_outliers": len(outliers),
                "high_severity": len([o for o in outliers if o.get("severity") == "high"]),
                "moderate_severity": len([o for o in outliers if o.get("severity") == "moderate"]),
                "extreme_severity": len([o for o in outliers if o.get("severity") == "extreme"]),
                "outlier_types": {},
                "most_problematic_days": [],
                "recommendations": []
            }
            
            # Count outlier types
            for outlier in outliers:
                outlier_type = outlier["type"]
                if outlier_type not in outlier_summary["outlier_types"]:
                    outlier_summary["outlier_types"][outlier_type] = 0
                outlier_summary["outlier_types"][outlier_type] += 1
            
            # Identify most problematic days
            daily_outlier_counts = defaultdict(int)
            for outlier in outliers:
                daily_outlier_counts[outlier["date"]] += 1
            
            outlier_summary["most_problematic_days"] = sorted(
                daily_outlier_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            
            # Generate recommendations
            recommendations = []
            if outlier_summary["high_severity"] > 0 or outlier_summary["extreme_severity"] > 0:
                recommendations.append({
                    "priority": "immediate",
                    "message": f"{outlier_summary['high_severity'] + outlier_summary['extreme_severity']} high-severity outliers detected",
                    "action": "Schedule immediate consultation"
                })
            
            if "binge_eating" in outlier_summary["outlier_types"]:
                recommendations.append({
                    "priority": "high",
                    "message": "Binge eating episodes detected",
                    "action": "Implement portion control strategies and mindful eating techniques"
                })
            
            if "under_eating" in outlier_summary["outlier_types"]:
                recommendations.append({
                    "priority": "high",
                    "message": "Under-eating patterns detected",
                    "action": "Assess for appetite issues and medication side effects"
                })
            
            if "late_night_eating" in outlier_summary["outlier_types"]:
                recommendations.append({
                    "priority": "medium",
                    "message": "Late night eating patterns detected",
                    "action": "Review sleep schedule and establish eating windows"
                })
            
            outlier_summary["recommendations"] = recommendations
            
            return {
                "user_email": user_email,
                "analysis_period_days": days,
                "outliers": sorted(outliers, key=lambda x: x["date"], reverse=True),
                "summary": outlier_summary
            }
            
        except Exception as e:
            print(f"Error detecting outliers for {user_email}: {e}")
            return {"user_email": user_email, "error": str(e), "outliers": [], "summary": {"total_outliers": 0}}

    async def detect_cohort_outliers(self, group_by: str = "diabetes_type", days: int = 30) -> dict:
        """Detect outliers across patient cohorts"""
        try:
            all_patients = await get_all_patients()
            grouped_patients = group_patients_by_criteria(all_patients, group_by)
            
            cohort_analysis = {}
            population_outliers = []
            
            for group_name, patients in grouped_patients.items():
                group_outliers = []
                registered_patients = []
                
                # Get registered patients for this group
                for patient in patients:
                    try:
                        # Check if patient has consumption data
                        from main import user_container
                        query = f"SELECT * FROM c WHERE c.type = 'user' AND c.registration_code = '{patient['registration_code']}'"
                        users = list(user_container.query_items(query=query, enable_cross_partition_query=True))
                        
                        if users:
                            user_email = users[0]["email"]
                            registered_patients.append({
                                "id": patient["id"],
                                "name": patient["name"],
                                "email": user_email
                            })
                    except Exception as e:
                        continue
                
                # Analyze each registered patient
                for patient in registered_patients:
                    try:
                        patient_outliers = await self.detect_nutritional_outliers(patient["email"], days)
                        
                        if patient_outliers.get("outliers"):
                            for outlier in patient_outliers["outliers"]:
                                outlier["patient_id"] = patient["id"]
                                outlier["patient_name"] = patient["name"]
                                outlier["group"] = group_name
                                group_outliers.append(outlier)
                                population_outliers.append(outlier)
                    
                    except Exception as e:
                        print(f"Error analyzing patient {patient['id']}: {e}")
                        continue
                
                # Analyze group patterns
                group_analysis = {
                    "patient_count": len(patients),
                    "registered_patients": len(registered_patients),
                    "patients_with_outliers": len(set(o["patient_id"] for o in group_outliers)),
                    "total_outliers": len(group_outliers),
                    "outlier_distribution": {},
                    "high_risk_patients": [],
                    "group_recommendations": []
                }
                
                # Count outlier types
                for outlier in group_outliers:
                    outlier_type = outlier["type"]
                    if outlier_type not in group_analysis["outlier_distribution"]:
                        group_analysis["outlier_distribution"][outlier_type] = 0
                    group_analysis["outlier_distribution"][outlier_type] += 1
                
                # Identify high-risk patients (patients with multiple high/extreme severity outliers)
                patient_risk_scores = defaultdict(int)
                for outlier in group_outliers:
                    if outlier.get("severity") in ["high", "extreme"]:
                        patient_risk_scores[outlier["patient_id"]] += 2 if outlier.get("severity") == "extreme" else 1
                
                group_analysis["high_risk_patients"] = [
                    {
                        "patient_id": pid, 
                        "patient_name": next(o["patient_name"] for o in group_outliers if o["patient_id"] == pid), 
                        "high_severity_outliers": score
                    }
                    for pid, score in patient_risk_scores.items()
                    if score >= 3  # Risk score of 3 or higher
                ]
                
                cohort_analysis[group_name] = group_analysis
            
            return {
                "grouping_criteria": group_by,
                "analysis_period_days": days,
                "total_population_outliers": len(population_outliers),
                "groups": cohort_analysis,
                "population_outliers": population_outliers[:50],  # Limit for performance
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error in detect_cohort_outliers: {str(e)}")
            raise Exception(f"Failed to detect cohort outliers: {str(e)}")

# Initialize global outlier detector
outlier_detector = OutlierDetector() 