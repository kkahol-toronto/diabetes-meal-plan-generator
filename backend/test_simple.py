#!/usr/bin/env python3
"""
Simple test file to check basic imports without FastAPI
"""

print("Testing basic imports...")

try:
    import os
    print("✓ os import successful")
except ImportError as e:
    print(f"✗ os import failed: {e}")

try:
    import json
    print("✓ json import successful")
except ImportError as e:
    print(f"✗ json import failed: {e}")

try:
    from dotenv import load_dotenv
    print("✓ dotenv import successful")
except ImportError as e:
    print(f"✗ dotenv import failed: {e}")

try:
    from database import create_user, get_user_by_email
    print("✓ database imports successful")
except ImportError as e:
    print(f"✗ database imports failed: {e}")

try:
    from passlib.context import CryptContext
    print("✓ passlib import successful")
except ImportError as e:
    print(f"✗ passlib import failed: {e}")

try:
    from jose import jwt
    print("✓ jose import successful")
except ImportError as e:
    print(f"✗ jose import failed: {e}")

try:
    from openai import AzureOpenAI
    print("✓ openai import successful")
except ImportError as e:
    print(f"✗ openai import failed: {e}")

try:
    from twilio.rest import Client
    print("✓ twilio import successful")
except ImportError as e:
    print(f"✗ twilio import failed: {e}")

try:
    from docx import Document
    print("✓ docx import successful")
except ImportError as e:
    print(f"✗ docx import failed: {e}")

print("\nAll basic imports tested. Testing FastAPI separately...")

try:
    import pydantic
    print("✓ pydantic import successful")
except ImportError as e:
    print(f"✗ pydantic import failed: {e}")

try:
    import fastapi
    print("✓ fastapi import successful")
except ImportError as e:
    print(f"✗ fastapi import failed: {e}")

print("Test complete!") 