#!/usr/bin/env python3
"""
Wrapper Script for PythonAnywhere Scheduled Tasks

This script serves as a wrapper to execute the Django management command
'check_birthdays' in the PythonAnywhere environment.

Instructions for PythonAnywhere:
1. Upload this script to your project root directory
2. In the PythonAnywhere Web Dashboard:
   - Go to the "Scheduled Tasks" tab
   - Add a new task with the following settings:
     - Time: 01:00 (or your preferred time)
     - Command: /home/yourusername/path/to/your/project/schedule_birthdays_pa.py

The script will:
- Set up the Django environment
- Import and execute the check_birthdays management command
- Print execution timestamps for logging purposes
"""

import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line
import datetime

# Print start time for logging
print(f"[{datetime.datetime.now()}] Starting birthday notification check...")

# Add your project directory to the Python path
# Adjust this path to match your PythonAnywhere project location
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ProyekBarokah.settings')

# Setup Django
try:
    django.setup()
    
    # Import the management command
    from admin_dashboard.management.commands.check_birthdays import Command
    
    # Create and execute the command
    command = Command()
    command.handle()
    
    # Print completion time for logging
    print(f"[{datetime.datetime.now()}] Birthday notification check completed successfully.")
    
except Exception as e:
    # Print error time and message for logging
    print(f"[{datetime.datetime.now()}] Error during birthday notification check: {e}")
    sys.exit(1)