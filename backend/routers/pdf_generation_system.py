from fastapi import APIRouter, HTTPException, Depends, Request as FastAPIRequest
from fastapi.responses import FileResponse
from typing import Dict, Any
from datetime import datetime
import os
import sys
from io import BytesIO
from models import User
from routers.auth import get_current_user
import traceback

# PDF generation imports
try:
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus.images import Image as RLImage
    PDF_AVAILABLE = True
except ImportError as e:
    print(f"Warning: PDF generation dependencies not available: {e}")
    PDF_AVAILABLE = False

router = APIRouter()

@router.post("/save-consolidated-pdf")
async def save_consolidated_pdf_endpoint(
    request: FastAPIRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Generates and saves a consolidated PDF, returns PDF info for storage reference."""
    if not PDF_AVAILABLE:
        raise HTTPException(status_code=503, detail="PDF generation service unavailable")
    
    try:
        data = await request.json()
        meal_plan = data.get('meal_plan', {})
        recipes = data.get('recipes', [])
        shopping_list = data.get('shopping_list', [])
        
        print("Generating consolidated PDF for saving...")
        
        # Generate PDF using the same logic as the download endpoint
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()
        
        # Add cover page
        try:
            cover_path = os.path.join("assets", "coverpage.png")
            elements.append(RLImage(cover_path, width=10*inch, height=6*inch))
            elements.append(Spacer(1, 48))
        except Exception as cover_err:
            print(f"Could not add cover page: {cover_err}")
        
        # Title
        elements.append(Paragraph("Consolidated Meal Plan", styles['Title']))
        elements.append(Spacer(1, 12))
        
        # Meal Plan Section
        elements.append(Paragraph("Meal Plan", styles['Heading1']))
        elements.append(Spacer(1, 12))
        data_table = [["Day", "Breakfast", "Lunch", "Dinner", "Snacks"]]
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for i, day in enumerate(days):
            data_table.append([
                day,
                meal_plan["breakfast"][i] if i < len(meal_plan["breakfast"]) else "",
                meal_plan["lunch"][i] if i < len(meal_plan["lunch"]) else "",
                meal_plan["dinner"][i] if i < len(meal_plan["dinner"]) else "",
                meal_plan["snacks"][i] if i < len(meal_plan["snacks"]) else "",
            ])
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
        for row in range(1, len(data_table)):
            for col in range(1, 5):
                table._cellvalues[row][col] = Paragraph(str(table._cellvalues[row][col]), styles['BodyText'])
        elements.append(table)
        elements.append(Spacer(1, 24))
        
        # Recipes Section (new page)
        elements.append(PageBreak())
        elements.append(Paragraph("Recipes", styles['Heading1']))
        elements.append(Spacer(1, 12))
        for recipe in recipes:
            elements.append(Paragraph(recipe["name"], styles['Heading2']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("Nutritional Information", styles['Heading3']))
            elements.append(Paragraph(f"Calories: {recipe['nutritional_info']['calories']}", styles['Normal']))
            elements.append(Paragraph(f"Protein: {recipe['nutritional_info']['protein']}", styles['Normal']))
            elements.append(Paragraph(f"Carbs: {recipe['nutritional_info']['carbs']}", styles['Normal']))
            elements.append(Paragraph(f"Fat: {recipe['nutritional_info']['fat']}", styles['Normal']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("Ingredients", styles['Heading3']))
            for ingredient in recipe["ingredients"]:
                elements.append(Paragraph(f"• {ingredient}", styles['Normal']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("Instructions", styles['Heading3']))
            for i, instruction in enumerate(recipe["instructions"], 1):
                elements.append(Paragraph(f"{i}. {instruction}", styles['Normal']))
            elements.append(Spacer(1, 24))
        
        # Shopping List Section (new page)
        elements.append(PageBreak())
        elements.append(Paragraph("Shopping List", styles['Heading1']))
        elements.append(Spacer(1, 12))
        categories = {}
        for item in shopping_list:
            if item["category"] not in categories:
                categories[item["category"]] = []
            categories[item["category"]].append(item)
        for category, items in categories.items():
            elements.append(Paragraph(category, styles['Heading2']))
            elements.append(Spacer(1, 12))
            for item in items:
                elements.append(Paragraph(f"• {item['name']} - {item['amount']}", styles['Normal']))
            elements.append(Spacer(1, 24))
        
        doc.build(elements)
        buffer.seek(0)
        
        # Create filename
        username = current_user["email"].split("@")[0]
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{username}_{date_str}_consolidated_meal_plan.pdf"
        
        # Save PDF to a storage directory (create directory if it doesn't exist)
        storage_dir = os.path.join("storage", "pdfs")
        os.makedirs(storage_dir, exist_ok=True)
        file_path = os.path.join(storage_dir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(buffer.getvalue())
        
        # Return PDF info for storage in meal plan
        pdf_info = {
            "filename": filename,
            "file_path": file_path,
            "generated_at": datetime.now().isoformat(),
            "file_size": len(buffer.getvalue())
        }
        
        print(f"Consolidated PDF saved to: {file_path}")
        return {"pdf_info": pdf_info}
        
    except Exception as e:
        print("Error in /save-consolidated-pdf:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download-saved-pdf/{filename}")
async def download_saved_pdf(
    filename: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Download a previously saved consolidated PDF"""
    try:
        # Security check: ensure filename is safe and belongs to user
        username = current_user["email"].split("@")[0]
        if not filename.startswith(username) or ".." in filename or "/" in filename:
            raise HTTPException(status_code=403, detail="Access denied")
        
        file_path = os.path.join("storage", "pdfs", filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        return FileResponse(
            file_path,
            media_type="application/pdf",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error downloading saved PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 