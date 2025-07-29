"""
Privacy & Data Management Router
Handles GDPR compliance, data export, account deletion, and consent management.
"""

import os
from datetime import datetime
from io import BytesIO
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Request as FastAPIRequest
from fastapi.responses import JSONResponse, StreamingResponse

from models import User
from routers.auth import get_current_user
from database import (
    get_user_by_email, get_user_meal_plans, get_user_consumption_history,
    get_recent_chat_history, get_user_recipes, get_user_shopping_lists,
    delete_all_user_meal_plans, user_container, interactions_container
)

router = APIRouter()

@router.post("/privacy/export-data")
async def export_privacy_data(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user)
):
    """Export user's privacy data in specified format (PDF, JSON, or DOCX)"""
    try:
        data = await request.json()
        data_types = data.get("data_types", [])
        format_type = data.get("format_type", "pdf")
        
        if not data_types:
            raise HTTPException(status_code=400, detail="Please specify data types to export")
        
        if format_type not in ["pdf", "json", "docx"]:
            raise HTTPException(status_code=400, detail="Invalid format type. Use pdf, json, or docx")
        
        print(f"[PRIVACY_EXPORT] Exporting data for user {current_user['email']}")
        print(f"[PRIVACY_EXPORT] Data types: {data_types}")
        print(f"[PRIVACY_EXPORT] Format: {format_type}")
        
        # Collect user data based on requested types
        export_data = {}
        
        # Get user profile
        if "profile" in data_types:
            try:
                user_doc = await get_user_by_email(current_user["email"])
                if user_doc:
                    export_data["profile"] = user_doc.get("profile", {})
            except Exception as e:
                print(f"[PRIVACY_EXPORT] Error getting profile: {e}")
                export_data["profile"] = {}
        
        # Get meal plans
        if "meal_plans" in data_types:
            try:
                meal_plans = await get_user_meal_plans(current_user["email"])
                export_data["meal_plans"] = meal_plans
            except Exception as e:
                print(f"[PRIVACY_EXPORT] Error getting meal plans: {e}")
                export_data["meal_plans"] = []
        
        # Get consumption history
        if "consumption_history" in data_types:
            try:
                consumption_history = await get_user_consumption_history(current_user["email"], limit=100)
                export_data["consumption_history"] = consumption_history
            except Exception as e:
                print(f"[PRIVACY_EXPORT] Error getting consumption history: {e}")
                export_data["consumption_history"] = []
        
        # Get chat history
        if "chat_history" in data_types:
            try:
                chat_history = await get_recent_chat_history(current_user["email"], limit=100)
                export_data["chat_history"] = chat_history
            except Exception as e:
                print(f"[PRIVACY_EXPORT] Error getting chat history: {e}")
                export_data["chat_history"] = []
        
        # Get recipes
        if "recipes" in data_types:
            try:
                recipes = await get_user_recipes(current_user["email"])
                export_data["recipes"] = recipes
            except Exception as e:
                print(f"[PRIVACY_EXPORT] Error getting recipes: {e}")
                export_data["recipes"] = []
        
        # Get shopping lists
        if "shopping_lists" in data_types:
            try:
                shopping_lists = await get_user_shopping_lists(current_user["email"])
                export_data["shopping_lists"] = shopping_lists
            except Exception as e:
                print(f"[PRIVACY_EXPORT] Error getting shopping lists: {e}")
                export_data["shopping_lists"] = []
        
        # Prepare user info for export
        user_info = {
            "email": current_user["email"],
            "consent_given": current_user.get("consent_given", False),
            "marketing_consent": current_user.get("marketing_consent", False),
            "analytics_consent": current_user.get("analytics_consent", False),
            "data_retention_preference": current_user.get("data_retention_preference", "standard"),
            "policy_version": current_user.get("policy_version", "1.0")
        }
        
        print(f"[PRIVACY_EXPORT] Collected data for {len(data_types)} data types")
        
        # Generate export based on format
        if format_type == "pdf":
            return await generate_data_export_pdf(export_data, user_info)
        elif format_type == "docx":
            return await generate_data_export_docx(export_data, user_info)
        else:  # json
            filename = f"health_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            return JSONResponse(
                content={
                    "export_data": export_data,
                    "user_info": user_info,
                    "export_timestamp": datetime.now().isoformat(),
                    "format": "json"
                },
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[PRIVACY_EXPORT] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.delete("/privacy/delete-account")
async def delete_account(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user)
):
    """Delete user account and all associated data"""
    try:
        data = await request.json()
        deletion_type = data.get("deletion_type", "complete")
        confirmation = data.get("confirmation", "")
        
        if confirmation.upper() != "DELETE":
            raise HTTPException(status_code=400, detail="Invalid confirmation. Type DELETE to confirm.")
        
        print(f"[PRIVACY_DELETE] Deleting account for user {current_user['email']}")
        print(f"[PRIVACY_DELETE] Deletion type: {deletion_type}")
        
        user_email = current_user["email"]
        
        # Delete user data from various containers
        try:
            # Delete user profile and main record from user_container
            try:
                user_doc = await get_user_by_email(user_email)
                if user_doc:
                    user_container.delete_item(item=user_doc, partition_key=user_email)
            except Exception as e:
                print(f"[PRIVACY_DELETE] Error deleting user document: {str(e)}")
            
            # Delete meal plans
            await delete_all_user_meal_plans(user_email)
            
            # Delete consumption history
            query = f"SELECT * FROM c WHERE c.user_id = '{user_email}' AND c.type = 'consumption_record'"
            consumption_records = list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
            for record in consumption_records:
                interactions_container.delete_item(item=record, partition_key=record.get("session_id", user_email))
            
            # Delete chat history
            query = f"SELECT * FROM c WHERE c.user_id = '{user_email}' AND c.type = 'chat_message'"
            chat_messages = list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
            for message in chat_messages:
                interactions_container.delete_item(item=message, partition_key=message.get("session_id", user_email))
            
            # Delete recipes
            query = f"SELECT * FROM c WHERE c.user_id = '{user_email}' AND c.type = 'recipes'"
            recipes = list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
            for recipe in recipes:
                interactions_container.delete_item(item=recipe, partition_key=recipe.get("session_id", user_email))
            
            # Delete shopping lists
            query = f"SELECT * FROM c WHERE c.user_id = '{user_email}' AND c.type = 'shopping_list'"
            shopping_lists = list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
            for shopping_list in shopping_lists:
                interactions_container.delete_item(item=shopping_list, partition_key=shopping_list.get("session_id", user_email))
            
            print(f"[PRIVACY_DELETE] Successfully deleted all data for user {user_email}")
            
        except Exception as e:
            print(f"[PRIVACY_DELETE] Error during data deletion: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete user data: {str(e)}")
        
        return {"message": "Account deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[PRIVACY_DELETE] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Account deletion failed: {str(e)}")

