#!/usr/bin/env python3
"""
Debug script to investigate meal plan storage issues
"""

import asyncio
import sys
import os
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import interactions_container

async def debug_meal_plans():
    """Debug meal plan storage issues"""
    
    print("🔍 Debugging Meal Plan Storage Issues...")
    print("=" * 60)
    
    try:
        # Get recent meal plans for all users
        query = "SELECT * FROM c WHERE (c.type = 'meal_plan' OR c.type = 'full_meal_plan') ORDER BY c.created_at DESC"
        all_plans = list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
        
        print(f"📊 Found {len(all_plans)} total meal plans in database")
        
        # Group by user
        users = {}
        for plan in all_plans:
            user_id = plan.get('user_id', 'unknown')
            if user_id not in users:
                users[user_id] = []
            users[user_id].append(plan)
        
        print(f"👥 Meal plans for {len(users)} users:")
        
        for user_id, plans in users.items():
            print(f"\n📋 User: {user_id}")
            print(f"   Total plans: {len(plans)}")
            
            # Check for recent duplicates (same day)
            today_plans = [p for p in plans if '2025-07-29' in p.get('created_at', '')]
            if len(today_plans) > 1:
                print(f"   ⚠️  {len(today_plans)} plans created today - potential duplicates!")
                
                # Check if they're actually duplicates
                for i, plan in enumerate(today_plans[:3]):
                    plan_type = plan.get('type', 'unknown')
                    calories = plan.get('dailyCalories') or (plan.get('meal_plan', {}).get('dailyCalories'))
                    has_pdf = bool(plan.get('consolidated_pdf') or plan.get('pdf_filename'))
                    created_at = plan.get('created_at', '')[:19]  # Just date/time
                    
                    print(f"     Plan {i+1}: {plan_type}, {calories} cal, PDF={has_pdf}, {created_at}")
            
            # Check PDF info
            pdf_plans = [p for p in plans if p.get('consolidated_pdf') or p.get('pdf_filename')]
            if pdf_plans:
                print(f"   📄 {len(pdf_plans)} plans have PDF info")
                for plan in pdf_plans[:2]:
                    pdf_info = plan.get('consolidated_pdf') or {'filename': plan.get('pdf_filename')}
                    print(f"     PDF: {pdf_info.get('filename', 'N/A')}")
            else:
                print(f"   ❌ No plans have PDF info")
        
        # Look for specific issues
        print(f"\n🔍 Detailed Analysis:")
        
        # Check for plans saved in the last hour
        recent_plans = [p for p in all_plans if '2025-07-29T20:' in p.get('created_at', '') or '2025-07-29T04:' in p.get('created_at', '')]
        
        if recent_plans:
            print(f"\n📅 Recent plans ({len(recent_plans)}):")
            for i, plan in enumerate(recent_plans):
                plan_id = plan.get('id', 'N/A')[:12] + '...' if len(plan.get('id', '')) > 12 else plan.get('id', 'N/A')
                plan_type = plan.get('type', 'unknown')
                
                # Check structure
                has_breakfast = bool(plan.get('breakfast') or plan.get('meal_plan', {}).get('breakfast'))
                has_pdf = bool(plan.get('consolidated_pdf') or plan.get('pdf_filename'))
                has_recipes = bool(plan.get('recipes'))
                has_shopping = bool(plan.get('shopping_list'))
                
                print(f"   Plan {i+1}: {plan_id}")
                print(f"     Type: {plan_type}")
                print(f"     Structure: breakfast={has_breakfast}, PDF={has_pdf}, recipes={has_recipes}, shopping={has_shopping}")
                
                # If it's a full_meal_plan, show nested structure
                if plan_type == 'full_meal_plan':
                    meal_plan_data = plan.get('meal_plan', {})
                    print(f"     Nested meal_plan keys: {list(meal_plan_data.keys())}")
                
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error debugging meal plans: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(debug_meal_plans())
    sys.exit(0 if result else 1) 