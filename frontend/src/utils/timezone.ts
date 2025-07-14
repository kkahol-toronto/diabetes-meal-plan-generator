/**
 * Frontend-only timezone utilities
 * Handles timezone conversion and date filtering without backend changes
 */

export interface TimezoneInfo {
  timezone: string;
  offset: number;
  displayName: string;
}

/**
 * Get the user's timezone information from the browser
 */
export function getUserTimezone(): TimezoneInfo {
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const now = new Date();
  const offset = now.getTimezoneOffset();
  
  // Get display name (e.g., "Eastern Standard Time")
  const displayName = new Intl.DateTimeFormat('en-US', {
    timeZoneName: 'long',
    timeZone: timezone
  }).formatToParts(now).find(part => part.type === 'timeZoneName')?.value || timezone;

  return {
    timezone,
    offset,
    displayName
  };
}

/**
 * Get the user's current local date (YYYY-MM-DD format)
 */
export function getUserLocalDate(): string {
  const userTimezone = getUserTimezone();
  const now = new Date();
  
  // Create a new date in the user's timezone
  const localDate = new Date(now.toLocaleString('en-US', { timeZone: userTimezone.timezone }));
  
  return localDate.toISOString().split('T')[0];
}

/**
 * Convert a UTC timestamp to user's local date
 */
export function convertUTCToLocalDate(utcTimestamp: string): string {
  const userTimezone = getUserTimezone();
  const utcDate = new Date(utcTimestamp);
  
  // Convert to user's timezone
  const localDate = new Date(utcDate.toLocaleString('en-US', { timeZone: userTimezone.timezone }));
  
  return localDate.toISOString().split('T')[0];
}

/**
 * Check if a UTC timestamp is from "today" in the user's timezone
 */
export function isToday(utcTimestamp: string): boolean {
  const todayLocal = getUserLocalDate();
  const recordDate = convertUTCToLocalDate(utcTimestamp);
  
  return recordDate === todayLocal;
}

/**
 * Get date range for last N days in user's timezone
 */
export function getLocalDateRange(days: number): { start: string; end: string } {
  const userTimezone = getUserTimezone();
  const now = new Date();
  
  // Get today in user's timezone
  const todayLocal = new Date(now.toLocaleString('en-US', { timeZone: userTimezone.timezone }));
  
  // Calculate start date (N days ago)
  const startDate = new Date(todayLocal);
  startDate.setDate(startDate.getDate() - days + 1);
  
  // Calculate end date (tomorrow to include all of today)
  const endDate = new Date(todayLocal);
  endDate.setDate(endDate.getDate() + 1);
  
  return {
    start: startDate.toISOString().split('T')[0],
    end: endDate.toISOString().split('T')[0]
  };
}

/**
 * Filter consumption records to only include those from today (user's timezone)
 */
export function filterTodayRecords<T extends { timestamp: string }>(records: T[]): T[] {
  return records.filter(record => isToday(record.timestamp));
}

/**
 * Filter consumption records for a specific date range (user's timezone)
 */
export function filterRecordsByDateRange<T extends { timestamp: string }>(
  records: T[], 
  days: number
): T[] {
  const { start, end } = getLocalDateRange(days);
  
  return records.filter(record => {
    const recordDate = convertUTCToLocalDate(record.timestamp);
    return recordDate >= start && recordDate < end;
  });
}

/**
 * Group consumption records by local date
 */
export function groupRecordsByLocalDate<T extends { timestamp: string }>(
  records: T[]
): Record<string, T[]> {
  const grouped: Record<string, T[]> = {};
  
  records.forEach(record => {
    const localDate = convertUTCToLocalDate(record.timestamp);
    
    if (!grouped[localDate]) {
      grouped[localDate] = [];
    }
    
    grouped[localDate].push(record);
  });
  
  return grouped;
}

/**
 * Calculate daily totals from consumption records using user's timezone
 */
export function calculateDailyTotalsFromRecords<T extends { 
  timestamp: string; 
  nutritional_info: any;
}>(records: T[]): {
  calories: number;
  protein: number;
  carbohydrates: number;
  fat: number;
  fiber: number;
  sugar: number;
  sodium: number;
} {
  const todayRecords = filterTodayRecords(records);
  
  const totals = {
    calories: 0,
    protein: 0,
    carbohydrates: 0,
    fat: 0,
    fiber: 0,
    sugar: 0,
    sodium: 0
  };
  
  todayRecords.forEach(record => {
    const nutrition = record.nutritional_info || {};
    totals.calories += nutrition.calories || 0;
    totals.protein += nutrition.protein || 0;
    totals.carbohydrates += nutrition.carbohydrates || 0;
    totals.fat += nutrition.fat || 0;
    totals.fiber += nutrition.fiber || 0;
    totals.sugar += nutrition.sugar || 0;
    totals.sodium += nutrition.sodium || 0;
  });
  
  return totals;
}

/**
 * Debug function to show timezone info
 */
export function debugTimezone(): void {
  const timezone = getUserTimezone();
  const localDate = getUserLocalDate();
  
  console.log('=== Timezone Debug Info ===');
  console.log('Timezone:', timezone.timezone);
  console.log('Offset:', timezone.offset);
  console.log('Display Name:', timezone.displayName);
  console.log('Local Date:', localDate);
  console.log('UTC Date:', new Date().toISOString().split('T')[0]);
  console.log('========================');
} 