#!/bin/bash

# Safe migration reset - preserves virtual environment and data

echo "Starting safe migration reset..."

# 1. Delete only migration files (not __init__.py)
echo "Cleaning migration files..."
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# 2. Delete the database
echo "Removing database..."
rm -f db.sqlite3

pip uninstall django
pip install -r requirements.txt

# 3. Create fresh migrations from your models
echo "Creating new migrations..."
python manage.py makemigrations

# 4. Apply migrations to new database
# echo "Applying migrations..."
# python manage.py migrate

# 5. Create a superuser (optional)
echo "Migration reset complete!"
echo "You may now create a superuser with: python manage.py createsuperuser"