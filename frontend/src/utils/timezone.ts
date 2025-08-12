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
 * Get the user's timezone information - prioritizing profile timezone over browser detection
 */
export function getUserTimezone(profileTimezone?: string): TimezoneInfo {
  // Use profile timezone if available, otherwise fall back to browser detection
  const timezone = profileTimezone || Intl.DateTimeFormat().resolvedOptions().timeZone;
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
 * Get the user's current local date (YYYY-MM-DD format) in their profile timezone
 */
export function getUserLocalDate(profileTimezone?: string): string {
  const timezone = profileTimezone || Intl.DateTimeFormat().resolvedOptions().timeZone;
  const now = new Date();
  
  // Use the user's timezone to get the correct local date
  const localDate = new Intl.DateTimeFormat('en-CA', {
    timeZone: timezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).format(now);
  
  return localDate; // Returns YYYY-MM-DD format
}

/**
 * Convert a UTC timestamp to user's local date in their profile timezone
 */
export function convertUTCToLocalDate(utcTimestamp: string, profileTimezone?: string): string {
  if (!utcTimestamp) return '';
  
  try {
    const date = new Date(utcTimestamp);
    if (isNaN(date.getTime())) return '';
    
    const timezone = profileTimezone || Intl.DateTimeFormat().resolvedOptions().timeZone;
    
    // Convert to local date using user's timezone
    const localDate = new Intl.DateTimeFormat('en-CA', {
      timeZone: timezone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    }).format(date);
    
    return localDate; // Returns YYYY-MM-DD format
  } catch (error) {
    console.error('Error converting UTC to local date:', error);
    return '';
  }
}

/**
 * Check if a UTC timestamp is from "today" in the user's timezone
 */
export function isToday(utcTimestamp: string, profileTimezone?: string): boolean {
  const todayLocal = getUserLocalDate(profileTimezone);
  const recordDate = convertUTCToLocalDate(utcTimestamp, profileTimezone);
  
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
export function filterTodayRecords<T extends { timestamp: string }>(records: T[], profileTimezone?: string): T[] {
  return records.filter(record => isToday(record.timestamp, profileTimezone));
}

/**
 * Filter consumption records for a specific date range (user's timezone)
 */
export function filterRecordsByDateRange<T extends { timestamp: string }>(
  records: T[], 
  days: number,
  profileTimezone?: string
): T[] {
  const { start, end } = getLocalDateRange(days);
  
  return records.filter(record => {
    const recordDate = convertUTCToLocalDate(record.timestamp, profileTimezone);
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

/**
 * Safely parse a YYYY-MM-DD string as a LOCAL date (midnight in local tz).
 * new Date('YYYY-MM-DD') is treated as UTC in JS and can render as previous day
 * for users behind UTC. This helper avoids that off-by-one.
 */
export function parseLocalYMD(dateStr: string): Date {
  try {
    if (!dateStr || typeof dateStr !== 'string') return new Date(NaN);
    const [yearStr, monthStr, dayStr] = dateStr.split('-');
    const year = parseInt(yearStr, 10);
    const month = parseInt(monthStr, 10);
    const day = parseInt(dayStr, 10);
    if (Number.isNaN(year) || Number.isNaN(month) || Number.isNaN(day)) {
      return new Date(dateStr);
    }
    // JS Date(y, mIndex, d) constructs a local-time date at midnight
    return new Date(year, month - 1, day);
  } catch {
    return new Date(dateStr);
  }
}

/**
 * Convenience: format a YYYY-MM-DD as a localized label using local midnight.
 */
export function formatLocalYMD(
  dateStr: string,
  locale: string = 'en-US',
  options: Intl.DateTimeFormatOptions = { weekday: 'short', month: 'short', day: 'numeric' }
): string {
  const d = parseLocalYMD(dateStr);
  return isNaN(d.getTime()) ? dateStr : d.toLocaleDateString(locale, options);
}

/**
 * Convert a UTC timestamp to a localized HH:MM string in user's timezone.
 */
export function formatLocalTime(
  utcTimestamp: string,
  profileTimezone?: string,
  locale: string = 'en-US',
  options: Intl.DateTimeFormatOptions = { hour: '2-digit', minute: '2-digit', hour12: false }
): string {
  if (!utcTimestamp) return '';
  const date = new Date(utcTimestamp);
  if (isNaN(date.getTime())) return '';
  const timezone = profileTimezone || Intl.DateTimeFormat().resolvedOptions().timeZone;
  return new Intl.DateTimeFormat(locale, { timeZone: timezone, ...options }).format(date);
}