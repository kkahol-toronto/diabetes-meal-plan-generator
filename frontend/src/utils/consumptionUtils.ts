/**
 * Utility functions for Smart Daily Meal Plan consumption display
 * 
 * Handles the multiple food logging display logic:
 * - Multiple foods in same logging: separated by commas
 * - Multiple separate loggings for same meal: separated by & sign
 */

export interface ConsumptionRecord {
  food_name: string;
  estimated_portion?: string;
  nutritional_info?: {
    calories?: number;
    protein?: number;
    carbohydrates?: number;
    fat?: number;
  };
  timestamp: string;
  id: string;
}

export interface ConsumptionByMeal {
  breakfast: ConsumptionRecord[];
  lunch: ConsumptionRecord[];
  dinner: ConsumptionRecord[];
  snack: ConsumptionRecord[];
}

/**
 * Format consumption records for display in Smart Daily Meal Plan
 * 
 * Groups foods by logging session (based on timestamp proximity) and formats them:
 * - Foods from same logging session: separated by commas
 * - Different logging sessions for same meal: separated by &
 * 
 * @param consumptionRecords - Array of consumption records for a meal type
 * @returns Formatted string for display
 */
export function formatConsumptionForDisplay(consumptionRecords: ConsumptionRecord[]): string {
  if (!consumptionRecords || consumptionRecords.length === 0) {
    return "";
  }

  // Sort records by timestamp
  const sortedRecords = [...consumptionRecords].sort((a, b) => 
    new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  // Group records by logging session (within 5 minutes of each other)
  const loggingSessions: ConsumptionRecord[][] = [];
  let currentSession: ConsumptionRecord[] = [];

  for (let i = 0; i < sortedRecords.length; i++) {
    const record = sortedRecords[i];
    
    if (currentSession.length === 0) {
      currentSession.push(record);
    } else {
      const lastRecord = currentSession[currentSession.length - 1];
      const timeDiff = new Date(record.timestamp).getTime() - new Date(lastRecord.timestamp).getTime();
      
      // If within 5 minutes (300,000 ms), consider same logging session
      if (timeDiff <= 300000) {
        currentSession.push(record);
      } else {
        // Start new session
        loggingSessions.push([...currentSession]);
        currentSession = [record];
      }
    }
  }
  
  // Add the last session
  if (currentSession.length > 0) {
    loggingSessions.push(currentSession);
  }

  // Format each session
  const sessionStrings = loggingSessions.map(session => {
    // Within a session, separate foods by commas
    return session.map(record => record.food_name).join(", ");
  });

  // Separate sessions with &
  return sessionStrings.join(" & ");
}

/**
 * Get total nutritional info for consumed foods in a meal type
 */
export function getTotalNutritionForMeal(consumptionRecords: ConsumptionRecord[]): {
  calories: number;
  protein: number;
  carbohydrates: number;
  fat: number;
} {
  if (!consumptionRecords || consumptionRecords.length === 0) {
    return { calories: 0, protein: 0, carbohydrates: 0, fat: 0 };
  }

  return consumptionRecords.reduce((totals, record) => {
    const nutrition = record.nutritional_info || {};
    return {
      calories: totals.calories + (nutrition.calories || 0),
      protein: totals.protein + (nutrition.protein || 0),
      carbohydrates: totals.carbohydrates + (nutrition.carbohydrates || 0),
      fat: totals.fat + (nutrition.fat || 0)
    };
  }, { calories: 0, protein: 0, carbohydrates: 0, fat: 0 });
}

/**
 * Check if a meal has been consumed (has any consumption records)
 */
export function isMealConsumed(mealType: string, consumptionByMeal: ConsumptionByMeal): boolean {
  const records = consumptionByMeal[mealType as keyof ConsumptionByMeal];
  return records && records.length > 0;
}

/**
 * Get consumption status for a meal type
 */
export function getMealConsumptionStatus(
  mealType: string, 
  consumptionByMeal: ConsumptionByMeal,
  plannedMeal?: any
): {
  isConsumed: boolean;
  consumptionText: string;
  isMatchingPlan: boolean;
  totalNutrition: { calories: number; protein: number; carbohydrates: number; fat: number };
} {
  const records = consumptionByMeal[mealType as keyof ConsumptionByMeal] || [];
  const isConsumed = records.length > 0;
  const consumptionText = formatConsumptionForDisplay(records);
  const totalNutrition = getTotalNutritionForMeal(records);
  
  // Simple matching logic - could be enhanced
  let isMatchingPlan = false;
  if (plannedMeal && isConsumed) {
    const plannedName = plannedMeal.meal_name?.toLowerCase() || "";
    const consumedText = consumptionText.toLowerCase();
    
    // Basic keyword matching - this could be improved with more sophisticated logic
    const plannedKeywords = plannedName.split(/\s+/).filter((word: string) => word.length > 3);
    isMatchingPlan = plannedKeywords.some((keyword: string) => consumedText.includes(keyword));
  }
  
  return {
    isConsumed,
    consumptionText,
    isMatchingPlan,
    totalNutrition
  };
}

/**
 * Format time for display (e.g., "2:30 PM")
 */
export function formatTimeForDisplay(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return "";
  }
}

/**
 * Get meal type icon/emoji
 */
export function getMealTypeIcon(mealType: string): string {
  const icons: { [key: string]: string } = {
    breakfast: "🌅",
    lunch: "☀️", 
    dinner: "🌙",
    snack: "🍎"
  };
  
  return icons[mealType] || "🍽️";
}

/**
 * Get consumption display color based on status
 */
export function getConsumptionStatusColor(
  isConsumed: boolean, 
  isMatchingPlan: boolean
): { backgroundColor: string; borderColor: string; textColor: string } {
  if (!isConsumed) {
    return {
      backgroundColor: 'rgba(255, 255, 255, 0.15)',
      borderColor: 'rgba(255, 255, 255, 0.3)',
      textColor: 'rgba(255, 255, 255, 0.7)'
    };
  }
  
  if (isMatchingPlan) {
    return {
      backgroundColor: 'rgba(76, 175, 80, 0.2)',
      borderColor: 'rgba(76, 175, 80, 0.8)',
      textColor: 'white'
    };
  }
  
  return {
    backgroundColor: 'rgba(255, 193, 7, 0.2)',
    borderColor: 'rgba(255, 193, 7, 0.8)',
    textColor: 'white'
  };
}