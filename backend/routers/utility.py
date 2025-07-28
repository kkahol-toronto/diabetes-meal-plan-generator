from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
import pytz

# Import models and dependencies
from models import User
from routers.auth import get_current_user

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Diabetes Diet Manager API",
        "version": "1.0.0"
    }


@router.post("/test-echo")
async def test_echo(current_user: User = Depends(get_current_user)):
    print(">>>> Entered /test-echo endpoint")
    return {"ok": True}


@router.post("/export/test-minimal")
async def export_test_minimal():
    print(">>>> Entered /export/test-minimal endpoint")
    return {"ok": True}


@router.get("/debug/timezone")  
async def debug_timezone(current_user: User = Depends(get_current_user)):
    """Debug endpoint to check user's timezone and day boundaries"""
    try:
        profile = current_user.get("profile", {})
        user_timezone = profile.get("timezone", "UTC")
        
        # Calculate day boundaries
        user_tz = pytz.timezone(user_timezone)
        utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
        user_now = utc_now.astimezone(user_tz)
        start_of_today_user = user_now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_tomorrow_user = start_of_today_user + timedelta(days=1)
        start_of_today_utc = start_of_today_user.astimezone(pytz.utc).replace(tzinfo=None)
        start_of_tomorrow_utc = start_of_tomorrow_user.astimezone(pytz.utc).replace(tzinfo=None)
        
        return {
            "user_email": current_user["email"],
            "profile_timezone": user_timezone,
            "utc_now": utc_now.isoformat(),
            "user_local_time": user_now.isoformat(),
            "start_of_today_user": start_of_today_user.isoformat(),
            "start_of_today_utc": start_of_today_utc.isoformat(),
            "start_of_tomorrow_utc": start_of_tomorrow_utc.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 