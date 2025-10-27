"""
Birthday Notification Management Command

INSTRUCTIONS FOR SCHEDULING ON LOCALHOST (WINDOWS):

1. TIME OF EXECUTION:
   - Ideal execution time: Daily at 01:00 AM

2. HOW TO SCHEDULE USING WINDOWS TASK SCHEDULER:
   a. Open Task Scheduler (taskschd.msc)
   b. Create a "Basic Task" with the following settings:
      - Name: "ProyekBarokah Birthday Notifications"
      - Description: "Send birthday notifications to customers"
   
   c. Set the trigger:
      - Daily
      - Start time: 01:00:00 AM
      
   d. Set the action:
      - Action: Start a program
      - Program/script: C:\\full\\path\\to\\your\\venv\\Scripts\\python.exe
      - Add arguments: "C:\\full\\path\\to\\your\\project\\manage.py" check_birthdays
      - Start in: C:\\full\\path\\to\\your\\project\\
      
   e. Important Notes:
      - ALWAYS use the full path to python.exe in your virtual environment
      - Example path: C:\\Users\\YourName\\myenv\\Scripts\\python.exe
      - Make sure the working directory is set to your project root

PYTHONANYWHERE SCHEDULING:
For PythonAnywhere deployment, use the schedule_birthdays_pa.py wrapper script
which should be placed in the project root directory.
"""

from django.core.management.base import BaseCommand
from admin_dashboard.signals import check_birthday_notifications


class Command(BaseCommand):
    help = 'Check for customers with birthdays today and send automatic notifications'

    def handle(self, *args, **options):
        self.stdout.write(
            'Starting birthday notification check...'
        )
        
        # Call the existing function from signals.py
        try:
            check_birthday_notifications()
            self.stdout.write(
                'Successfully completed birthday notification check'
            )
        except Exception as e:
            self.stdout.write(
                f'Error during birthday notification check: {e}'
            )