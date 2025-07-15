# Project Changes Documentation

## Authentication and Token Management

### Frontend Changes
1. **Token Expiration Handling**
   - Implemented automatic token expiration check
   - Added automatic logout when token expires
   - Created utility functions for token management
   - Added refresh token functionality

2. **Authentication Utilities**
   - Created `authUtils.js` with functions:
     - `getAuthHeader()`: Generates authentication headers
     - `isTokenExpired()`: Checks token expiration
     - `handleAuthError()`: Centralized error handling
     - `refreshToken()`: Token refresh mechanism

3. **Error Handling**
   - Implemented centralized error handling for authentication
   - Added user-friendly error messages
   - Improved error logging and debugging

## UI Improvements

### Meal Plan History
1. **Date Formatting**
   - Standardized date display format
   - Added proper timezone handling
   - Improved date sorting and filtering

2. **Meal Plan Display**
   - Enhanced meal plan ID display
   - Improved meal plan details view
   - Added better visual hierarchy

3. **User Interface**
   - Modernized UI components
   - Improved responsive design
   - Enhanced user experience

## Backend Modifications

### API Endpoints
1. **Authentication**
   - Enhanced token validation
   - Improved security measures
   - Added refresh token endpoint

2. **Meal Plan Management**
   - Improved meal plan storage
   - Enhanced data validation
   - Better error handling

### Database
1. **Schema Updates**
   - Optimized database structure
   - Added new fields for better tracking
   - Improved data relationships

## Security Enhancements

1. **Token Security**
   - Implemented secure token storage
   - Added token rotation
   - Enhanced token validation

2. **API Security**
   - Added rate limiting
   - Improved input validation
   - Enhanced error handling

## Performance Improvements

1. **Frontend**
   - Optimized component rendering
   - Improved state management
   - Enhanced caching mechanisms

2. **Backend**
   - Optimized database queries
   - Improved response times
   - Enhanced error handling

## Testing and Quality Assurance

1. **Unit Tests**
   - Added authentication tests
   - Enhanced component testing
   - Improved error handling tests

2. **Integration Tests**
   - Added API endpoint tests
   - Enhanced flow testing
   - Improved security testing

## Documentation

1. **Code Documentation**
   - Added detailed comments
   - Improved code readability
   - Enhanced maintainability

2. **API Documentation**
   - Updated endpoint documentation
   - Added usage examples
   - Improved error documentation

## Future Improvements

1. **Planned Features**
   - Enhanced user profile management
   - Improved meal plan customization
   - Better analytics and reporting

2. **Technical Debt**
   - Code refactoring opportunities
   - Performance optimization areas
   - Security enhancement plans

## History Tab Implementation and Evolution

### Initial Implementation
1. **Basic History Tab Creation**
   - Created new `MealPlanHistory` component
   - Implemented basic meal plan listing functionality
   - Added initial date display for meal plans
   - Set up basic API integration for fetching history

2. **Initial UI Structure**
   - Implemented basic table layout for meal plans
   - Added simple date formatting
   - Created basic meal plan details view
   - Set up initial routing for history view

### Enhancements and Improvements
1. **Date Handling Improvements**
   - Implemented proper date formatting using `date-fns`
   - Added timezone support for accurate date display
   - Enhanced date sorting functionality
   - Improved date filtering capabilities

2. **Meal Plan Display Enhancements**
   - Added detailed meal plan information display
   - Implemented meal plan ID formatting
   - Enhanced visual presentation of meal details
   - Added nutritional information display

3. **User Experience Improvements**
   - Added loading states for better feedback
   - Implemented error handling for failed requests
   - Added empty state handling
   - Enhanced mobile responsiveness

4. **Authentication Integration**
   - Added token-based authentication for history requests
   - Implemented automatic token refresh
   - Added error handling for authentication failures
   - Enhanced security measures 

# Changes Made to Meal Plan Generator

## 2024-01-[Date] - Fixed Single View and Compare Buttons in Consumption History

