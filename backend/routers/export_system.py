"""
Export System Router
Handles PDF export functionality for meal plans, recipes, and shopping lists.
Provides consolidated and individual document export capabilities.
"""

from fastapi import APIRouter, HTTPException, Depends, Request as FastAPIRequest
from fastapi.responses import StreamingResponse
from typing import Dict, Any
from datetime import datetime
from io import BytesIO
import traceback

from models import User
from routers.auth import get_current_user
from database import get_user_meal_plans, get_user_recipes, get_user_shopping_lists

# ReportLab imports for PDF generation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

router = APIRouter()

@router.post("/export/consolidated-meal-plan")
async def export_consolidated_meal_plan(current_user: User = Depends(get_current_user)):
    try:
        print(">>>> Entered /export/consolidated-meal-plan endpoint")
        # Fetch meal plans
        meal_plans = await get_user_meal_plans(current_user["email"])
        if not meal_plans:
            print("No meal plan found")
            raise HTTPException(status_code=404, detail="No meal plan found")
        latest_meal_plan = meal_plans[-1]
        print("meal_plan:", latest_meal_plan)
        # Fetch latest recipes and shopping list for the user
        all_recipes = await get_user_recipes(current_user["email"])
        recipes = all_recipes[-1]["recipes"] if all_recipes else []
        all_shopping_lists = await get_user_shopping_lists(current_user["email"])
        shopping_list = all_shopping_lists[-1]["items"] if all_shopping_lists else []
        print("recipes:", recipes)
        print("shopping_list:", shopping_list)
        # Generate PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=15,
            textColor=colors.darkgreen
        )
        
        # Title
        elements.append(Paragraph("Comprehensive Meal Plan", title_style))
        elements.append(Spacer(1, 20))
        
        # Meal Plan Section
        elements.append(Paragraph("Weekly Meal Plan", heading_style))
        if latest_meal_plan:
            # Add meal plan table
            meal_data = [["Day", "Breakfast", "Lunch", "Dinner", "Snacks"]]
            
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            breakfast_meals = latest_meal_plan.get("breakfast", [])
            lunch_meals = latest_meal_plan.get("lunch", [])
            dinner_meals = latest_meal_plan.get("dinner", [])
            snack_meals = latest_meal_plan.get("snacks", [])
            
            for i, day in enumerate(days):
                breakfast = breakfast_meals[i] if i < len(breakfast_meals) else "Not specified"
                lunch = lunch_meals[i] if i < len(lunch_meals) else "Not specified"
                dinner = dinner_meals[i] if i < len(dinner_meals) else "Not specified"
                snacks = snack_meals[i] if i < len(snack_meals) else "Not specified"
                
                meal_data.append([
                    day,
                    Paragraph(breakfast[:50] + "..." if len(breakfast) > 50 else breakfast, styles['Normal']),
                    Paragraph(lunch[:50] + "..." if len(lunch) > 50 else lunch, styles['Normal']),
                    Paragraph(dinner[:50] + "..." if len(dinner) > 50 else dinner, styles['Normal']),
                    Paragraph(snacks[:50] + "..." if len(snacks) > 50 else snacks, styles['Normal'])
                ])
            
            meal_table = Table(meal_data, colWidths=[1*inch, 2*inch, 2*inch, 2*inch, 1.5*inch])
            meal_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(meal_table)
        
        elements.append(Spacer(1, 30))
        
        # Recipes Section
        elements.append(Paragraph("Recipe Collection", heading_style))
        if recipes:
            for i, recipe in enumerate(recipes[:5], 1):  # Limit to 5 recipes
                recipe_name = recipe.get("name", f"Recipe {i}")
                ingredients = recipe.get("ingredients", [])
                instructions = recipe.get("instructions", "No instructions provided")
                
                elements.append(Paragraph(f"{i}. {recipe_name}", styles['Heading2']))
                elements.append(Paragraph(f"<b>Ingredients:</b> {', '.join(ingredients[:10])}", styles['Normal']))
                elements.append(Paragraph(f"<b>Instructions:</b> {instructions[:200]}...", styles['Normal']))
                elements.append(Spacer(1, 10))
        else:
            elements.append(Paragraph("No recipes available", styles['Normal']))
        
        elements.append(Spacer(1, 30))
        
        # Shopping List Section
        elements.append(Paragraph("Shopping List", heading_style))
        if shopping_list:
            # Group items by category
            categorized_items = {}
            for item in shopping_list:
                category = item.get("category", "Miscellaneous")
                if category not in categorized_items:
                    categorized_items[category] = []
                categorized_items[category].append(item.get("name", "Unknown item"))
            
            for category, items in categorized_items.items():
                elements.append(Paragraph(f"<b>{category}:</b>", styles['Heading3']))
                for item in items:
                    elements.append(Paragraph(f"• {item}", styles['Normal']))
                elements.append(Spacer(1, 10))
        else:
            elements.append(Paragraph("No shopping list available", styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        filename = f"consolidated-meal-plan-{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        print("Error in /export/consolidated-meal-plan:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export/{type}")
async def export_document(
    type: str,
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        data = await request.json()
        
        if type == "meal-plan":
            content = data["meal_plan"]
            title = "Meal Plan"
        elif type == "recipes":
            content = data["recipes"]
            title = "Recipe Collection"
        elif type == "shopping-list":
            content = data["shopping_list"]
            title = "Shopping List"
        else:
            raise HTTPException(status_code=400, detail="Invalid export type")

        # Generate PDF using reportlab
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=20,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Title
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 20))
        
        # Content based on type
        if type == "meal-plan":
            # Meal plan content
            if isinstance(content, dict):
                for meal_type, meals in content.items():
                    if isinstance(meals, list) and meals:
                        elements.append(Paragraph(f"<b>{meal_type.title()}:</b>", styles['Heading2']))
                        for i, meal in enumerate(meals, 1):
                            elements.append(Paragraph(f"{i}. {meal}", styles['Normal']))
                        elements.append(Spacer(1, 15))
        
        elif type == "recipes":
            # Recipe content
            if isinstance(content, list):
                for i, recipe in enumerate(content, 1):
                    recipe_name = recipe.get("name", f"Recipe {i}")
                    ingredients = recipe.get("ingredients", [])
                    instructions = recipe.get("instructions", "No instructions provided")
                    
                    elements.append(Paragraph(f"{i}. {recipe_name}", styles['Heading2']))
                    elements.append(Paragraph(f"<b>Ingredients:</b>", styles['Heading3']))
                    for ingredient in ingredients:
                        elements.append(Paragraph(f"• {ingredient}", styles['Normal']))
                    elements.append(Paragraph(f"<b>Instructions:</b>", styles['Heading3']))
                    elements.append(Paragraph(instructions, styles['Normal']))
                    elements.append(Spacer(1, 20))
        
        elif type == "shopping-list":
            # Shopping list content
            if isinstance(content, list):
                # Group by category if available
                categorized = {}
                for item in content:
                    category = item.get("category", "Items")
                    if category not in categorized:
                        categorized[category] = []
                    categorized[category].append(item.get("name", "Unknown item"))
                
                for category, items in categorized.items():
                    elements.append(Paragraph(f"<b>{category}:</b>", styles['Heading2']))
                    for item in items:
                        elements.append(Paragraph(f"• {item}", styles['Normal']))
                    elements.append(Spacer(1, 15))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={type}-{datetime.now().strftime('%Y%m%d')}.pdf"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))