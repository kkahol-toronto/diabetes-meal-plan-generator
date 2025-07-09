#!/usr/bin/env python3
"""
Simple startup script for Azure App Service
"""
import os

def main():
    port = os.environ.get('PORT', '8000')
    # Use gunicorn for production deployment (more stable)
    os.system(f"gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:{port}")

if __name__ == '__main__':
    main() 