"""
Creates a default admin user for development.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates default admin user (admin/admin123) for development'

    def handle(self, *args, **options):
        if User.objects.filter(username='admin').exists():
            self.stdout.write(self.style.WARNING('Admin user already exists'))
            return

        User.objects.create_superuser(
            username='admin',
            email='admin@ardt.local',
            password='admin123',
            first_name='Admin',
            last_name='User'
        )
        self.stdout.write(self.style.SUCCESS('✅ Created admin user: admin / admin123'))