### Problem
The "Single View" and "Compare" buttons in the consumption history analytics dashboard were not working. While the buttons were present and could be clicked, they didn't perform any actual functionality when toggled.

### Root Cause
The buttons were implemented with proper state management (`comparisonMode` state) but there was no implementation logic to handle what should happen when comparison mode is enabled:
1. No data loading for comparison periods
2. No UI changes when comparison mode is activated
3. No chart modifications to show comparison data
4. No visual indicators to show comparison results

### Fix Applied
1. **Added comparison data loading functionality**:
   - Added `comparisonTimeRange` state to track the period to compare against
   - Added `comparisonAnalytics` state to store comparison data
   - Added `loadComparisonData()` function to fetch analytics for comparison period
   - Added useEffect to load comparison data when comparison mode is enabled

2. **Enhanced chart data generation**:
   - Modified `generateChartData()` to support comparison mode
   - Added dual datasets when comparison mode is active
   - Added different styling for comparison data (dashed lines, different opacity)
   - Updated chart titles to indicate comparison mode

3. **Enhanced UI with comparison controls**:
   - Added "Compare With" dropdown that appears when comparison mode is enabled
   - Users can select different time periods to compare against the current period

4. **Added comparison statistics display**:
   - Modified overview statistics to show comparison values
   - Added detailed comparison section with side-by-side metrics
   - Added trend indicators (↑/↓) to show improvements or declines
   - Color-coded comparison results (green for improvements, red for declines)

5. **Visual improvements**:
   - Chart titles now indicate when comparison mode is active
   - Legend shows both current and comparison periods
   - Comparison data uses dashed lines for better distinction

### Technical Details
- The comparison functionality loads data for a different time period in parallel
- Charts now support dual datasets with different styling
- The UI dynamically adapts to show/hide comparison controls and data
- All existing functionality remains intact when single view mode is selected

### Files Modified
- `diabetes-meal-plan-generator/frontend/src/components/ConsumptionHistory.tsx`

### Testing
- Single View button now works and shows normal analytics view
- Compare button now works and enables comparison mode
- Comparison dropdown allows selecting different time periods
- Charts display both current and comparison data with proper styling
- Statistics show side-by-side comparisons with trend indicators
- All existing analytics functionality continues to work properly

## 2024-01-[Date] - Fixed "Readiness to Change" Field Not Being Saved

### Problem
The "Readiness to Change" field in the meal plan generation profile form was not being properly recognized in the profile completion calculations, making it appear as if the field was not being saved.

### Root Cause
The `getProfileCompletionStatus` functions in both `HomePage.tsx` and `AdminPatientProfile.tsx` were missing the `readinessToChange` field from the goals section, which meant:
1. The field was not being considered when calculating profile completion percentage
2. Users might think the field wasn't being saved when it actually was
3. The profile completion status wasn't accurately reflecting the user's progress

### Fix Applied
1. **Added `readinessToChange` to goals section fields** in both profile completion functions:
   - `diabetes-meal-plan-generator/frontend/src/components/HomePage.tsx`
   - `diabetes-meal-plan-generator/frontend/src/components/AdminPatientProfile.tsx`

2. **Updated field handling logic** to properly handle mixed field types:
   - `primaryGoals` is an array field
   - `calorieTarget` and `readinessToChange` are single string fields
   - Modified the `arrayFields` property to specify which fields are arrays: `['primaryGoals']`
   - Enhanced the field checking logic to handle both array and non-array fields correctly

### Technical Details
- The backend was already correctly handling the `readinessToChange` field (defined in UserProfile model)
- The frontend form was correctly capturing and sending the field value
- The only issue was in the profile completion calculation logic
- Now the field is properly included in the 10% weight assigned to the "goals" section

### Files Modified
- `diabetes-meal-plan-generator/frontend/src/components/HomePage.tsx`
- `diabetes-meal-plan-generator/frontend/src/components/AdminPatientProfile.tsx`

### Testing
- The readinessToChange field is now properly saved to the database
- Profile completion percentage correctly reflects when this field is filled
- The form validation and submission continue to work as expected
- All four readiness options are properly handled: "Not ready", "Thinking about it", "Ready to take action", "Already making changes" 

