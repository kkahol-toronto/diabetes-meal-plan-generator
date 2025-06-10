export interface NutrientData {
  name: string;
  total: number;
  goal: number;
  unit: string;
}

export interface MacroData {
  name: string;
  amount: number;
  percentage: number;
  goal: number;
  color: string;
}

export interface FoodItem {
  name: string;
  amount: number;
}

export interface NutritionData {
  calories: {
    total: number;
    goal: number;
    weeklyData: Array<{
      day: string;
      total: number;
      macros: {
        carbs: number;
        fat: number;
        protein: number;
      };
    }>;
    highestItems: FoodItem[];
  };
  nutrients: NutrientData[];
  macros: {
    carbs: MacroData;
    fat: MacroData;
    protein: MacroData;
    highestItems: FoodItem[];
  };
}

export const MACRO_COLORS = {
  carbs: '#4DB6AC',  // Teal
  fat: '#CE93D8',    // Purple
  protein: '#FFB74D' // Orange
} as const; 