@router.put("/privacy/update-consent")
async def update_consent(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user)
):
    """Update user consent preferences"""
    try:
        data = await request.json()
        
        print(f"[PRIVACY_CONSENT] Updating consent for user {current_user['email']}")
        print(f"[PRIVACY_CONSENT] New consent settings: {data}")
        
        # Update user record with new consent settings
        user_email = current_user["email"]
        
        try:
            # Get current user document
            user_doc = await get_user_by_email(user_email)
            if not user_doc:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Update consent fields
            user_doc["consent_given"] = data.get("consent_given", user_doc.get("consent_given", False))
            user_doc["marketing_consent"] = data.get("marketing_consent", user_doc.get("marketing_consent", False))
            user_doc["analytics_consent"] = data.get("analytics_consent", user_doc.get("analytics_consent", False))
            user_doc["data_retention_preference"] = data.get("data_retention_preference", user_doc.get("data_retention_preference", "standard"))
            user_doc["last_consent_update"] = datetime.utcnow().isoformat()
            
            # Update the user document
            user_container.upsert_item(body=user_doc)
            
            print(f"[PRIVACY_CONSENT] Successfully updated consent for user {user_email}")
            
        except Exception as e:
            print(f"[PRIVACY_CONSENT] Error updating consent: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update consent: {str(e)}")
        
        return {"message": "Consent preferences updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[PRIVACY_CONSENT] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Consent update failed: {str(e)}")

