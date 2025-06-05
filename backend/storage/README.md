# Storage Directory

This directory contains user-generated files that are stored on the server.

## Directory Structure

- `pdfs/` - Consolidated PDF files generated from meal plans
  - Contains user-specific PDF files with format: `{username}_{timestamp}_consolidated_meal_plan.pdf`
  - PDFs are automatically generated when users save their complete meal plans
  - PDFs can be downloaded from the meal plan history page

## Security Notes

- PDF files are named with the user's email prefix to ensure access control
- The backend verifies file ownership before allowing downloads
- Files are served securely through the authenticated `/download-saved-pdf/` endpoint

## Maintenance

- Consider implementing automatic cleanup of old PDF files
- Monitor disk space usage as PDFs can accumulate over time
- Backup important meal plan PDFs if needed for compliance or user requests 