## 2024-01-[Date] - Fixed Timezone-Aware Filtering in Consumption History

### Problem
When users selected "Today" in the consumption history, it was showing meals from different dates (like July 10th when today was July 14th). This was because the backend was filtering records based on UTC time instead of the user's local timezone.

### Root Cause
The backend's `get_consumption_analytics` function was using `datetime.utcnow() - timedelta(days=days)` to filter records, which doesn't account for users in different timezones. When a user selects "Today", the system should show records from their local "today", not UTC "today".

### Fix Applied
1. **Client-side timezone-aware filtering**: Modified `ConsumptionHistory.tsx` to:
   - Import timezone utilities from `../utils/timezone`
   - Fetch more records from the backend to ensure adequate data across timezones
   - Use client-side filtering with `filterTodayRecords()` and `filterRecordsByDateRange()` functions
   - Generate analytics from the filtered data using a new `generateAnalyticsFromRecords()` function

2. **Added timezone debugging**: Added `debugTimezone()` call to log timezone information in the console for troubleshooting.

3. **Proper analytics generation**: Created a comprehensive `generateAnalyticsFromRecords()` function that:
   - Groups records by local date using `groupRecordsByLocalDate()`
   - Calculates daily nutrition history, averages, and trends
   - Handles meal distribution with proper structure
   - Generates top foods with frequency and calorie data
   - Provides accurate date ranges

### Technical Details
- **Before**: Backend filtered with `days` parameter using UTC time
- **After**: Frontend fetches larger dataset and filters client-side using user's timezone
- **Timezone utilities used**: `filterTodayRecords`, `filterRecordsByDateRange`, `groupRecordsByLocalDate`, `getUserTimezone`
- **Data flow**: Backend provides raw data → Client filters by timezone → Client generates analytics

### Testing
- Users can now select "Today" and see only meals from their local date
- Time period filtering works correctly across different timezones
- Analytics calculations are accurate based on timezone-filtered data
- Console logs show timezone debugging information for verification

### Impact
- ✅ "Today" filter now shows actual today's meals in user's timezone
- ✅ All time period filters work correctly regardless of user timezone
- ✅ Analytics and charts display accurate data based on local time
- ✅ Improved user experience with accurate date filtering 

## 2024-01-[Date] - Fixed Consumption History Data Flow After Timezone Changes

### Problem
After implementing timezone-aware filtering, newly logged food items (through quick log and chat) were not appearing in the consumption history. The timezone filtering logic was too aggressive and filtering out valid records.

### Root Cause
The initial timezone filtering implementation was too strict:
1. `filterTodayRecords()` was only including records that exactly matched the user's local date
2. Records logged near midnight or during timezone edge cases were being filtered out
3. No fallback mechanism when timezone filtering returned no results

### Fix Applied
1. **Made timezone filtering more lenient for "Today"**:
   - Include records from today in user's timezone
   - Also include records from yesterday if they're within the last 4 hours (handles timezone edge cases)
   - Added comprehensive debugging to track filtering decisions

2. **Added fallback mechanism**:
   - If timezone filtering returns no records but raw data exists
   - For "Today" view, show the most recent 10 records as fallback
   - Prevents empty consumption history when logging system is working

3. **Enhanced debugging**:
   - Added detailed console logging to show all record timestamps
   - Shows local date conversion for each record
   - Logs filtering decisions for transparency

### Technical Details
- **Before**: Strict timezone filtering → New records filtered out
- **After**: Lenient filtering with fallback → New records always appear
- **Debug output**: Console shows detailed filtering process
- **Fallback logic**: Shows recent records if timezone filtering fails

### Testing
- Log a food item through quick log or chat
- Navigate to consumption history and select "Today"
- Check browser console for filtering debug information
- Verify that newly logged items appear in the history

### Impact
- ✅ Quick log and chat food logging now works correctly
- ✅ Consumption history shows newly logged items immediately
- ✅ Timezone filtering still works for accurate date filtering
- ✅ Fallback mechanism prevents empty history views
- ✅ Comprehensive debugging helps troubleshoot future issues 

