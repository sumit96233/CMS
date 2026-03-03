#!/usr/bin/env python
"""
Run this ONCE to set up the database and create the admin user.
Usage:  python setup.py
"""
import os, sys, subprocess

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'compms.settings')

def run(cmd):
    print(f"\n>>> {cmd}")
    subprocess.run(cmd, shell=True, check=True)

print("=" * 55)
print("  CompMS — First-time setup")
print("=" * 55)

run("pip install -r requirements.txt")
run("python manage.py makemigrations events")
run("python manage.py migrate")

print("\n" + "=" * 55)
print("  Creating admin user")
print("=" * 55)

import django
django.setup()
from django.contrib.auth.models import User

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username  = 'admin',
        password  = 'admin123',
        email     = 'admin@compms.com',
        first_name= 'Admin',
        last_name = 'User',
    )
    print("  Admin created  →  username: admin  |  password: admin123")
else:
    print("  Admin already exists.")

print("\n" + "=" * 55)
print("  Setup complete!")
print("  Run:  python manage.py runserver")
print("  Open: http://127.0.0.1:8000")
print("  Admin login: admin / admin123")
print("=" * 55)
