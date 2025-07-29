#!/usr/bin/env python3
"""
Test script to verify that meal plans with PDFs are properly retrieved after the database fix.
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_user_meal_plans, interactions_container

async def test_meal_plan_retrieval():
    """Test that meal plans with PDFs are retrieved correctly"""
    
    print("🔍 Testing meal plan retrieval after PDF fix...")
    
    # Get a sample user from the database to test with
    try:
        # Query for any user that has meal plans (in interactions container)
        query = "SELECT DISTINCT c.user_id FROM c WHERE (c.type = 'meal_plan' OR c.type = 'full_meal_plan')"
        users = list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
        
        if not users:
            print("❌ No users with meal plans found in database")
            return False
            
        test_user = users[0]['user_id']
        print(f"📋 Testing with user: {test_user}")
        
        # Get meal plans using our fixed function
        meal_plans = await get_user_meal_plans(test_user)
        
        print(f"✅ Retrieved {len(meal_plans)} meal plans")
        
        # Check for meal plans with PDFs
        pdf_plans = [plan for plan in meal_plans if plan.get('consolidated_pdf')]
        print(f"📄 Found {len(pdf_plans)} meal plans with PDFs")
        
        # Display details
        for i, plan in enumerate(meal_plans[:3]):  # Show first 3 plans
            has_pdf = '📄 PDF' if plan.get('consolidated_pdf') else '❌ No PDF'
            plan_id = plan.get('id', 'N/A')
            if len(plan_id) > 8:
                plan_id = plan_id[:8] + '...'
            print(f"  Plan {i+1}: ID={plan_id} {has_pdf}")
            if plan.get('consolidated_pdf'):
                pdf_info = plan['consolidated_pdf']
                print(f"    PDF: {pdf_info.get('filename', 'N/A')}")
        
        # Test raw database query to compare
        raw_query_meal_plan = f"SELECT * FROM c WHERE c.type = 'meal_plan' AND c.user_id = '{test_user}'"
        raw_query_full_meal_plan = f"SELECT * FROM c WHERE c.type = 'full_meal_plan' AND c.user_id = '{test_user}'"
        
        regular_plans = list(interactions_container.query_items(query=raw_query_meal_plan, enable_cross_partition_query=True))
        full_plans = list(interactions_container.query_items(query=raw_query_full_meal_plan, enable_cross_partition_query=True))
        
        print(f"\n📊 Raw database counts:")
        print(f"  Regular meal plans (type='meal_plan'): {len(regular_plans)}")
        print(f"  Full meal plans (type='full_meal_plan'): {len(full_plans)}")
        print(f"  Total retrieved by fixed function: {len(meal_plans)}")
        
        # Show some details about full_meal_plans
        if full_plans:
            print(f"\n🔍 Full meal plan details:")
            for i, plan in enumerate(full_plans[:2]):
                has_pdf = bool(plan.get('consolidated_pdf'))
                has_pdf_filename = bool(plan.get('pdf_filename'))
                print(f"  Full Plan {i+1}: PDF info={has_pdf}, PDF filename={has_pdf_filename}")
        
        # Verify our fix worked
        expected_total = len(regular_plans) + len(full_plans)
        if len(meal_plans) >= expected_total and expected_total > 0:
            print("✅ SUCCESS: Fixed function retrieves both regular and full meal plans!")
            if pdf_plans:
                print(f"✅ SUCCESS: Found {len(pdf_plans)} meal plans with PDF info!")
            return True
        elif expected_total == 0:
            print("⚠️  No meal plans found for this user")
            return False
        else:
            print("❌ ISSUE: Fixed function may not be retrieving all meal plans")
            return False
            
    except Exception as e:
        print(f"❌ Error testing meal plan retrieval: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🧪 PDF Fix Test - Meal Plan History")
    print("=" * 50)
    
    success = await test_meal_plan_retrieval()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 TEST PASSED: PDF meal plans should now appear in history!")
    else:
        print("❌ TEST FAILED: There may still be issues with PDF retrieval")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1) 