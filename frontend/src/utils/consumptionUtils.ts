/**
 * Consumption Utilities for Smart Daily Meal Plan
 * 
 * Handles formatting and calculations for consumption data display
 */

interface ConsumptionRecord {
  food_name: string;
  quantity: string;
  calories: number;
  protein: number;
  timestamp: string;
  session_id?: string;
}

interface NutritionTotals {
  calories: number;
  protein: number;
}

/**
 * Format consumption text for display
 * - Items from same session (within 5 minutes): separated by commas
 * - Items from different sessions: separated by '&'
 */
export const formatConsumptionText = (consumptionRecords: ConsumptionRecord[]): string => {
  if (!consumptionRecords || consumptionRecords.length === 0) {
    return '';
  }

  // Group by session (items within 5 minutes of each other)
  const sessions: ConsumptionRecord[][] = [];
  let currentSession: ConsumptionRecord[] = [];
  
  for (let i = 0; i < consumptionRecords.length; i++) {
    const record = consumptionRecords[i];
    
    if (currentSession.length === 0) {
      currentSession.push(record);
    } else {
      const lastRecord = currentSession[currentSession.length - 1];
      const timeDiff = Math.abs(
        new Date(record.timestamp).getTime() - new Date(lastRecord.timestamp).getTime()
      );
      
      // If within 5 minutes (300000 ms), add to current session
      if (timeDiff <= 300000) {
        currentSession.push(record);
      } else {
        // Start new session
        sessions.push([...currentSession]);
        currentSession = [record];
      }
    }
  }
  
  // Add the last session
  if (currentSession.length > 0) {
    sessions.push(currentSession);
  }

  // Format each session
  const sessionTexts = sessions.map(session => {
    return session.map(record => record.food_name).join(', ');
  });

  // Join sessions with '&'
  return sessionTexts.join(' & ');
};

/**
 * Calculate total nutrition from consumption records
 */
export const getTotalNutrition = (consumptionRecords: ConsumptionRecord[]): NutritionTotals => {
  if (!consumptionRecords || consumptionRecords.length === 0) {
    return { calories: 0, protein: 0 };
  }

  const totals = consumptionRecords.reduce(
    (acc, record) => ({
      calories: acc.calories + (record.calories || 0),
      protein: acc.protein + (record.protein || 0),
    }),
    { calories: 0, protein: 0 }
  );

  return {
    calories: Math.round(totals.calories),
    protein: Math.round(totals.protein * 10) / 10, // Round to 1 decimal place
  };
};

/**
 * Check if consumption matches planned meal
 * Uses keyword matching to determine if what was consumed matches what was planned
 */
export const isConsumptionMatchingPlan = (
  plannedMealName: string,
  consumptionText: string
): boolean => {
  if (!plannedMealName || !consumptionText) {
    return false;
  }

  const plannedName = plannedMealName.toLowerCase();
  const consumedText = consumptionText.toLowerCase();
  
  // Extract keywords from planned meal name (words longer than 3 characters)
  const plannedKeywords = plannedName.split(/\s+/).filter((word: string) => word.length > 3);
  
  // Check if any planned keywords appear in consumed text
  return plannedKeywords.some((keyword: string) => consumedText.includes(keyword));
};

/**
 * Get meal type emoji
 */
export const getMealEmoji = (mealType: string): string => {
  const emojiMap: { [key: string]: string } = {
    breakfast: '🍳',
    lunch: '🥗', 
    dinner: '🍽️',
    snack: '🍪'
  };
  
  return emojiMap[mealType.toLowerCase()] || '🍽️';
};