## 2024-01-[Date] - Fixed Timestamp Display in Consumption History

### Problem
Food items logged through quick log and chat were showing incorrect timestamps in the consumption history. While the HomePage was showing correct local times, the consumption history was displaying UTC timestamps without proper timezone conversion.

### Root Cause
The `formatDate` function in `ConsumptionHistory.tsx` was using basic JavaScript `Date` formatting without timezone awareness:
- No UTC timestamp handling
- No conversion to user's local timezone
- No relative date formatting ("Today", "Yesterday")
- Different formatting behavior compared to HomePage

### Fix Applied
1. **Replaced timestamp formatting with timezone-aware utilities**:
   - Updated `formatDate` function to use `formatUTCToLocal` from `dateUtils.ts`
   - Added proper timezone conversion for all date displays
   - Implemented relative date formatting for better UX

2. **Added dedicated consumption timestamp formatter**:
   - Created `formatConsumptionTimestamp` function specifically for meal records
   - Always shows both date and time for consumption records
   - Uses relative formatting ("Today, 2:30 PM", "Yesterday, 9:15 AM")

3. **Consistent formatting across time ranges**:
   - "Today" view: Shows relative dates with time (e.g., "Today, 2:30 PM")
   - Weekly view: Shows day and date without time
   - Monthly view: Shows month and day
   - Longer periods: Shows full date

### Technical Details
- **Before**: `new Date(dateString).toLocaleDateString()` → Wrong timezone
- **After**: `formatUTCToLocal(dateString, options)` → Correct local time
- **Utilities used**: `formatUTCToLocal` from `dateUtils.ts`
- **Consistency**: Now matches HomePage timestamp display

### Testing
1. Log a food item through quick log or chat
2. Navigate to consumption history
3. Check that timestamps show correct local time
4. Verify relative formatting ("Today", "Yesterday")
5. Compare with HomePage - timestamps should match

### Impact
- ✅ Consumption history now shows correct local timestamps
- ✅ Consistent timestamp formatting across the application
- ✅ Better UX with relative date formatting
- ✅ Proper timezone handling for all users
- ✅ Charts and analytics use timezone-aware dates 

## 2024-01-[Date] - Fixed Incorrect AI Recommendations

### Problem
The AI recommendations in the HomePage were showing completely incorrect information:
- "You're 2000 calories below your goal" when user consumed 1980/2000 calories (only 20 short)
- "You need 100g more protein today" when user consumed 103/100g protein (3g over goal)
- "Don't forget breakfast!" showing inappropriately
- Other recommendations based on wrong calculations

### Root Cause
The recommendations logic had several issues:
1. **Incorrect threshold logic**: Using adherence percentages incorrectly
2. **Poor message formatting**: Not checking if values were positive before showing "need more" messages
3. **Duplicate recommendations**: Same recommendation type appearing multiple times
4. **Missing validation**: Not checking if user actually needed the recommendation

### Fix Applied
1. **Fixed adherence threshold logic**:
   - Calories: Only show "below goal" if < 70% adherence, "over goal" if > 110%
   - Protein: Only show "need more" if < 80% adherence AND actually need more
   - Added positive messages for good adherence (≥85% calories, ≥100% protein)

2. **Improved message accuracy**:
   - Added validation to check if `protein_needed > 0` before showing "need more"
   - Fixed calorie calculations to use actual remaining calories
   - Added debug logging to track calculation values

3. **Enhanced breakfast logic**:
   - Only show breakfast reminder if it's past 10 AM AND user has other meals but no breakfast
   - Removed duplicate breakfast recommendation logic

4. **Added recommendation deduplication**:
   - Remove duplicate recommendation types
   - Limit to top 4 most relevant recommendations
   - Prioritize by importance level

### Technical Details
- **Before**: `if adherence["calories"] < 70` → Wrong threshold logic
- **After**: `if calorie_adherence_pct < 70` → Correct adherence checking
- **Debug logging**: Added `print(f"[DEBUG] today_totals: {today_totals}")` for troubleshooting
- **Validation**: Check `protein_needed > 0` before showing protein recommendations

