# Diabetes Diet Planner

A full-stack application for generating personalized meal plans, recipes, and shopping lists for diabetes management. Built with **FastAPI** (backend) and **React** (frontend).

## Features
- User registration and authentication
- Profile creation with dietary preferences and health conditions
- AI-powered meal plan and recipe generation
- Shopping list generation
- PDF export of meal plan, recipes, shopping list, and a consolidated PDF with a custom cover page
- Admin panel for patient management

## Project Structure
```
.
├── backend/                # FastAPI backend
├── frontend/               # React frontend
├── assets/                 # Static assets (e.g., coverpage.png)
├── .env                    # Environment variables (not tracked)
├── .gitignore
├── README.md
```

## Setup

### 1. Clone the repository
```sh
git clone <your-repo-url>
cd diabetes_diet_planner
```

### 2. Backend Setup (FastAPI)
- Create and activate a Python virtual environment:
  ```sh
  python3 -m venv ddp_env
  source ddp_env/bin/activate
  ```
- Install dependencies:
  ```sh
  pip install -r backend/requirements.txt
  ```
- Copy `.env.example` to `.env` and set your environment variables (OpenAI, Twilio, DB, etc).
- Make sure `assets/coverpage.png` exists for PDF export.
- Run the backend:
  ```sh
  cd backend
  uvicorn main:app --reload
  ```

### 3. Frontend Setup (React)
- Install dependencies:
  ```sh
  cd ../frontend
  npm install
  ```
- Run the frontend:
  ```sh
  npm start
  ```

## Environment Variables
- Backend expects a `.env` file with keys for OpenAI, Twilio, database, and secret keys.
- See `.env.example` for details.

## PDF Export
- The consolidated PDF export includes a custom cover page (`assets/coverpage.png`), meal plan, recipes, and shopping list, each on separate pages.
- Download options are available in the frontend after generating your plan.

## Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](LICENSE) 