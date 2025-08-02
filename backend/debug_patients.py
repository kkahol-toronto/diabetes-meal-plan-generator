#!/usr/bin/env python3
"""
Debug script to check actual patient data structure
"""
import asyncio
import sys
from database import get_all_patients

async def check_patient_data():
    try:
        print("🔍 Fetching all patients from database...")
        patients = await get_all_patients()
        print(f"📊 Total patients found: {len(patients)}")
        
        if not patients:
            print("❌ No patients found in database!")
            return
            
        print("\n🔍 Analyzing patient data structure:")
        print("=" * 60)
        
        # Check all unique field names across patients
        all_fields = set()
        for patient in patients:
            all_fields.update(patient.keys())
        
        print(f"📋 All fields found in patient records: {sorted(all_fields)}")
        print("\n📝 First 5 patients detailed analysis:")
        print("=" * 60)
        
        for i, patient in enumerate(patients[:5]):
            print(f"\n👤 Patient {i+1}:")
            print(f"   ID: {patient.get('id', 'Missing')}")
            print(f"   Name: {patient.get('name', 'Missing')}")
            print(f"   Email: {patient.get('email', 'Missing')}")
            print(f"   Condition: '{patient.get('condition', 'Missing')}'")
            print(f"   Medical Conditions: {patient.get('medical_conditions', 'Missing')}")
            print(f"   Diabetes Type: '{patient.get('diabetes_type', 'Missing')}'")
            print(f"   Registration Code: {patient.get('registration_code', 'Missing')}")
            print(f"   Type: {patient.get('type', 'Missing')}")
            print(f"   Created At: {patient.get('created_at', 'Missing')}")
            
        print("\n🎯 Condition field analysis:")
        print("=" * 60)
        condition_counts = {}
        for patient in patients:
            condition = patient.get('condition', 'Unknown')
            condition_counts[condition] = condition_counts.get(condition, 0) + 1
            
        for condition, count in condition_counts.items():
            print(f"   '{condition}': {count} patients")
            
        print("\n🎯 Medical conditions field analysis:")
        print("=" * 60)
        med_conditions_found = []
        for patient in patients:
            med_cond = patient.get('medical_conditions', [])
            if med_cond:
                med_conditions_found.extend(med_cond)
                
        if med_conditions_found:
            from collections import Counter
            med_count = Counter(med_conditions_found)
            for condition, count in med_count.items():
                print(f"   '{condition}': {count} patients")
        else:
            print("   No medical_conditions arrays found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_patient_data())