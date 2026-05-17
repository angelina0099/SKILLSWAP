# SKILLSWAP

SkillSwap is a Django-based skill exchange marketplace built with accounts, messaging, reviews, and skill request workflows.

## Repository layout

- `SKILLSWAP/` - main Django project directory
- `SKILLSWAP/accounts/`, `SKILLSWAP/messaging/`, `SKILLSWAP/reviews/`, `SKILLSWAP/skills/` - app modules
- `SKILLSWAP/templates/` - site templates

## Getting started

1. Create a Python virtual environment:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Run migrations:

   ```powershell
   python manage.py migrate
   ```

4. Start the development server:

   ```powershell
   python manage.py runserver
   ```

## Notes

- This repository ignores local SQLite databases, environment files, bytecode, and virtual environments.
- Do not commit `db.sqlite3`, `venv/`, or any generated Python cache files.
