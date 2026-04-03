"""
Seed drilling applications reference data.
"""
from django.core.management.base import BaseCommand
from apps.technology.models import Application


class Command(BaseCommand):
    help = 'Seed drilling applications reference data'

    def handle(self, *args, **options):
        data = [
            ('VERT', 'Vertical', 'Standard vertical drilling'),
            ('DIR', 'Directional', 'Directional drilling with mud motor'),
            ('HORZ', 'Horizontal', 'Horizontal section drilling'),
            ('ERD', 'Extended Reach', 'Extended reach drilling'),
            ('RSS', 'Rotary Steerable', 'Rotary steerable system drilling'),
            ('MOTOR', 'Motor Drilling', 'Positive displacement motor drilling'),
            ('TURB', 'Turbine', 'Turbine drilling'),
            ('SLIDE', 'Slide Drilling', 'Sliding mode with bent motor'),
            ('ROTATE', 'Rotary', 'Standard rotary drilling'),
            ('CURVE', 'Curve/Build', 'Build section in directional well'),
            ('LATERAL', 'Lateral', 'Lateral section in horizontal well'),
            ('KICKOFF', 'Kickoff', 'Kickoff from vertical to directional'),
            ('TANGENT', 'Tangent', 'Tangent section hold angle'),
            ('TOPHOLE', 'Top Hole', 'Surface/top hole section'),
            ('INTERMED', 'Intermediate', 'Intermediate hole section'),
            ('PRODHOLE', 'Production Hole', 'Production section drilling'),
            ('REAM', 'Reaming', 'Hole opening/reaming operation'),
            ('SIDETRACK', 'Sidetrack', 'Sidetrack/whipstock operation'),
        ]

        created = 0
        for code, name, desc in data:
            obj, was_created = Application.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': desc}
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f'Application: {created} created, {len(data) - created} already exist'))
