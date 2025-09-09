from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime
from typing import Dict, Any

# Import models
from models import Token, TokenData, User, RegistrationData, Patient

# Import utilities
from utils import (
    get_password_hash, verify_password, create_access_token,
    generate_registration_code, send_registration_code,
    SECRET_KEY, ALGORITHM, oauth2_scheme
)

# Import constants
from constants import ACCESS_TOKEN_EXPIRE_MINUTES, DEFAULT_CALORIE_TARGET

# Import database functions
from database import (
    get_user_by_email, create_user, get_patient_by_registration_code,
    get_patient_by_id, user_container, create_patient, get_all_patients
)

from jose import JWTError, jwt
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import json

router = APIRouter()

# Google OAuth configuration
GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID_HERE"  # Replace with actual client ID


async def get_current_user(token: str = Depends(oauth2_scheme)):
    print("get_current_user called")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        print("Decoding JWT token...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        print(f"Decoded username: {username}")
        if username is None:
            print("Username is None in token payload")
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as e:
        print(f"JWTError while decoding token: {e}")
        raise credentials_exception
    except Exception as e:
        print(f"Unexpected error while decoding token: {e}")
        raise credentials_exception
    try:
        print(f"Fetching user by email: {token_data.username}")
        user = await get_user_by_email(token_data.username)
        print(f"User fetched: {user}")
        if user is None:
            print("User not found in database")
            raise credentials_exception
        print("Returning user from get_current_user")
        return user
    except Exception as e:
        print(f"Error fetching user from database: {e}")
        raise credentials_exception


@router.post("/login", response_model=Token)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"Login attempt for user: {form_data.username}")
    
    user = await get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        print(f"Login failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"User found: {user}")
    
    # Check if user has electronic signature and valid consent
    user_has_consent = user.get("consent_given", False)
    user_has_signature = user.get("electronic_signature", "") != ""
    user_policy_version = user.get("policy_version", "")
    CURRENT_POLICY_VERSION = "1.0.0"
    
    # Get form data directly from the request
    form = await request.form()
    consent_given = form.get('consent_given', 'false').lower() == 'true'
    consent_timestamp = form.get('consent_timestamp')
    policy_version = form.get('policy_version', CURRENT_POLICY_VERSION)
    electronic_signature = form.get('electronic_signature', '')
    signature_timestamp = form.get('signature_timestamp', '')
    research_consent = form.get('research_consent', 'false').lower() == 'true'
    
    # Check if user needs to sign consent
    needs_consent_signature = (
        not user_has_consent or 
        not user_has_signature or 
        user_policy_version != CURRENT_POLICY_VERSION
    )
    
    if needs_consent_signature:
        if not consent_given or not electronic_signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Electronic signature and consent are required to access services"
            )
    
    # Update user's consent information
    try:
        # Use existing consent data if user already has consent and no new consent provided
        final_consent_given = consent_given if (needs_consent_signature and consent_given) else user.get("consent_given", False)
        final_consent_timestamp = consent_timestamp if consent_timestamp else user.get("consent_timestamp")
        final_policy_version = policy_version if policy_version else user.get("policy_version", CURRENT_POLICY_VERSION)
        final_electronic_signature = electronic_signature if electronic_signature else user.get("electronic_signature", "")
        final_signature_timestamp = signature_timestamp if signature_timestamp else user.get("signature_timestamp", "")
        final_research_consent = research_consent if needs_consent_signature else user.get("research_consent", False)
        
        # Build a new dictionary with only the fields we want to update
        update_dict = {
            "id": user["id"],  # Required for upsert
            "type": "user",    # Required for querying
            "consent_given": final_consent_given,
            "consent_timestamp": final_consent_timestamp,
            "policy_version": final_policy_version,
            "electronic_signature": final_electronic_signature,
            "signature_timestamp": final_signature_timestamp,
            "research_consent": final_research_consent,
            # Preserve other critical fields
            "email": user["email"],
            "username": user["username"],
            "hashed_password": user["hashed_password"],
            "disabled": user.get("disabled", False),
            "is_admin": user.get("is_admin", False),  # CRITICAL: Preserve admin status
            "patient_id": user.get("patient_id"),
            "registration_code": user.get("registration_code"),  # Preserve registration code
            "profile": user.get("profile", {}),
            "data_retention_preference": user.get("data_retention_preference", "standard"),
            "marketing_consent": user.get("marketing_consent", False),
            "analytics_consent": user.get("analytics_consent", True),
            "last_consent_update": user.get("last_consent_update"),
            "signature_ip_address": user.get("signature_ip_address"),
            "created_at": user.get("created_at"),
            "updated_at": datetime.utcnow().isoformat(),
            "updated_by": "system"
        }
        
        # Perform the upsert
        user_container.upsert_item(body=update_dict)
    except Exception as e:
        print(f"Error during user update: {e}")
        # If update fails, continue with login since consent info is not critical
    
    # Get patient info if available
    patient_name = None
    if user.get("patient_id"):
        try:
            print(f"Fetching patient info for patient_id: {user['patient_id']}")
            patient = await get_patient_by_id(user["patient_id"])
            if patient:
                patient_name = patient.get("name")
                print(f"Found patient name: {patient_name}")
            else:
                print("No patient found with the given ID")
        except Exception as e:
            print(f"Error fetching patient info: {str(e)}")
    else:
        print("No patient_id found in user data")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "sub": user["email"],
        "is_admin": user.get("is_admin", False),
        "name": patient_name,
        "consent_given": final_consent_given,
        "consent_timestamp": final_consent_timestamp,
        "policy_version": final_policy_version
    }
    print(f"Creating token with data: {token_data}")
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register")
async def register(data: RegistrationData):
    # Find patient with registration code
    patient = await get_patient_by_registration_code(data.registration_code)
    if not patient:
        raise HTTPException(status_code=400, detail="Invalid registration code")
    
    existing_user = await get_user_by_email(data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(data.password)
    
    # Check if admin has already created a profile for this patient
    admin_profile = None
    try:
        profile_query = f"SELECT * FROM c WHERE c.type = 'user_profile' AND c.registration_code = '{data.registration_code}'"
        profiles = list(user_container.query_items(query=profile_query, enable_cross_partition_query=True))
        if profiles:
            admin_profile = profiles[0].get('profile', {})
    except Exception as e:
        print(f"Error checking for admin profile: {e}")
    
    # Create comprehensive user profile from patient data
    initial_profile = {
        "name": patient.get("name", ""),
        "medicalConditions": patient.get("medical_conditions", [patient.get("condition", "")]),
        "currentMedications": patient.get("medications", []),
        "allergies": patient.get("allergies", []),
        "dietaryRestrictions": patient.get("dietary_restrictions", []),
        "calorieTarget": DEFAULT_CALORIE_TARGET,  # Default, will be customized based on conditions
        "primaryGoals": ["Manage health conditions", "Maintain balanced nutrition"]
    }
    
    # If admin has created a profile, merge it with patient data (admin profile takes precedence)
    if admin_profile:
        # Merge profiles, giving priority to admin-entered data
        for key, value in admin_profile.items():
            if value and value != []:  # Only override if admin actually entered data
                initial_profile[key] = value
    
    user_data = {
        "username": data.email,
        "email": data.email,
        "hashed_password": hashed_password,
        "disabled": False,
        "patient_id": patient["id"],
        "registration_code": data.registration_code,  # Store registration code
        "profile": initial_profile,  # Include merged profile
        "consent_given": data.consent_given,
        "consent_timestamp": data.consent_timestamp,
        "policy_version": data.policy_version,
        "data_retention_preference": data.data_retention_preference,
        "marketing_consent": data.marketing_consent,
        "analytics_consent": data.analytics_consent,
        "last_consent_update": data.consent_timestamp,
        # Electronic Signature Fields
        "electronic_signature": data.electronic_signature,
        "signature_timestamp": data.signature_timestamp,
        "signature_ip_address": data.signature_ip_address,
        "research_consent": data.research_consent,
        "timezone": data.timezone or "UTC"
    }
    
    await create_user(user_data)
    
    # Create a proper user profile record in the database
    profile_record = {
        "id": f"profile_{data.email}",
        "type": "user_profile",
        "user_id": data.email,
        "registration_code": data.registration_code,
        "profile": initial_profile,
        "created_by": "patient_registration",
        "admin_prefilled": bool(admin_profile),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Save the profile
    try:
        user_container.upsert_item(body=profile_record)
    except Exception as e:
        print(f"Error saving user profile record: {e}")
    
    return {
        "message": "Registration successful", 
        "profile_initialized": True,
        "admin_prefilled": bool(admin_profile),
        "health_conditions": initial_profile["medicalConditions"]
    }


@router.post("/admin/login", response_model=Token)
async def admin_login(form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"[ADMIN LOGIN] Received username: {form_data.username}")
    user = await get_user_by_email(form_data.username)
    print(f"[ADMIN LOGIN] Loaded user: {user}")
    if not user:
        print("[ADMIN LOGIN] User not found")
    else:
        print(f"[ADMIN LOGIN] is_admin: {user.get('is_admin')}")
        print(f"[ADMIN LOGIN] hashed_password: {user.get('hashed_password')}")
        password_ok = verify_password(form_data.password, user["hashed_password"])
        print(f"[ADMIN LOGIN] verify_password result: {password_ok}")
        if not user.get("is_admin"):
            print("[ADMIN LOGIN] User is not admin")
        if not password_ok:
            print("[ADMIN LOGIN] Password does not match")
    if not user or not user.get("is_admin") or not verify_password(form_data.password, user["hashed_password"]):
        print("[ADMIN LOGIN] Raising 401 Unauthorized")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "is_admin": True},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/auth/google", response_model=Token)
async def google_login(request: Request):
    """
    Google OAuth2 login endpoint.
    Accepts a Google JWT token and creates/logs in a user.
    """
    try:
        # Get the request body
        body = await request.json()
        google_token = body.get("token")
        
        if not google_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google token is required"
            )
        
        # Verify the Google token
        try:
            # For development, we'll skip verification and extract info from token
            # In production, uncomment the verification below
            
            # idinfo = id_token.verify_oauth2_token(
            #     google_token, google_requests.Request(), GOOGLE_CLIENT_ID
            # )
            
            # For now, let's decode the token without verification (development only)
            import base64
            import json
            
            # Split the token and decode the payload
            parts = google_token.split('.')
            if len(parts) != 3:
                raise ValueError("Invalid token format")
            
            # Add padding if needed
            payload = parts[1]
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding
                
            decoded_payload = base64.urlsafe_b64decode(payload)
            idinfo = json.loads(decoded_payload)
            
        except Exception as e:
            print(f"Google token verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token"
            )
        
        # Extract user information from Google token
        email = idinfo.get('email')
        name = idinfo.get('name', '')
        google_id = idinfo.get('sub')
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not found in Google token"
            )
        
        print(f"Google OAuth: Processing login for {email}")
        
        # Check if user exists in our database
        user = await get_user_by_email(email)
        
        if not user:
            # Create new user with Google OAuth
            print(f"Creating new user from Google OAuth: {email}")
            
            # Generate a registration code for the new user
            registration_code = generate_registration_code()
            
            # Create user data
            user_data = {
                "email": email,
                "username": email,
                "hashed_password": get_password_hash("google_oauth_" + google_id),  # Placeholder password
                "disabled": False,
                "is_admin": False,
                "patient_id": registration_code,
                "registration_code": registration_code,
                "consent_given": False,  # They'll need to provide consent
                "consent_timestamp": None,
                "policy_version": "1.0.0",
                "electronic_signature": "",
                "signature_timestamp": None,
                "research_consent": False,
                "profile": {
                    "name": name,
                    "email": email
                },
                "google_id": google_id,
                "auth_provider": "google"
            }
            
            try:
                user = await create_user(user_data)
                print(f"Successfully created Google OAuth user: {email}")
            except Exception as e:
                print(f"Error creating Google OAuth user: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user account"
                )
        else:
            print(f"Existing user found for Google OAuth: {email}")
            # Update user with Google ID if not present
            if not user.get("google_id"):
                user["google_id"] = google_id
                user["auth_provider"] = "google"
                # Update user in database would go here
        
        # Check consent status
        user_has_consent = user.get("consent_given", False)
        user_has_signature = user.get("electronic_signature", "") != ""
        
        if not user_has_consent or not user_has_signature:
            # User needs to provide consent - return special response
            return {
                "access_token": "CONSENT_REQUIRED",
                "token_type": "consent_required",
                "detail": "Electronic signature and consent are required",
                "user_email": email,
                "user_name": name
            }
        
        # Create access token for the user
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        token_data = {
            "sub": user["email"],
            "is_admin": user.get("is_admin", False),
            "name": user.get("profile", {}).get("name", name),
            "consent_given": user.get("consent_given", False),
            "consent_timestamp": user.get("consent_timestamp"),
            "policy_version": user.get("policy_version", "1.0.0")
        }
        
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        
        print(f"Google OAuth login successful for: {email}")
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "user_id": user.get("patient_id", user.get("id", email))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Google OAuth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google authentication failed"
        )


@router.post("/admin/create-patient")
async def create_patient_endpoint(
    patient: Patient,
    current_user: User = Depends(get_current_user)
):
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
        
        # Try to send registration code via SMS
        sms_result = send_registration_code(patient.phone, registration_code)
        
        if sms_result:
            return {
                "message": "Patient created and registration code sent via SMS",
                "registration_code": registration_code
            }
        else:
            return {
                "message": "Patient created successfully. Please note down the registration code as SMS could not be sent.",
                "registration_code": registration_code
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/patients")
async def get_patients(current_user: User = Depends(get_current_user)):
    # Check if user is admin using the token data
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        patients = await get_all_patients()
        return patients
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 