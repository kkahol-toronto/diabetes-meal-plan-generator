from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, List, Optional
from ..models.user import User
from ..services.auth import get_current_user
from sqlalchemy.orm import Session
from ..database.dependencies import get_db
from fastapi.responses import StreamingResponse
from datetime import datetime
import json
from io import BytesIO
import os
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

router = APIRouter()

@router.delete("/me/data", status_code=200)
async def delete_my_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Permanently delete the current user's account and all related PHI.
    """
    try:
        # Get the user from the database
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = current_user.get("email")
        
        # Delete all containers by user_id for Cosmos DB
        # 1. Delete meal plans
        from database import delete_all_user_meal_plans
        await delete_all_user_meal_plans(user_id)
        
        # 2. Delete chat history
        from database import clear_chat_history
        await clear_chat_history(user_id)
        
        # 3. Delete consumption history
        from database import interactions_container
        query = f"SELECT c.id, c.user_id FROM c WHERE c.type = 'consumption' AND c.user_id = '{user_id}'"
        consumption_items = list(interactions_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        for item in consumption_items:
            interactions_container.delete_item(item=item['id'], partition_key=item['user_id'])
        
        # 4. Delete shopping lists
        query = f"SELECT c.id, c.user_id FROM c WHERE c.type = 'shopping_list' AND c.user_id = '{user_id}'"
        shopping_items = list(interactions_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        for item in shopping_items:
            interactions_container.delete_item(item=item['id'], partition_key=item['user_id'])
        
        # 5. Delete recipes
        query = f"SELECT c.id, c.user_id FROM c WHERE c.type = 'recipe' AND c.user_id = '{user_id}'"
        recipe_items = list(interactions_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        for item in recipe_items:
            interactions_container.delete_item(item=item['id'], partition_key=item['user_id'])
        
        # 6. Finally delete the user record
        from database import user_container
        user_container.delete_item(item=user_id, partition_key=user_id)
        
        return {"detail": "Account and all data deleted."}
    except Exception as e:
        print(f"Error deleting user data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete account: {str(e)}")

@router.get("/me/data-export")
async def export_my_data(
    format: str = Query("json", enum=["json", "pdf"]),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export the current user's data in JSON or PDF format.
    """
    try:
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = current_user.get("email")
        
        # Gather user profile data
        from database import get_user_by_email
        user_item = await get_user_by_email(user_id)
        if not user_item:
            raise HTTPException(status_code=404, detail="User profile not found")
            
        profile = {k: v for k, v in user_item.items() if k not in ['hashed_password', 'salt']}
        
        # Gather meal plans - get the latest 25
        from database import get_user_meal_plans
        meal_plans = await get_user_meal_plans(user_id)
        meal_plans = sorted(meal_plans, key=lambda x: x.get("created_at", ""), reverse=True)[:25]
        
        # Gather chat logs - get the latest 25
        from database import get_recent_chat_history
        chat_logs = await get_recent_chat_history(user_id, limit=25)
        
        # Gather consumption history - get the latest 25
        from database import get_user_consumption_history
        consumption_items = await get_user_consumption_history(user_id, limit=25)
        
        # Prepare the export data
        export_data = {
            "profile": profile,
            "meal_plans": meal_plans,
            "chat_logs": chat_logs,
            "consumption_history": consumption_items,
            "export_date": datetime.utcnow().isoformat()
        }
        
        if format == "json":
            return export_data
        
        elif format == "pdf":
            try:
                # Create a PDF document with better styling
                buffer = BytesIO()
                doc = SimpleDocTemplate(
                    buffer, 
                    pagesize=LETTER,
                    rightMargin=72, 
                    leftMargin=72,
                    topMargin=72, 
                    bottomMargin=72
                )
                
                # Define styles
                styles = getSampleStyleSheet()
                title_style = styles['Title']
                heading_style = styles['Heading1']
                heading2_style = styles['Heading2']
                normal_style = styles['Normal']
                
                # Custom styles
                section_title_style = ParagraphStyle(
                    'SectionTitle',
                    parent=styles['Heading1'],
                    fontSize=16,
                    spaceAfter=12,
                    textColor=colors.darkblue
                )
                
                sub_title_style = ParagraphStyle(
                    'SubTitle',
                    parent=styles['Heading2'],
                    fontSize=14,
                    spaceAfter=8,
                    textColor=colors.darkblue
                )
                
                # Create document elements
                elements = []
                
                # Add cover page with logo
                try:
                    logo_path = os.path.join(os.path.dirname(__file__), "../../assets/coverpage.png")
                    if os.path.exists(logo_path):
                        elements.append(Image(logo_path, width=4*inch, height=2*inch))
                except Exception as e:
                    print(f"Could not add logo: {str(e)}")
                
                # Title and date
                elements.append(Paragraph("Diabetes Meal Planner - Data Export", title_style))
                elements.append(Paragraph(f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}", normal_style))
                elements.append(Paragraph(f"User: {profile.get('email', 'Unknown')}", normal_style))
                elements.append(Spacer(1, 0.5*inch))
                
                # Table of contents
                elements.append(Paragraph("Contents:", section_title_style))
                elements.append(Paragraph("1. Profile Information", normal_style))
                elements.append(Paragraph("2. Meal Plans", normal_style))
                elements.append(Paragraph("3. Consumption History", normal_style))
                elements.append(Paragraph("4. Chat History", normal_style))
                elements.append(Spacer(1, 0.25*inch))
                elements.append(PageBreak())
                
                # 1. Profile Information
                elements.append(Paragraph("1. Profile Information", section_title_style))
                
                # Create a table for profile data
                profile_data = []
                for k, v in profile.items():
                    if k not in ['id', '_rid', '_self', '_etag', '_attachments', '_ts', 'hashed_password']:
                        label = k.replace('_', ' ').title()
                        value = str(v) if v is not None else "Not provided"
                        profile_data.append([label, value])
                
                if profile_data:
                    profile_table = Table(profile_data, colWidths=[2*inch, 4*inch])
                    profile_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (0, -1), colors.darkblue),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    elements.append(profile_table)
                
                elements.append(Spacer(1, 0.25*inch))
                elements.append(PageBreak())
                
                # 2. Meal Plans
                elements.append(Paragraph("2. Meal Plans", section_title_style))
                elements.append(Paragraph(f"Total Meal Plans: {len(meal_plans)}", normal_style))
                elements.append(Spacer(1, 0.1*inch))
                
                # Display the 10 most recent meal plans
                recent_meal_plans = meal_plans[:10]
                for i, mp in enumerate(recent_meal_plans):
                    elements.append(Paragraph(f"Meal Plan {i+1}: {mp.get('created_at', 'N/A')}", sub_title_style))
                    
                    # Extract meal plan details
                    meal_data = []
                    meal_data.append(["Day", "Breakfast", "Lunch", "Dinner", "Snacks"])
                    
                    # Add days
                    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                    breakfast = mp.get("breakfast", [])
                    lunch = mp.get("lunch", [])
                    dinner = mp.get("dinner", [])
                    snacks = mp.get("snacks", [])
                    
                    for day_idx, day in enumerate(days):
                        if day_idx < len(breakfast) and day_idx < len(lunch) and day_idx < len(dinner) and day_idx < len(snacks):
                            meal_data.append([
                                day,
                                breakfast[day_idx] if day_idx < len(breakfast) else "",
                                lunch[day_idx] if day_idx < len(lunch) else "",
                                dinner[day_idx] if day_idx < len(dinner) else "",
                                snacks[day_idx] if day_idx < len(snacks) else ""
                            ])
                    
                    # Create table for meal plan
                    if len(meal_data) > 1:  # Only if we have data
                        meal_table = Table(meal_data, colWidths=[0.8*inch, 1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
                        meal_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ]))
                        elements.append(meal_table)
                    
                    # Add nutritional info if available
                    if "dailyCalories" in mp or "macronutrients" in mp:
                        elements.append(Spacer(1, 0.1*inch))
                        elements.append(Paragraph("Nutritional Information:", normal_style))
                        
                        nutri_data = []
                        calories = mp.get("dailyCalories", "N/A")
                        macros = mp.get("macronutrients", {})
                        
                        nutri_data.append(["Daily Calories", str(calories)])
                        if macros:
                            for macro, value in macros.items():
                                nutri_data.append([macro.title(), str(value)])
                        
                        nutri_table = Table(nutri_data, colWidths=[2*inch, 2*inch])
                        nutri_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ]))
                        elements.append(nutri_table)
                    
                    elements.append(Spacer(1, 0.2*inch))
                
                elements.append(PageBreak())
                
                # 3. Consumption History
                elements.append(Paragraph("3. Consumption History", section_title_style))
                elements.append(Paragraph(f"Total Records: {len(consumption_items)}", normal_style))
                elements.append(Spacer(1, 0.1*inch))
                
                # Display the 10 most recent consumption records
                recent_consumption = consumption_items[:10]
                
                if recent_consumption:
                    # Create table for consumption history
                    consumption_data = [["Date", "Food", "Meal Type", "Calories", "Carbs", "Protein", "Fat"]]
                    
                    for item in recent_consumption:
                        date = item.get("timestamp", "N/A")
                        if isinstance(date, str) and len(date) > 10:
                            date = date[:10]  # Just the date part
                            
                        food = item.get("food_name", "Unknown")
                        meal_type = item.get("meal_type", "N/A")
                        
                        nutrition = item.get("nutritional_info", {})
                        calories = nutrition.get("calories", "N/A")
                        carbs = nutrition.get("carbohydrates", "N/A")
                        protein = nutrition.get("protein", "N/A")
                        fat = nutrition.get("fat", "N/A")
                        
                        consumption_data.append([date, food, meal_type, calories, carbs, protein, fat])
                    
                    consumption_table = Table(consumption_data, colWidths=[1*inch, 2*inch, 0.8*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch])
                    consumption_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    elements.append(consumption_table)
                else:
                    elements.append(Paragraph("No consumption records found.", normal_style))
                
                elements.append(PageBreak())
                
                # 4. Chat History
                elements.append(Paragraph("4. Chat History", section_title_style))
                elements.append(Paragraph(f"Total Messages: {len(chat_logs)}", normal_style))
                elements.append(Spacer(1, 0.1*inch))
                
                # Display the 10 most recent chat messages
                recent_chats = chat_logs[:10]
                
                if recent_chats:
                    # Group by session
                    chat_sessions = {}
                    for chat in recent_chats:
                        session_id = chat.get("session_id", "default")
                        if session_id not in chat_sessions:
                            chat_sessions[session_id] = []
                        chat_sessions[session_id].append(chat)
                    
                    # Display each session
                    for session_id, messages in chat_sessions.items():
                        elements.append(Paragraph(f"Session: {session_id}", sub_title_style))
                        
                        chat_data = [["Time", "Role", "Message"]]
                        
                        for msg in messages:
                            timestamp = msg.get("timestamp", "N/A")
                            if isinstance(timestamp, str) and len(timestamp) > 16:
                                timestamp = timestamp[11:16]  # Just the time part
                                
                            role = msg.get("role", "user")
                            content = msg.get("content", "")
                            if len(content) > 100:
                                content = content[:97] + "..."
                            
                            chat_data.append([timestamp, role, content])
                        
                        chat_table = Table(chat_data, colWidths=[0.8*inch, 0.8*inch, 5*inch])
                        chat_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            # Style user vs assistant messages differently
                            ('BACKGROUND', (1, 1), (1, -1), colors.white),
                            ('TEXTCOLOR', (1, 1), (1, -1), colors.black),
                        ]))
                        elements.append(chat_table)
                        elements.append(Spacer(1, 0.2*inch))
                else:
                    elements.append(Paragraph("No chat history found.", normal_style))
                
                # Build the PDF
                doc.build(elements)
                buffer.seek(0)
                
                # Return the PDF
                return StreamingResponse(
                    buffer, 
                    media_type="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=my-data.pdf"}
                )
                
            except ImportError as e:
                print(f"PDF generation error (ImportError): {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail="PDF generation is not available. Please install reportlab package or try JSON format."
                )
            except Exception as e:
                print(f"PDF generation error: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to generate PDF: {str(e)}"
                )
        
    except Exception as e:
        print(f"Error exporting user data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}") 