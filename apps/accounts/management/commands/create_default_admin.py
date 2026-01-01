"""
Creates a default admin user for development.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates default admin user (admin/ra@mzi@123) for development'

    def handle(self, *args, **options):
        if User.objects.filter(username='admin').exists():
            self.stdout.write(self.style.WARNING('Admin user already exists'))
            return

        User.objects.create_superuser(
            username='admin',
            email='ramzikassab1982@gmail.com',
            password='ra@mzi@123',
            first_name='Ramzi',
            last_name='Kassab'
        )
        self.stdout.write(self.style.SUCCESS('✅ Created admin user: admin / ra@mzi@123'))
