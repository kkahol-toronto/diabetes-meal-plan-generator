export interface ConsumptionRecord {
  id: string;
  timestamp: string;
  food_name: string;
  estimated_portion: string;
  nutritional_info: {
    calories: number;
    carbohydrates: number;
    protein: number;
    fat: number;
    fiber: number;
    sugar: number;
    sodium: number;
  };
  medical_rating: {
    diabetes_suitability: string;
    glycemic_impact: string;
    recommended_frequency: string;
    portion_recommendation: string;
  };
  image_analysis: string;
  image_url: string;
}

export interface Analytics {
  period_days?: number;
  total_records?: number;
  total_calories?: number;
  average_daily_calories?: number;
  total_macronutrients: {
    carbohydrates: number;
    protein: number;
    fat: number;
  };
  micronutrients?: {
    [key: string]: {
      consumed: number;
      recommended: number;
    };
  };
  diabetes_suitable_percentage?: number;
  consumption_records: ConsumptionRecord[];
} 