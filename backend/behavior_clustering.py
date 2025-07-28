import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
from typing import Dict, List, Any
from database import get_user_consumption_history, get_all_patients, get_patient_by_id, get_consumption_analytics
import asyncio

class BehaviorCluster:
    """Advanced behavior clustering for patient segmentation"""
    
    def __init__(self):
        self.feature_extractors = {
            "eating_patterns": self._extract_eating_patterns,
            "nutritional_preferences": self._extract_nutritional_preferences,
            "temporal_behaviors": self._extract_temporal_behaviors,
            "compliance_patterns": self._extract_compliance_patterns,
            "engagement_behaviors": self._extract_engagement_behaviors
        }
        
        self.cluster_names = {
            0: "Consistent Health-Conscious",
            1: "Weekend Warriors", 
            2: "Night Eaters",
            3: "Under-reporters",
            4: "High Protein Advocates",
            5: "Carb Watchers",
            6: "Irregular Eaters",
            7: "Binge-Restrict Cyclers"
        }
    
    async def _extract_eating_patterns(self, user_email: str, days: int = 90) -> dict:
        """Extract eating pattern features"""
        try:
            consumption_history = await get_user_consumption_history(user_email, limit=500)
            
            # Filter to date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            recent_records = [
                record for record in consumption_history
                if datetime.fromisoformat(record.get("timestamp", record.get("date", "")).replace('Z', '+00:00')) >= start_date
            ]
            
            if not recent_records:
                return {"meals_per_day": 0, "eating_window": 12, "meal_regularity": 0}
            
            # Group by date
            daily_meals = defaultdict(list)
            for record in recent_records:
                timestamp_str = record.get("timestamp", record.get("date", ""))
                if timestamp_str:
                    date = timestamp_str[:10]
                    try:
                        hour = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')).hour
                        daily_meals[date].append(hour)
                    except:
                        continue
            
            # Calculate metrics
            meals_per_day = np.mean([len(meals) for meals in daily_meals.values()]) if daily_meals else 0
            
            # Eating window (first to last meal)
            eating_windows = []
            for meals in daily_meals.values():
                if len(meals) > 1:
                    eating_windows.append(max(meals) - min(meals))
            avg_eating_window = np.mean(eating_windows) if eating_windows else 12
            
            # Meal regularity (variance in meal times)
            meal_time_variances = []
            for meals in daily_meals.values():
                if len(meals) > 1:
                    meal_time_variances.append(np.var(meals))
            meal_regularity = 100 - np.mean(meal_time_variances) if meal_time_variances else 50
            
            return {
                "meals_per_day": float(meals_per_day),
                "eating_window": float(avg_eating_window),
                "meal_regularity": float(max(0, min(100, meal_regularity)))
            }
            
        except Exception as e:
            print(f"Error extracting eating patterns for {user_email}: {e}")
            return {"meals_per_day": 0, "eating_window": 12, "meal_regularity": 0}
    
    async def _extract_nutritional_preferences(self, user_email: str, days: int = 90) -> dict:
        """Extract nutritional preference features"""
        try:
            analytics = await get_consumption_analytics(user_email, days, "UTC")
            daily_averages = analytics.get("daily_averages", {})
            
            total_calories = daily_averages.get("calories", 1)
            
            # Calculate macro ratios
            protein_ratio = (daily_averages.get("protein", 0) * 4) / total_calories * 100 if total_calories > 0 else 0
            carb_ratio = (daily_averages.get("carbohydrates", 0) * 4) / total_calories * 100 if total_calories > 0 else 0
            fat_ratio = (daily_averages.get("fat", 0) * 9) / total_calories * 100 if total_calories > 0 else 0
            
            # Normalize to 100%
            total_ratio = protein_ratio + carb_ratio + fat_ratio
            if total_ratio > 0:
                protein_ratio = (protein_ratio / total_ratio) * 100
                carb_ratio = (carb_ratio / total_ratio) * 100
                fat_ratio = (fat_ratio / total_ratio) * 100
            
            return {
                "protein_preference": float(protein_ratio),
                "carb_preference": float(carb_ratio),
                "fat_preference": float(fat_ratio),
                "fiber_intake": float(daily_averages.get("fiber", 0)),
                "sodium_intake": float(daily_averages.get("sodium", 0)),
                "sugar_intake": float(daily_averages.get("sugar", 0))
            }
            
        except Exception as e:
            print(f"Error extracting nutritional preferences for {user_email}: {e}")
            return {
                "protein_preference": 20, "carb_preference": 50, "fat_preference": 30,
                "fiber_intake": 0, "sodium_intake": 0, "sugar_intake": 0
            }
    
    async def _extract_temporal_behaviors(self, user_email: str, days: int = 90) -> dict:
        """Extract temporal behavior features"""
        try:
            consumption_history = await get_user_consumption_history(user_email, limit=500)
            
            if not consumption_history:
                return {"night_eating_score": 0, "weekend_consistency": 50, "meal_timing_variance": 50}
            
            # Analyze meal times
            night_meals = 0  # After 10 PM
            weekend_meals = 0
            weekday_meals = 0
            meal_hours = []
            
            for record in consumption_history[:min(len(consumption_history), 200)]:
                timestamp_str = record.get("timestamp", record.get("date", ""))
                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        hour = timestamp.hour
                        weekday = timestamp.weekday()
                        
                        meal_hours.append(hour)
                        
                        if hour >= 22 or hour <= 5:  # 10 PM to 5 AM
                            night_meals += 1
                        
                        if weekday >= 5:  # Weekend
                            weekend_meals += 1
                        else:
                            weekday_meals += 1
                    except:
                        continue
            
            # Calculate scores
            night_eating_score = (night_meals / len(consumption_history)) * 100 if consumption_history else 0
            
            weekend_consistency = 50  # Default
            if weekend_meals > 0 and weekday_meals > 0:
                weekend_ratio = weekend_meals / max(weekend_meals + weekday_meals, 1)
                expected_weekend_ratio = 2/7  # 2 days out of 7
                weekend_consistency = 100 - abs(weekend_ratio - expected_weekend_ratio) * 100
            
            meal_timing_variance = np.var(meal_hours) if meal_hours else 25
            
            return {
                "night_eating_score": float(night_eating_score),
                "weekend_consistency": float(max(0, min(100, weekend_consistency))),
                "meal_timing_variance": float(min(100, meal_timing_variance * 2))
            }
            
        except Exception as e:
            print(f"Error extracting temporal behaviors for {user_email}: {e}")
            return {"night_eating_score": 0, "weekend_consistency": 50, "meal_timing_variance": 50}
    
    async def _extract_compliance_patterns(self, user_email: str, days: int = 90) -> dict:
        """Extract compliance behavior features"""
        try:
            analytics = await get_consumption_analytics(user_email, days, "UTC")
            adherence_stats = analytics.get("adherence_stats", {})
            
            return {
                "diabetes_compliance": float(adherence_stats.get("diabetes_suitable_percentage", 0)),
                "calorie_compliance": float(adherence_stats.get("calorie_goal_adherence", 0)),
                "protein_compliance": float(adherence_stats.get("protein_goal_adherence", 0)),
                "carb_compliance": float(adherence_stats.get("carb_goal_adherence", 0))
            }
            
        except Exception as e:
            print(f"Error extracting compliance patterns for {user_email}: {e}")
            return {
                "diabetes_compliance": 0, "calorie_compliance": 0,
                "protein_compliance": 0, "carb_compliance": 0
            }
    
    async def _extract_engagement_behaviors(self, user_email: str, days: int = 90) -> dict:
        """Extract engagement behavior features"""
        try:
            # Calculate engagement metrics based on consumption history
            consumption_history = await get_user_consumption_history(user_email, limit=500)
            
            if not consumption_history:
                return {
                    "logging_frequency": 0, "logging_consistency": 0,
                    "current_streak": 0, "engagement_score": 0
                }
            
            # Calculate logging frequency
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Count days with logs
            logged_dates = set()
            for record in consumption_history:
                timestamp_str = record.get("timestamp", record.get("date", ""))
                if timestamp_str:
                    try:
                        date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')).date()
                        if start_date.date() <= date <= end_date.date():
                            logged_dates.add(date)
                    except:
                        continue
            
            logging_frequency = (len(logged_dates) / days) * 100 if days > 0 else 0
            
            # Calculate consistency (variance in daily log counts)
            daily_log_counts = {}
            for record in consumption_history:
                timestamp_str = record.get("timestamp", record.get("date", ""))
                if timestamp_str:
                    try:
                        date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')).date()
                        if start_date.date() <= date <= end_date.date():
                            daily_log_counts[date] = daily_log_counts.get(date, 0) + 1
                    except:
                        continue
            
            if daily_log_counts:
                log_counts = list(daily_log_counts.values())
                consistency = 100 - (np.std(log_counts) * 10)  # Lower std = higher consistency
                consistency = max(0, min(100, consistency))
            else:
                consistency = 0
            
            # Calculate current streak
            current_streak = 0
            current_date = datetime.utcnow().date()
            while current_date in logged_dates and current_streak < 30:
                current_streak += 1
                current_date -= timedelta(days=1)
            
            # Overall engagement score
            engagement_score = (logging_frequency * 0.4 + consistency * 0.3 + min(current_streak * 3, 100) * 0.3)
            
            return {
                "logging_frequency": float(logging_frequency),
                "logging_consistency": float(consistency),
                "current_streak": float(current_streak),
                "engagement_score": float(engagement_score)
            }
            
        except Exception as e:
            print(f"Error extracting engagement behaviors for {user_email}: {e}")
            return {
                "logging_frequency": 0, "logging_consistency": 0,
                "current_streak": 0, "engagement_score": 0
            }
    
    async def extract_patient_features(self, user_email: str, days: int = 90) -> dict:
        """Extract comprehensive behavioral features for a patient"""
        try:
            features = {}
            
            # Extract all feature categories
            for category, extractor in self.feature_extractors.items():
                category_features = await extractor(user_email, days)
                for key, value in category_features.items():
                    features[f"{category}_{key}"] = value
            
            return features
            
        except Exception as e:
            print(f"Error extracting features for {user_email}: {e}")
            return {}
    
    async def cluster_patient_cohort(self, n_clusters: int = 6) -> dict:
        """Perform clustering analysis on entire patient cohort"""
        try:
            # Get all patients
            all_patients = await get_all_patients()
            
            # Extract features for all patients
            patient_features = []
            patient_info = []
            
            print(f"Extracting features for {len(all_patients)} patients...")
            
            for i, patient in enumerate(all_patients):
                print(f"Processing patient {i+1}/{len(all_patients)}: {patient['name']}")
                
                try:
                    # Check if patient has an email
                    if not patient.get("email"):
                        print(f"Skipping patient {patient['name']} - no email")
                        continue
                    
                    features = await self.extract_patient_features(patient["email"], days=90)
                    
                    if features and any(v > 0 for v in features.values()):  # Only include patients with meaningful data
                        patient_features.append(list(features.values()))
                        patient_info.append({
                            "patient_id": patient["id"],
                            "patient_name": patient["name"],
                            "email": patient["email"],
                            "condition": patient.get("condition", ""),
                            "features": features
                        })
                
                except Exception as e:
                    print(f"Error processing patient {patient['id']}: {e}")
                    continue
            
            if len(patient_features) < 2:  # Minimum 2 patients for any clustering
                return {
                    "error": f"Insufficient data: only {len(patient_features)} patients with enough data for clustering",
                    "minimum_required": max(2, n_clusters),
                    "patients_with_data": len(patient_features)
                }
            
            # Adjust n_clusters if we have fewer patients than requested clusters
            if len(patient_features) < n_clusters:
                n_clusters = len(patient_features)
            
            # Convert to numpy array and standardize
            X = np.array(patient_features)
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Perform clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X_scaled)
            
            # Perform PCA for visualization
            pca = PCA(n_components=2)
            X_pca = pca.fit_transform(X_scaled)
            
            # Organize results by cluster
            clusters = defaultdict(list)
            for i, label in enumerate(cluster_labels):
                patient_info[i]["cluster"] = int(label)
                patient_info[i]["pca_x"] = float(X_pca[i][0])
                patient_info[i]["pca_y"] = float(X_pca[i][1])
                clusters[int(label)].append(patient_info[i])
            
            # Analyze cluster characteristics
            cluster_analysis = {}
            feature_names = list(patient_info[0]["features"].keys()) if patient_info else []
            
            for cluster_id, patients in clusters.items():
                if not patients:
                    continue
                
                # Calculate cluster centroid in original feature space
                cluster_features = np.array([list(p["features"].values()) for p in patients])
                centroid = np.mean(cluster_features, axis=0)
                
                # Find most characteristic features (highest values in centroid)
                feature_importance = dict(zip(feature_names, centroid))
                top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
                
                # Generate cluster description
                cluster_description = self._generate_cluster_description(top_features, centroid, feature_names)
                
                cluster_analysis[cluster_id] = {
                    "cluster_name": self.cluster_names.get(cluster_id, f"Cluster {cluster_id}"),
                    "patient_count": len(patients),
                    "patients": patients,
                    "centroid_features": feature_importance,
                    "top_characteristics": top_features,
                    "description": cluster_description,
                    "avg_engagement": float(np.mean([p["features"].get("engagement_behaviors_engagement_score", 0) for p in patients])),
                    "avg_compliance": float(np.mean([p["features"].get("compliance_patterns_diabetes_compliance", 0) for p in patients]))
                }
            
            return {
                "total_patients_analyzed": len(patient_info),
                "n_clusters": n_clusters,
                "clusters": dict(cluster_analysis),
                "pca_visualization_data": {
                    "patients": patient_info,
                    "explained_variance_ratio": pca.explained_variance_ratio_.tolist()
                },
                "feature_names": feature_names,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error in cluster analysis: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    def _generate_cluster_description(self, top_features: list, centroid: np.ndarray, feature_names: list) -> str:
        """Generate human-readable cluster description"""
        descriptions = []
        
        # Analyze top features
        for feature, value in top_features[:3]:
            if "protein_preference" in feature and value > 25:
                descriptions.append("High protein preference")
            elif "carb_preference" in feature and value > 50:
                descriptions.append("High carbohydrate preference")
            elif "night_eating_score" in feature and value > 20:
                descriptions.append("Frequent night eating")
            elif "weekend_consistency" in feature and value < 30:
                descriptions.append("Poor weekend consistency")
            elif "logging_frequency" in feature and value > 70:
                descriptions.append("Highly engaged loggers")
            elif "diabetes_compliance" in feature and value > 70:
                descriptions.append("High diabetes compliance")
            elif "meal_timing_variance" in feature and value > 60:
                descriptions.append("Irregular meal timing")
            elif "engagement_score" in feature and value > 70:
                descriptions.append("High engagement")
            elif "meals_per_day" in feature and value > 4:
                descriptions.append("Frequent eaters")
            elif "meals_per_day" in feature and value < 2:
                descriptions.append("Infrequent eaters")
        
        if not descriptions:
            descriptions.append("Mixed behavioral patterns")
        
        return " • ".join(descriptions)

# Initialize behavior cluster analyzer
behavior_clusterer = BehaviorCluster() 