### Testing
1. Log food items to reach different adherence levels
2. Check AI recommendations in the HomePage
3. Verify recommendations match actual consumption data
4. Check backend logs for debug information

### Impact
- ✅ AI recommendations now show accurate information
- ✅ Positive reinforcement for good adherence
- ✅ Breakfast reminders only when appropriate
- ✅ No duplicate or contradictory recommendations
- ✅ Better user experience with relevant suggestions 

# Changed Files Log

## 2024-01-XX - AI Recommendations Accuracy Fix

### Issue
AI recommendations were completely incorrect:
- "You're 2000 calories below your goal" when user consumed 1980/2000 calories (only 20 short)
- "You need 100g more protein today" when user consumed 103/100g protein (3g over goal)

### Root Cause
The issue was caused by timezone-aware filtering problems in the daily insights endpoint. The backend was using UTC date filtering to get "today's consumption," but users' data might be in different timezones. This resulted in empty `today_consumption` arrays, making all `today_totals` values zero, which led to incorrect calculations:
- `remaining_calories = 2000 - 0 = 2000` (should be 2000 - 1980 = 20)
- `protein_needed = 100 - 0 = 100` (should be 100 - 103 = -3)

### Solution
**File:** `diabetes-meal-plan-generator/backend/main.py`
- **Fixed timezone-aware filtering** for today's consumption records
- **Added lenient filtering** using last 36 hours instead of strict UTC date matching
- **Added fallback mechanism** to use last 12 hours of records if no "today" records found
- **Added comprehensive debug logging** to troubleshoot data filtering issues
- **Added validation checks** to only show recommendations when values are positive
- **Removed emojis** from recommendation messages per user preference

### Technical Details
- Modified `get_daily_coaching_insights` endpoint in main.py
- Changed from strict UTC date filtering to timezone-aware time-based filtering
- Added debug logging to track consumption record filtering
- Added validation to prevent showing "need more" messages when user is already over goal
- Updated calculation logic to handle edge cases properly

### Impact
- Fixed incorrect AI recommendations showing wrong calorie and protein deficits
- Improved timezone handling for users in different time zones
- Added better error handling and debugging capabilities
- Maintained user preference for no emojis in UI text 

## 2024-01-XX - Macronutrient Data Consistency Fix

### Issue
There was a significant discrepancy between macronutrient data shown on different pages:
- **Homepage**: 1980 calories, 103g protein
- **Consumption History**: 3900 calories, 149g protein

### Root Cause
The two pages were using different data sources and filtering logic:
- **Homepage**: Called `/coach/daily-insights` with server-side timezone-aware filtering
- **Consumption History**: Called `/consumption/history` with client-side filtering that was too lenient

The consumption history page was including yesterday's records if they were within 4 hours of current time, effectively doubling the data shown.

### Solution  
**File:** `diabetes-meal-plan-generator/frontend/src/components/ConsumptionHistory.tsx`
- **Fixed client-side filtering** to only include today's records (no yesterday records)
- **Removed lenient 4-hour window** that was including extra meals
- **Made filtering consistent** with homepage logic
- **Updated debug logging** to reflect the change

### Technical Details
- Modified the `selectedDays === 1` filtering logic in `loadConsumptionData` function
- Changed from including yesterday's records within 4 hours to strict today-only filtering
- Updated console logging to remove yesterday references
- This ensures both pages now show consistent macronutrient data

### Impact
- Both pages now show consistent macronutrient totals
- Eliminated data discrepancies between different views
- More accurate daily tracking and recommendations
- Better user experience with consistent data across the app 

## 2024-01-XX - Final Data Consistency Fix

### Issue
Even after fixing the client-side filtering, the pages were still showing different values because they were using different data sources:
- **Homepage**: Used backend-calculated daily totals from `/coach/daily-insights`
- **Consumption History**: Used client-side calculated averages from `generateAnalyticsFromRecords()`

