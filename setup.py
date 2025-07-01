from setuptools import setup, find_packages

setup(
    name="diabetes-meal-plan-generator",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "jinja2",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "python-multipart",
        "aiofiles",
        "starlette",
    ],
) 