from django.core.management.base import BaseCommand
from admin_dashboard.signals import check_birthday_notifications


class Command(BaseCommand):
    help = 'Check for customers with birthdays today and send automatic notifications'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting birthday notification check...')
        )
        
        # Call the existing function from signals.py
        try:
            check_birthday_notifications()
            self.stdout.write(
                self.style.SUCCESS('Successfully completed birthday notification check')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during birthday notification check: {e}')
            )