async def generate_data_export_pdf(export_data: dict, user_info: dict):
    """Generate professional PDF export of user data with logo and improved layout"""
    try:
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
        import os
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=72, leftMargin=72,
            topMargin=100, bottomMargin=72,
            title="Health Data Export"
        )
        
        # Custom styles
        styles = getSampleStyleSheet()
        
        # Define custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2E7D32')
        )
        
        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            spaceBefore=30,
            textColor=colors.HexColor('#1976D2'),
            borderWidth=1,
            borderColor=colors.HexColor('#1976D2'),
            borderPadding=10,
            backColor=colors.HexColor('#E3F2FD')
        )
        
        subsection_style = ParagraphStyle(
            'SubSection',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=15,
            textColor=colors.HexColor('#424242')
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            leading=12,
            alignment=TA_JUSTIFY
        )
        
        story = []
        
        # Header with logo
        def add_logo_header():
            header_content = []
            logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "coverpage2.png")
            
            if os.path.exists(logo_path):
                try:
                    # Create header table with logo
                    logo_img = RLImage(logo_path, width=2*inch, height=1*inch)
                    header_data = [
                        ["Diabetes Meal Plan Generator", logo_img],
                        ["Personal Health Data Export", ""]
                    ]
                    header_table = Table(header_data, colWidths=[5*inch, 2*inch])
                    header_table.setStyle(TableStyle([
                        ('ALIGN', (0,0), (0,-1), 'LEFT'),
                        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                        ('FONTSIZE', (0,0), (0,0), 16),
                        ('FONTSIZE', (0,1), (0,1), 12),
                        ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#2E7D32')),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                    ]))
                    header_content.append(header_table)
                except Exception as e:
                    print(f"Logo error: {e}")
                    header_content.append(Paragraph("Diabetes Meal Plan Generator", title_style))
                    header_content.append(Paragraph("Personal Health Data Export", styles['Heading2']))
            else:
                header_content.append(Paragraph("Diabetes Meal Plan Generator", title_style))
                header_content.append(Paragraph("Personal Health Data Export", styles['Heading2']))
            
            return header_content
            
        # Add header
        story.extend(add_logo_header())
        story.append(Spacer(1, 30))
        
        # User information section
        story.append(Paragraph("User Information", section_title_style))
        story.append(Paragraph(f"<b>Email:</b> {user_info['email']}", normal_style))
        story.append(Paragraph(f"<b>Export Date:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", normal_style))
        story.append(Paragraph(f"<b>Data Retention Preference:</b> {user_info.get('data_retention_preference', 'Standard')}", normal_style))
        story.append(Spacer(1, 20))
        
        # Consent information
        story.append(Paragraph("Consent Status", section_title_style))
        consent_data = [
            ['Consent Type', 'Status'],
            ['General Consent', 'Given' if user_info.get('consent_given') else 'Not Given'],
            ['Marketing Consent', 'Given' if user_info.get('marketing_consent') else 'Not Given'],
            ['Analytics Consent', 'Given' if user_info.get('analytics_consent') else 'Not Given']
        ]
        consent_table = Table(consent_data, colWidths=[3*inch, 2*inch])
        consent_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 12),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        story.append(consent_table)
        story.append(Spacer(1, 20))
        
        # Data sections
        for section_key, section_data in export_data.items():
            if not section_data:
                continue
                
            section_title = section_key.replace('_', ' ').title()
            story.append(Paragraph(section_title, section_title_style))
            
            if section_key == 'profile' and isinstance(section_data, dict):
                # Profile data as key-value pairs
                for key, value in section_data.items():
                    if value:
                        story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {str(value)}", normal_style))
                        story.append(Spacer(1, 6))
                        
            elif isinstance(section_data, list) and section_data:
                # List data - limit to last 10 items for readability
                limited_data = section_data[-10:] if len(section_data) > 10 else section_data
                
                for i, item in enumerate(limited_data, 1):
                    story.append(Paragraph(f"<b>Item {i}:</b>", subsection_style))
                    
                    if isinstance(item, dict):
                        for key, value in item.items():
                            if value and key not in ['id', '_rid', '_self', '_etag', '_attachments', '_ts']:
                                story.append(Paragraph(f"• <b>{key.replace('_', ' ').title()}:</b> {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}", normal_style))
                    else:
                        story.append(Paragraph(f"• {str(item)[:200]}{'...' if len(str(item)) > 200 else ''}", normal_style))
                    
                    story.append(Spacer(1, 12))
                
                if len(section_data) > 10:
                    story.append(Paragraph(f"<i>... and {len(section_data) - 10} more items</i>", normal_style))
                    story.append(Spacer(1, 10))
            
            story.append(PageBreak())
        
        # Footer
        story.append(Paragraph("Data Export Complete", section_title_style))
        story.append(Paragraph(f"This export contains your personal health data from Diabetes Meal Plan Generator as of {datetime.now().strftime('%B %d, %Y')}. Please keep this document secure and confidential.", normal_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        filename = f"health_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        print(f"[PRIVACY] Error generating PDF: {str(e)}")
        # Fallback to JSON if PDF generation fails
        return JSONResponse(content={
            "message": "PDF export encountered an error, providing JSON format instead",
            "error": str(e),
            "data": export_data,
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "format": "json_fallback"
            }
        })

async def generate_data_export_docx(export_data: dict, user_info: dict):
    """Generate simplified DOCX export using HTML format"""
    try:
        # Limit data to last 10 items for consistency
        limited_export_data = {}
        for key, value in export_data.items():
            if isinstance(value, list) and len(value) > 10:
                limited_export_data[key] = value[-10:]  # Last 10 items
            else:
                limited_export_data[key] = value
        
        # Generate HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Health Data Export</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ text-align: center; color: #2E7D32; border-bottom: 2px solid #2E7D32; padding-bottom: 20px; }}
                .section {{ margin: 30px 0; }}
                .section-title {{ color: #1976D2; font-size: 18px; font-weight: bold; margin: 20px 0 10px 0; }}
                .item {{ margin: 15px 0; padding: 10px; background-color: #f5f5f5; }}
                .key {{ font-weight: bold; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #2E7D32; color: white; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Diabetes Meal Plan Generator</h1>
                <h2>Personal Health Data Export</h2>
                <p><strong>User:</strong> {user_info['email']}</p>
                <p><strong>Export Date:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
            
            <div class="section">
                <div class="section-title">Consent Status</div>
                <table>
                    <tr><th>Consent Type</th><th>Status</th></tr>
                    <tr><td>General Consent</td><td>{'Given' if user_info.get('consent_given') else 'Not Given'}</td></tr>
                    <tr><td>Marketing Consent</td><td>{'Given' if user_info.get('marketing_consent') else 'Not Given'}</td></tr>
                    <tr><td>Analytics Consent</td><td>{'Given' if user_info.get('analytics_consent') else 'Not Given'}</td></tr>
                </table>
            </div>
        """
        
        # Add data sections
        for section_key, section_data in limited_export_data.items():
            if not section_data:
                continue
                
            section_title = section_key.replace('_', ' ').title()
            html_content += f'<div class="section"><div class="section-title">{section_title}</div>'
            
            if section_key == 'profile' and isinstance(section_data, dict):
                html_content += '<div class="item">'
                for key, value in section_data.items():
                    if value:
                        html_content += f'<p><span class="key">{key.replace("_", " ").title()}:</span> {str(value)}</p>'
                html_content += '</div>'
                        
            elif isinstance(section_data, list) and section_data:
                for i, item in enumerate(section_data, 1):
                    html_content += f'<div class="item"><h4>Item {i}</h4>'
                    
                    if isinstance(item, dict):
                        for key, value in item.items():
                            if value and key not in ['id', '_rid', '_self', '_etag', '_attachments', '_ts']:
                                safe_value = str(value)[:200] + ('...' if len(str(value)) > 200 else '')
                                html_content += f'<p><span class="key">{key.replace("_", " ").title()}:</span> {safe_value}</p>'
                    else:
                        safe_item = str(item)[:300] + ('...' if len(str(item)) > 300 else '')
                        html_content += f'<p>{safe_item}</p>'
                    
                    html_content += '</div>'
            
            html_content += '</div>'
        
        html_content += """
            <div class="section">
                <div class="section-title">Export Information</div>
                <div class="item">
                    <p>This export contains your personal health data from Diabetes Meal Plan Generator. 
                    Please keep this document secure and confidential.</p>
                    <p><strong>Export Format:</strong> HTML/DOCX Compatible</p>
                    <p><strong>Data Privacy:</strong> This export is generated in compliance with GDPR requirements.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Convert to bytes for streaming response
        buffer = BytesIO()
        buffer.write(html_content.encode('utf-8'))
        buffer.seek(0)
        
        filename = f"health_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        return StreamingResponse(
            buffer,
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        print(f"[PRIVACY] Error generating DOCX: {str(e)}")
        # Fallback to JSON if DOCX generation fails
        return JSONResponse(content={
            "message": "DOCX export encountered an error, providing JSON format instead",
            "error": str(e),
            "data": limited_export_data,
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "format": "json_fallback"
            }
        })