### Root Cause
The consumption history page was generating its own analytics using `generateAnalyticsFromRecords()` which calculated daily averages by dividing totals by the number of days. This created a discrepancy even when both pages filtered the same records.

### Solution
**File:** `diabetes-meal-plan-generator/frontend/src/components/ConsumptionHistory.tsx`
- **Modified "Today" view** to use backend daily insights data instead of client-side calculations
- **Ensured data consistency** by using the same data source for both pages
- **Added fallback logic** to use client-side calculations for other time ranges
- **Maintained existing functionality** for weekly/monthly views

### Technical Details
- For `selectedDays === 1`, override the analytics with `insightsData.today_totals`
- This ensures both pages use the same timezone-aware filtered data from the backend
- Other time ranges continue to use client-side analytics as before
- Added console logging to confirm when backend data is being used

### Impact
- **Guaranteed data consistency** between homepage and consumption history pages
- **Same macronutrient values** displayed across the entire application
- **Accurate AI recommendations** based on consistent data
- **Better user experience** with no confusing data discrepancies 

## 2024-01-XX - Final UI Data Display Fix

### Issue
Despite backend data consistency fixes, the frontend was still showing different values because the consumption history page was using a different data source for displaying the values in the UI.

### Root Cause
The consumption history page UI was still displaying `analytics.daily_averages` values (calculated averages) instead of the actual `today_totals` from the daily insights endpoint, even though the data was being fetched correctly.

### Solution
**File:** `diabetes-meal-plan-generator/frontend/src/components/ConsumptionHistory.tsx`
- **Modified UI display logic** to use `dailyInsights.today_totals` directly for "Today" view
- **Added conditional rendering** to use backend data when `selectedTimeRange === '1'`
- **Updated labels** to show "Total Calories" and "Total Protein" for today view vs "Avg" for other periods
- **Maintained existing functionality** for other time ranges

### Technical Details
- Changed calories display from `analytics.daily_averages.calories` to `dailyInsights.today_totals.calories` for today view
- Changed protein display from `analytics.daily_averages.protein` to `dailyInsights.today_totals.protein` for today view
- Added conditional logic: `selectedTimeRange === '1' && dailyInsights?.today_totals ? backend_data : calculated_data`
- Updated labels to reflect whether showing totals (today) or averages (other periods)

### Impact
- **Both pages now display identical values** from the same backend source
- **No more data calculation differences** between pages
- **Consistent user experience** across the entire application
- **Simplified codebase** with single source of truth for today's data 

### Final Solution
**Files modified:** `diabetes-meal-plan-generator/frontend/src/components/ConsumptionHistory.tsx`

I made the consumption history page use the **exact same data source** as the homepage for all UI displays when showing "Today" data:

1. **Main metric cards**: Now use `dailyInsights.today_totals` instead of `analytics.daily_averages`
2. **Micronutrients section**: Now use `dailyInsights.today_totals` for fiber, sugar, and sodium
3. **Labels**: Changed from "Daily Average" to "Daily Total" for Today view
4. **Units**: Removed "/day" suffix for Today view since it's showing totals, not averages

### Key Changes
- **Unified data source**: Both pages now use `/coach/daily-insights` endpoint data for Today view
- **Consistent display logic**: Same conditional rendering based on `selectedTimeRange === '1'`
- **Proper labeling**: Shows "Daily Total" vs "Daily Average" appropriately
- **Accurate units**: Removes "/day" suffix when showing today's totals

### Impact
- **GUARANTEED consistency**: Both homepage and consumption history now show identical macronutrient values
- **Accurate data**: Today's totals are calculated server-side with proper timezone handling
- **Better UX**: No more confusing data discrepancies between pages
- **Maintainable**: Single source of truth for today's nutritional data

### Testing
After applying these changes, both pages should show identical values for:
- Calories consumed today
- Protein consumed today  
- Carbohydrates consumed today
- Fat consumed today
- Fiber consumed today
- Sugar consumed today
- Sodium consumed today

This ensures the AI recommendations are based on the same data the user sees throughout the application. 