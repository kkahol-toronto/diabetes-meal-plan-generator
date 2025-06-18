from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from typing import Dict, Any, List, Optional
from openai import AzureOpenAI
import os
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image
import base64
import json
import traceback

from database import save_chat_message # Assuming save_chat_message is accessible or moved
from app.dependencies import get_current_user, User # Import from the new dependencies file

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

router = APIRouter()

@router.post("/analyze-pantry-fridge")
async def analyze_pantry_fridge(
    image: UploadFile = File(...),
    session_id: str = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Analyze fridge/pantry image and identify items and quantities."""
    try:
        print(f"[analyze_pantry_fridge] Starting analysis for user {current_user['id']}")
        
        contents = await image.read()
        
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        if len(contents) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")
        
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        file_extension = image.filename.lower().split('.')[-1] if image.filename else ''
        if not file_extension or f'.{file_extension}' not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file format. Allowed formats: {', '.join(allowed_extensions)}")
        
        try:
            img = Image.open(BytesIO(contents))
            
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            max_size = 1024
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=85, optimize=True)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            print("[analyze_pantry_fridge] Image processed and converted to base64")
            
        except Exception as img_error:
            print(f"[analyze_pantry_fridge] Image processing error: {str(img_error)}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid or corrupted image file. Please upload a valid image in one of these formats: {', '.join(allowed_extensions)}"
            )
        
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {
                    "role": "system",
                    "content": """You are an AI assistant specialized in identifying food items and their quantities from images of fridges or pantries. \
                    Analyze the image and return a structured JSON response with a list of identified items and their estimated quantities. \
                    If you cannot identify an item or its quantity, you can state "unknown". \
                    The format should be:
                    {
                        "identified_items": [
                            {"item_name": "name of item", "quantity": "estimated quantity (e.g., 2 apples, half a carton, 300g pasta)"},
                            {"item_name": "another item", "quantity": "estimated quantity"},
                            // ... more items
                        ],
                        "notes": "Any additional observations about the contents."
                    }
                    Be precise and objective in your identification."""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Identify the items and their quantities in this image of a fridge or pantry."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_str}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=800,
            temperature=0.3
        )
        
        print("[analyze_pantry_fridge] Received analysis from OpenAI")
        
        analysis_text = response.choices[0].message.content
        
        try:
            start_idx = analysis_text.find('{')
            end_idx = analysis_text.rfind('}') + 1
            json_str = analysis_text[start_idx:end_idx]
            analysis_data = json.loads(json_str)
            print(f"[analyze_pantry_fridge] Successfully parsed analysis data: {analysis_data}")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[analyze_pantry_fridge] Error parsing analysis data: {str(e)}")
            analysis_data = {
                "identified_items": [{"item_name": "unknown", "quantity": "unknown"}],
                "notes": analysis_text
            }
        
        # Save analysis to chat history for context
        if session_id:
            print(f"[analyze_pantry_fridge] Saving to chat with session_id: {session_id}")
            # Save user message (image context)
            await save_chat_message(
                user_id=current_user["email"],
                session_id=session_id,
                message="Image of fridge/pantry submitted for analysis.",
                is_user=True,
                image_url=img_str,
                metadata={"type": "fridge_pantry_analysis_request"}
            )
            # Save AI response
            await save_chat_message(
                user_id=current_user["email"],
                session_id=session_id,
                message=json.dumps(analysis_data, indent=2), # Store JSON as string in message
                is_user=False,
                metadata={"type": "fridge_pantry_analysis_response", "data": analysis_data}
            )

        return {"success": True, "analysis": analysis_data}

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"[analyze_pantry_fridge] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 