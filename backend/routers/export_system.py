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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os

router = APIRouter()

@router.post("/export/recipes")
async def export_recipes_pdf(current_user: User = Depends(get_current_user)):
    """
    Export the user's latest recipes as a beautiful PDF.
    Fetches recipes directly from the database to ensure accuracy.
    """
    try:
        print(f">>>> Entered /export/recipes endpoint for user {current_user['email']}")
        
        # Fetch latest recipes from database
        all_recipes = await get_user_recipes(current_user["email"], limit=1)
        if not all_recipes:
            print("No recipes found in database")
            raise HTTPException(status_code=404, detail="No recipes found. Please generate recipes first.")
        
        # Extract the recipes array from the latest recipe document
        latest_recipe_doc = all_recipes[0]
        recipes = latest_recipe_doc.get("recipes", [])
        
        if not recipes:
            print("Latest recipe document has no recipes array")
            raise HTTPException(status_code=404, detail="No recipes found in the latest recipe collection.")
        
        print(f"Found {len(recipes)} recipes to export")
        
        # Generate PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)  # Use portrait for recipes
        elements = []
        styles = getSampleStyleSheet()
        
        # Main title style
        main_title_style = ParagraphStyle(
            'MainTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkgreen,
            fontName='Helvetica-Bold'
        )
        
        # Add main title
        elements.append(Paragraph("🍽️ Diabetes-Friendly Recipe Collection", main_title_style))
        
        # Add collection overview
        overview_style = ParagraphStyle(
            'Overview',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=25,
            alignment=TA_CENTER,
            textColor=colors.grey,
            fontName='Helvetica-Oblique'
        )
        
        current_date = datetime.now().strftime("%B %d, %Y")
        elements.append(Paragraph(f"Generated on {current_date}", overview_style))
        elements.append(Paragraph(f"This collection contains {len(recipes)} carefully crafted recipes", overview_style))
        elements.append(Spacer(1, 20))
        
        # Define custom styles for recipes
        recipe_title_style = ParagraphStyle(
            'RecipeTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=12,
            spaceBefore=25,
            textColor=colors.darkgreen,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=colors.lightgrey,
            borderPadding=8,
            backColor=colors.lightgrey
        )
        
        section_heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.darkblue,
            leftIndent=5,
            fontName='Helvetica-Bold'
        )
        
        ingredient_style = ParagraphStyle(
            'Ingredient',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=4,
            leftIndent=15,
            textColor=colors.black,
            fontName='Helvetica'
        )
        
        instruction_style = ParagraphStyle(
            'Instruction',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            spaceBefore=4,
            leftIndent=5,
            textColor=colors.black,
            leading=14,
            fontName='Helvetica'
        )
        
        # Process each recipe
        for i, recipe in enumerate(recipes, 1):
            # Recipe title with number
            recipe_name = recipe.get("name", f"Recipe {i}")
            elements.append(Paragraph(f"Recipe {i}: {recipe_name}", recipe_title_style))
            
            # Nutritional information box (if available)
            nutritional_info = recipe.get("nutritional_info", {})
            if nutritional_info:
                elements.append(Paragraph("🍎 Nutritional Information (per serving)", section_heading_style))
                
                # Create a table for nutritional info
                nutrition_data = [
                    ['Nutrient', 'Amount'],
                    ['Calories', f"{nutritional_info.get('calories', 'N/A')} kcal"],
                    ['Protein', f"{nutritional_info.get('protein', 'N/A')} g"],
                    ['Carbohydrates', f"{nutritional_info.get('carbs', nutritional_info.get('carbohydrates', 'N/A'))} g"],
                    ['Fat', f"{nutritional_info.get('fat', 'N/A')} g"],
                    ['Fiber', f"{nutritional_info.get('fiber', 'N/A')} g"],
                    ['Sugar', f"{nutritional_info.get('sugar', 'N/A')} g"]
                ]
                
                nutrition_table = Table(nutrition_data, colWidths=[2.5*inch, 2*inch])
                nutrition_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightcyan),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]))
                elements.append(nutrition_table)
                elements.append(Spacer(1, 15))
            
            # Ingredients section
            ingredients = recipe.get("ingredients", [])
            if ingredients:
                elements.append(Paragraph("🥕 Ingredients", section_heading_style))
                for ingredient in ingredients:
                    elements.append(Paragraph(f"• {ingredient}", ingredient_style))
                elements.append(Spacer(1, 12))
            
            # Instructions section
            instructions = recipe.get("instructions", "No instructions provided")
            if instructions:
                elements.append(Paragraph("👨‍🍳 Instructions", section_heading_style))
                
                # Handle both string and list instructions
                if isinstance(instructions, list):
                    for j, instruction in enumerate(instructions, 1):
                        elements.append(Paragraph(f"{j}. {instruction}", instruction_style))
                else:
                    # Split string instructions by sentences or steps
                    instruction_steps = [step.strip() for step in instructions.split('.') if step.strip()]
                    if len(instruction_steps) > 1:
                        for j, step in enumerate(instruction_steps, 1):
                            if step:  # Only add non-empty steps
                                elements.append(Paragraph(f"{j}. {step}.", instruction_style))
                    else:
                        elements.append(Paragraph(instructions, instruction_style))
                elements.append(Spacer(1, 10))
            
            # Diabetes-friendly note
            diabetes_note_style = ParagraphStyle(
                'DiabetesNote',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=15,
                spaceBefore=8,
                leftIndent=5,
                textColor=colors.green,
                fontName='Helvetica-Oblique',
                backColor=colors.lightgreen,
                borderWidth=0.5,
                borderColor=colors.green,
                borderPadding=6
            )
            elements.append(Paragraph("💚 This recipe is designed to be diabetes-friendly with balanced macronutrients.", diabetes_note_style))
            
            # Add page break between recipes (except for the last one) if there are many recipes
            if i < len(recipes) and len(recipes) > 3:
                elements.append(PageBreak())
            elif i < len(recipes):
                elements.append(Spacer(1, 25))
                # Add a subtle line separator
                line_style = ParagraphStyle(
                    'LineSeparator',
                    parent=styles['Normal'],
                    fontSize=8,
                    spaceAfter=20,
                    alignment=TA_CENTER,
                    textColor=colors.lightgrey
                )
                elements.append(Paragraph("─" * 60, line_style))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        username = current_user["email"].split("@")[0]
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"{username}_{date_str}_recipe_collection.pdf"
        
        print(f"Successfully generated recipe PDF: {filename}")
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException as he:
        print(f"HTTP Exception in /export/recipes: {str(he.detail)}")
        raise he
    except Exception as e:
        print(f"Error in /export/recipes: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to export recipes: {str(e)}")

