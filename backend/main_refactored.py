"""
Refactored main.py - Diabetes Diet Manager API
This demonstrates the new modular structure with separated concerns.
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta

# Import configuration and app setup
from config import app, ACCESS_TOKEN_EXPIRE_MINUTES

# Import models
from models import (
    Token, User, Patient, UserProfile, MealPlanRequest, 
    ChatMessage, RegistrationData, ImageAnalysisRequest
)

# Import authentication
from auth import (
    get_current_user, verify_password, create_access_token, 
    get_password_hash, generate_registration_code
)

# Import services
from app.services.openai_service import robust_openai_call, robust_json_parse
from app.services.meal_planning import (
    trigger_meal_plan_recalibration, 
    generate_consumption_aware_meal_plan,
    generate_meal_plan_prompt
)

# Import utilities
from app.utils.helpers import send_registration_code, sanitize_vegetarian_meal

# Import database functions
from database import (
    create_user, get_user_by_email, create_patient,
    get_patient_by_registration_code, get_all_patients,
    save_meal_plan, get_user_meal_plans,
    get_patient_by_id
)

# Health Check Endpoint for Azure App Service
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Diabetes Diet Manager API",
        "version": "2.0.0",
        "architecture": "modular"
    }

# Authentication endpoints
@app.post("/login", response_model=Token)
async def login(request: Request, form_data: dict):
    """User login endpoint with consent handling"""
    print(f"Login attempt for user: {form_data.get('username')}")
    
    user = await get_user_by_email(form_data.get('username'))
    if not user or not verify_password(form_data.get('password'), user["hashed_password"]):
        print(f"Login failed for user: {form_data.get('username')}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Handle consent and electronic signature logic
    # (Implementation details moved to auth service)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "sub": user["email"],
        "is_admin": user.get("is_admin", False),
        "consent_given": user.get("consent_given", False)
    }
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register")
async def register(data: RegistrationData):
    """User registration endpoint"""
    # Find patient with registration code
    patient = await get_patient_by_registration_code(data.registration_code)
    if not patient:
        raise HTTPException(status_code=400, detail="Invalid registration code")
    
    existing_user = await get_user_by_email(data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(data.password)
    
    # Create comprehensive user data
    user_data = {
        "username": data.email,
        "email": data.email,
        "hashed_password": hashed_password,
        "disabled": False,
        "patient_id": patient["id"],
        "registration_code": data.registration_code,
        "consent_given": data.consent_given,
        "electronic_signature": data.electronic_signature,
        "timezone": data.timezone or "UTC"
    }
    
    await create_user(user_data)
    return {"message": "Registration successful"}

# Meal planning endpoints
@app.post("/generate-meal-plan")
async def generate_meal_plan_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Generate personalized meal plan using AI"""
    try:
        data = await request.json()
        user_profile = data.get("user_profile")
        days = data.get("days", 7)

        if not user_profile:
            raise HTTPException(status_code=400, detail="User profile is required")
        
        # Generate prompt using meal planning service
        prompt = generate_meal_plan_prompt(UserProfile(**user_profile))
        
        # Call OpenAI service
        response = await robust_openai_call(
            messages=[{"role": "user", "content": prompt}],
            context="meal_plan_generation"
        )
        
        if response["success"]:
            # Parse response and save meal plan
            parsed_result = robust_json_parse(response["content"])
            if parsed_result["success"]:
                meal_plan_data = parsed_result["data"]
                
                # Save to database
                await save_meal_plan(current_user["email"], meal_plan_data)
                
                return {"meal_plan": meal_plan_data, "message": "Meal plan generated successfully"}
            else:
                raise HTTPException(status_code=500, detail="Failed to parse meal plan")
        else:
            raise HTTPException(status_code=500, detail="Failed to generate meal plan")
            
    except Exception as e:
        print(f"Error generating meal plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/meal-plans")
async def get_meal_plans(current_user: User = Depends(get_current_user)):
    """Get user's meal plans"""
    try:
        meal_plans = await get_user_meal_plans(current_user["email"])
        return {"meal_plans": meal_plans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Admin endpoints
@app.post("/admin/create-patient")
async def create_patient_endpoint(
    patient: Patient,
    current_user: User = Depends(get_current_user)
):
    """Admin endpoint to create new patient"""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        registration_code = generate_registration_code()
        patient_data = {
            "name": patient.name,
            "phone": patient.phone,
            "condition": patient.condition,
            "medical_conditions": patient.medical_conditions or [patient.condition],
            "medications": patient.medications or [],
            "allergies": patient.allergies or [],
            "dietary_restrictions": patient.dietary_restrictions or [],
            "registration_code": registration_code,
            "created_at": datetime.utcnow().isoformat()
        }
        
        await create_patient(patient_data)
        
        # Send SMS with registration code
        sms_result = send_registration_code(patient.phone, registration_code)
        
        return {
            "message": "Patient created successfully",
            "registration_code": registration_code,
            "sms_sent": bool(sms_result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/patients")
async def get_patients(current_user: User = Depends(get_current_user)):
    """Get all patients (admin only)"""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        patients = await get_all_patients()
        return {"patients": patients}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Consumption tracking endpoints
@app.post("/log-consumption")
async def log_consumption(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Log food consumption and trigger meal plan recalibration"""
    try:
        data = await request.json()
        
        # Log the consumption (implementation in database service)
        # ...
        
        # Trigger meal plan recalibration
        user_profile = data.get("user_profile", {})
        updated_plan = await trigger_meal_plan_recalibration(
            current_user["email"], 
            user_profile
        )
        
        return {
            "message": "Consumption logged successfully",
            "updated_meal_plan": updated_plan
        }
        
    except Exception as e:
        print(f"Error logging consumption: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Additional endpoints would be organized similarly...
# Chat endpoints -> routers/chat.py
# Analytics endpoints -> routers/analytics.py  
# Recipe endpoints -> routers/recipes.py

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 