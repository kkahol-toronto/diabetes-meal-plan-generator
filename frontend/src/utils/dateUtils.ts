/**
 * Utility functions for handling dates and timezones consistently across the app
 */

/**
 * Converts a UTC timestamp to local time and formats it appropriately
 * @param dateString - UTC timestamp string from backend
 * @param options - Optional formatting options
 * @returns Formatted date string in local timezone
 */
export const formatUTCToLocal = (
  dateString: string,
  options: {
    includeDate?: boolean;
    includeTime?: boolean;
    relative?: boolean;
    format?: 'short' | 'long' | 'numeric';
    profileTimezone?: string;
  } = {}
): string => {
  const {
    includeDate = true,
    includeTime = true,
    relative = false,
    format = 'short'
  } = options;

  try {
    // Handle the case where backend sends UTC timestamp without 'Z' suffix
    let processedDateString = dateString;
    
    // If the string doesn't end with 'Z' or timezone info, assume it's UTC
    if (!dateString.includes('Z') && !dateString.includes('+') && !dateString.includes('-', 10)) {
      processedDateString = dateString + 'Z';
    }
    
    const date = new Date(processedDateString);
    if (isNaN(date.getTime())) {
      return 'Invalid Date';
    }

    // Get user's timezone - use profile timezone if provided, otherwise browser detection
    const timeZone = options.profileTimezone || Intl.DateTimeFormat().resolvedOptions().timeZone;

    // Handle relative dates (Today, Yesterday, etc.)
    if (relative && includeDate) {
      const now = new Date();
      const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());
      const nowOnly = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      const diffTime = nowOnly.getTime() - dateOnly.getTime();
      const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));

      const timeString = includeTime ? date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
        timeZone
      }) : '';

      if (diffDays === 0) return includeTime ? `Today, ${timeString}` : 'Today';
      if (diffDays === 1) return includeTime ? `Yesterday, ${timeString}` : 'Yesterday';
      if (diffDays === -1) return includeTime ? `Tomorrow, ${timeString}` : 'Tomorrow';
    }

    // Build format options
    const formatOptions: Intl.DateTimeFormatOptions = { timeZone };

    if (includeDate) {
      if (format === 'long') {
        formatOptions.year = 'numeric';
        formatOptions.month = 'long';
        formatOptions.day = 'numeric';
      } else if (format === 'short') {
        formatOptions.year = 'numeric';
        formatOptions.month = 'short';
        formatOptions.day = 'numeric';
      } else {
        formatOptions.year = 'numeric';
        formatOptions.month = '2-digit';
        formatOptions.day = '2-digit';
      }
    }

    if (includeTime) {
      formatOptions.hour = '2-digit';
      formatOptions.minute = '2-digit';
      formatOptions.hour12 = true;
    }

    return date.toLocaleString('en-US', formatOptions);
  } catch (e) {
    console.error('Date formatting error:', e);
    return 'Invalid Date';
  }
};

/**
 * Formats a date for meal plan history display
 * @param dateString - UTC timestamp string
 * @returns Formatted date with relative day names
 */
export const formatMealPlanDate = (dateString: string): string => {
  return formatUTCToLocal(dateString, {
    includeDate: true,
    includeTime: true,
    relative: true,
    format: 'long'
  });
};

/**
 * Formats a timestamp for consumption history display
 * @param timestamp - UTC timestamp string
 * @returns Formatted timestamp
 */
export const formatConsumptionTimestamp = (timestamp: string): string => {
  return formatUTCToLocal(timestamp, {
    includeDate: true,
    includeTime: true,
    relative: false,
    format: 'short'
  });
};

/**
 * Gets the current timezone name
 * @returns Timezone string (e.g., "America/Toronto")
 */
export const getCurrentTimezone = (): string => {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
};

/**
 * Gets the current timezone offset in hours
 * @returns Offset in hours (e.g., -5 for EST)
 */
export const getTimezoneOffset = (): number => {
  return -new Date().getTimezoneOffset() / 60;
};

/**
 * Converts local time to UTC for sending to backend
 * @param date - Local date object or string
 * @returns ISO string in UTC
 */
export const toUTC = (date: Date | string): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return dateObj.toISOString();
}; 