@router.post("/export/consolidated-meal-plan")
async def export_consolidated_meal_plan(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Export a comprehensive consolidated meal plan PDF with professional formatting.
    Accepts current meal plan data from frontend or falls back to database fetch.
    """
    try:
        print(">>>> Entered /export/consolidated-meal-plan endpoint")
        
        # Try to get data from request body first (current generated data)
        try:
            data = await request.json()
            latest_meal_plan = data.get('meal_plan', {})
            recipes = data.get('recipes', [])
            shopping_list = data.get('shopping_list', [])
            print(f"Using provided data: meal_plan={bool(latest_meal_plan)}, recipes={len(recipes)}, shopping_list={len(shopping_list)}")
        except:
            # Fallback to database fetch if no data provided (backward compatibility)
            print("No data provided in request, fetching from database...")
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
            print(f"Found {len(recipes)} recipes and {len(shopping_list)} shopping list items from database")
        
        # Generate PDF with professional formatting
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()
        
        # Add cover page (if available)
        try:
            cover_path = os.path.join("assets", "coverpage.png")
            if os.path.exists(cover_path):
                elements.append(RLImage(cover_path, width=10*inch, height=6*inch))
                elements.append(Spacer(1, 48))
                print("Added cover page to consolidated PDF")
            else:
                print(f"Cover page not found at {cover_path}")
        except Exception as cover_err:
            print(f"Could not add cover page: {cover_err}")
        
        # Professional title
        title_style = ParagraphStyle(
            'ProfessionalTitle',
            parent=styles['Title'],
            fontSize=28,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph("Consolidated Meal Plan", title_style))
        elements.append(Spacer(1, 12))
        
        # Meal Plan Section
        section_heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=12,
            spaceBefore=12,
            textColor=colors.darkgreen,
            fontName='Helvetica-Bold'
        )
        
        elements.append(Paragraph("Meal Plan", section_heading_style))
        elements.append(Spacer(1, 12))
        
        # Create meal plan table with better formatting
        data_table = [["Day", "Breakfast", "Lunch", "Dinner", "Snacks"]]
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for i, day in enumerate(days):
            breakfast = latest_meal_plan.get("breakfast", [])[i] if i < len(latest_meal_plan.get("breakfast", [])) else "Not specified"
            lunch = latest_meal_plan.get("lunch", [])[i] if i < len(latest_meal_plan.get("lunch", [])) else "Not specified"
            dinner = latest_meal_plan.get("dinner", [])[i] if i < len(latest_meal_plan.get("dinner", [])) else "Not specified"
            snacks = latest_meal_plan.get("snacks", [])[i] if i < len(latest_meal_plan.get("snacks", [])) else "Not specified"
            
            data_table.append([
                day,
                breakfast,
                lunch,
                dinner,
                snacks,
            ])
        
        # Create table with professional styling
        col_widths = [0.8*inch, 2.5*inch, 2.5*inch, 2.5*inch, 2.5*inch]
        table = Table(data_table, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        # Apply paragraph styling to table cells for better text wrapping
        for row in range(1, len(data_table)):
            for col in range(1, 5):
                table._cellvalues[row][col] = Paragraph(str(table._cellvalues[row][col]), styles['BodyText'])
        
        elements.append(table)
        elements.append(Spacer(1, 24))
        
        # Recipes Section (new page for better organization)
        elements.append(PageBreak())
        elements.append(Paragraph("Recipes", section_heading_style))
        elements.append(Spacer(1, 12))
        
        if recipes:
            for recipe in recipes:
                recipe_name = recipe.get("name", "Unknown Recipe")
                elements.append(Paragraph(recipe_name, styles['Heading2']))
                elements.append(Spacer(1, 12))
                
                # Nutritional Information
                nutritional_info = recipe.get('nutritional_info', {})
                if nutritional_info:
                    elements.append(Paragraph("Nutritional Information", styles['Heading3']))
                    elements.append(Paragraph(f"Calories: {nutritional_info.get('calories', 'N/A')}", styles['Normal']))
                    elements.append(Paragraph(f"Protein: {nutritional_info.get('protein', 'N/A')}g", styles['Normal']))
                    elements.append(Paragraph(f"Carbs: {nutritional_info.get('carbs', nutritional_info.get('carbohydrates', 'N/A'))}g", styles['Normal']))
                    elements.append(Paragraph(f"Fat: {nutritional_info.get('fat', 'N/A')}g", styles['Normal']))
                    elements.append(Spacer(1, 12))
                
                # Ingredients
                ingredients = recipe.get("ingredients", [])
                if ingredients:
                    elements.append(Paragraph("Ingredients", styles['Heading3']))
                    for ingredient in ingredients:
                        elements.append(Paragraph(f"• {ingredient}", styles['Normal']))
                    elements.append(Spacer(1, 12))
                
                # Instructions
                instructions = recipe.get("instructions", [])
                if instructions:
                    elements.append(Paragraph("Instructions", styles['Heading3']))
                    if isinstance(instructions, list):
                        for i, instruction in enumerate(instructions, 1):
                            elements.append(Paragraph(f"{i}. {instruction}", styles['Normal']))
                    else:
                        elements.append(Paragraph(str(instructions), styles['Normal']))
                    elements.append(Spacer(1, 24))
        else:
            elements.append(Paragraph("No recipes available", styles['Normal']))
        
        # Shopping List Section (new page for better organization)
        elements.append(PageBreak())
        elements.append(Paragraph("Shopping List", section_heading_style))
        elements.append(Spacer(1, 12))
        
        if shopping_list:
            # Group items by category
            categories = {}
            for item in shopping_list:
                category = item.get("category", "Miscellaneous")
                if category not in categories:
                    categories[category] = []
                categories[category].append(item)
            
            # Display each category
            for category, items in categories.items():
                elements.append(Paragraph(category, styles['Heading2']))
                elements.append(Spacer(1, 12))
                for item in items:
                    item_name = item.get('name', 'Unknown item')
                    item_amount = item.get('amount', '')
                    if item_amount:
                        elements.append(Paragraph(f"• {item_name} - {item_amount}", styles['Normal']))
                    else:
                        elements.append(Paragraph(f"• {item_name}", styles['Normal']))
                elements.append(Spacer(1, 24))
        else:
            elements.append(Paragraph("No shopping list available", styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        # Create professional filename
        username = current_user["email"].split("@")[0]
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"{username}_{date_str}_consolidated_meal_plan.pdf"
        
        print(f"Successfully generated consolidated PDF: {filename}")
        
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
            # Recipe content - Create beautiful, professional recipe PDF
            if isinstance(content, list):
                # Define custom styles for recipes
                recipe_title_style = ParagraphStyle(
                    'RecipeTitle',
                    parent=styles['Heading1'],
                    fontSize=18,
                    spaceAfter=12,
                    spaceBefore=20,
                    textColor=colors.darkgreen,
                    alignment=TA_LEFT,
                    borderWidth=0,
                    borderColor=colors.darkgreen,
                    borderPadding=8
                )
                
                section_heading_style = ParagraphStyle(
                    'SectionHeading',
                    parent=styles['Heading2'],
                    fontSize=14,
                    spaceAfter=8,
                    spaceBefore=12,
                    textColor=colors.darkblue,
                    leftIndent=10
                )
                
                ingredient_style = ParagraphStyle(
                    'Ingredient',
                    parent=styles['Normal'],
                    fontSize=11,
                    spaceAfter=4,
                    leftIndent=20,
                    bulletIndent=15,
                    textColor=colors.black
                )
                
                instruction_style = ParagraphStyle(
                    'Instruction',
                    parent=styles['Normal'],
                    fontSize=11,
                    spaceAfter=6,
                    spaceBefore=6,
                    leftIndent=10,
                    textColor=colors.black,
                    leading=14
                )
                
                nutrition_style = ParagraphStyle(
                    'Nutrition',
                    parent=styles['Normal'],
                    fontSize=10,
                    spaceAfter=3,
                    leftIndent=20,
                    textColor=colors.darkred
                )
                
                # Add recipe collection overview
                overview_style = ParagraphStyle(
                    'Overview',
                    parent=styles['Normal'],
                    fontSize=12,
                    spaceAfter=20,
                    alignment=TA_CENTER,
                    textColor=colors.grey
                )
                
                elements.append(Paragraph(f"This collection contains {len(content)} diabetes-friendly recipes", overview_style))
                elements.append(Spacer(1, 10))
                
                # Process each recipe
                for i, recipe in enumerate(content, 1):
                    # Recipe title with number
                    recipe_name = recipe.get("name", f"Recipe {i}")
                    elements.append(Paragraph(f"Recipe {i}: {recipe_name}", recipe_title_style))
                    
                    # Nutritional information box (if available)
                    nutritional_info = recipe.get("nutritional_info", {})
                    if nutritional_info:
                        elements.append(Paragraph("🍎 Nutritional Information (per serving)", section_heading_style))
                        
                        # Create a table for nutritional info
                        nutrition_data = [
                            ['Nutrient', 'Amount'],
                            ['Calories', f"{nutritional_info.get('calories', 'N/A')} kcal"],
                            ['Protein', f"{nutritional_info.get('protein', 'N/A')} g"],
                            ['Carbohydrates', f"{nutritional_info.get('carbs', nutritional_info.get('carbohydrates', 'N/A'))} g"],
                            ['Fat', f"{nutritional_info.get('fat', 'N/A')} g"],
                            ['Fiber', f"{nutritional_info.get('fiber', 'N/A')} g"],
                            ['Sugar', f"{nutritional_info.get('sugar', 'N/A')} g"]
                        ]
                        
                        nutrition_table = Table(nutrition_data, colWidths=[2*inch, 1.5*inch])
                        nutrition_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 1), (-1, -1), 9),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ]))
                        elements.append(nutrition_table)
                        elements.append(Spacer(1, 12))
                    
                    # Ingredients section
                    ingredients = recipe.get("ingredients", [])
                    if ingredients:
                        elements.append(Paragraph("🥕 Ingredients", section_heading_style))
                        for ingredient in ingredients:
                            elements.append(Paragraph(f"• {ingredient}", ingredient_style))
                        elements.append(Spacer(1, 10))
                    
                    # Instructions section
                    instructions = recipe.get("instructions", "No instructions provided")
                    if instructions:
                        elements.append(Paragraph("👨‍🍳 Instructions", section_heading_style))
                        
                        # Handle both string and list instructions
                        if isinstance(instructions, list):
                            for j, instruction in enumerate(instructions, 1):
                                elements.append(Paragraph(f"{j}. {instruction}", instruction_style))
                        else:
                            # Split string instructions by sentences or steps
                            instruction_steps = [step.strip() for step in instructions.split('.') if step.strip()]
                            if len(instruction_steps) > 1:
                                for j, step in enumerate(instruction_steps, 1):
                                    if step:  # Only add non-empty steps
                                        elements.append(Paragraph(f"{j}. {step}.", instruction_style))
                            else:
                                elements.append(Paragraph(instructions, instruction_style))
                    
                    # Diabetes-friendly note
                    diabetes_note_style = ParagraphStyle(
                        'DiabetesNote',
                        parent=styles['Normal'],
                        fontSize=10,
                        spaceAfter=8,
                        spaceBefore=8,
                        leftIndent=10,
                        textColor=colors.green,
                        fontName='Helvetica-Oblique'
                    )
                    elements.append(Paragraph("💚 This recipe is designed to be diabetes-friendly with balanced macronutrients.", diabetes_note_style))
                    
                    # Add separator between recipes (except for the last one)
                    if i < len(content):
                        elements.append(Spacer(1, 20))
                        # Add a subtle line separator
                        line_style = ParagraphStyle(
                            'LineSeparator',
                            parent=styles['Normal'],
                            fontSize=8,
                            spaceAfter=15,
                            alignment=TA_CENTER,
                            textColor=colors.lightgrey
                        )
                        elements.append(Paragraph("─" * 50, line_style))
                        elements.append(Spacer(1, 10))
        
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