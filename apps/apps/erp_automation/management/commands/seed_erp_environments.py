"""
Seed default ERP environment URLs.

Usage:
    python manage.py seed_erp_environments
"""
from django.core.management.base import BaseCommand
from apps.erp_automation.models import ERPEnvironment


DEFAULT_ENVIRONMENTS = [
    {
        "name": "Sandbox",
        "url": "https://sandbox.alrushaid.net/namespaces/AXSF/",
        "is_default": True,
        "sort_order": 1,
    },
    {
        "name": "Production",
        "url": "https://prod.alrushaid.net/namespaces/AXSF/",
        "is_default": False,
        "sort_order": 2,
    },
]


class Command(BaseCommand):
    help = "Seed default ERP environment URLs (Sandbox + Production)"

    def handle(self, *args, **options):
        created_count = 0
        for env_data in DEFAULT_ENVIRONMENTS:
            obj, created = ERPEnvironment.objects.get_or_create(
                name=env_data["name"],
                defaults={
                    "url": env_data["url"],
                    "is_default": env_data["is_default"],
                    "sort_order": env_data["sort_order"],
                },
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f"  [+] Created: {obj.name} -> {obj.url}"
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"  [=] Already exists: {obj.name} -> {obj.url}"
                ))

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {created_count} new environment(s) created, "
            f"{len(DEFAULT_ENVIRONMENTS) - created_count} already existed."
        ))
