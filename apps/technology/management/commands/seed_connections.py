"""
Seed Connections reference data.
Sample connections with their types, sizes, and KSA replacement status.
"""

from django.core.management.base import BaseCommand

from apps.technology.models import Connection, ConnectionType, ConnectionSize, UpperSectionType


class Command(BaseCommand):
    help = "Seed sample Connections reference data"

    def handle(self, *args, **options):
        # First ensure we have connection types and sizes
        api_reg = ConnectionType.objects.filter(code="API-REG").first()
        api_if = ConnectionType.objects.filter(code="API-IF").first()
        ht = ConnectionType.objects.filter(code="HT").first()

        size_4_half = ConnectionSize.objects.filter(code="4-1/2").first()
        size_6_5_8 = ConnectionSize.objects.filter(code="6-5/8").first()

        std_shank = UpperSectionType.objects.filter(code="STD").first()
        wos = UpperSectionType.objects.filter(code="WOS").first()
        shankless = UpperSectionType.objects.filter(code="SL").first()

        if not all([api_reg, size_4_half]):
            self.stdout.write(
                self.style.WARNING(
                    "Missing connection types or sizes. Run seed_connection_types and seed_connection_sizes first."
                )
            )
            return

        connections = [
            {
                "mat_no": "800100001",
                "connection_type": api_reg,
                "connection_size": size_4_half,
                "upper_section_type": std_shank,
                "special_features": "",
                "can_replace_in_ksa": True,
                "remarks": "Standard 4-1/2 API-REG connection",
            },
            {
                "mat_no": "800100002",
                "connection_type": api_if,
                "connection_size": size_4_half,
                "upper_section_type": std_shank,
                "special_features": "",
                "can_replace_in_ksa": True,
                "remarks": "Standard 4-1/2 API-IF connection",
            },
            {
                "mat_no": "800100003",
                "connection_type": api_reg,
                "connection_size": size_6_5_8,
                "upper_section_type": std_shank,
                "special_features": "Extended gauge",
                "can_replace_in_ksa": True,
                "remarks": "6-5/8 API-REG with extended gauge",
            },
        ]

        # Add WOS connection if we have the type
        if wos and size_4_half:
            connections.append({
                "mat_no": "800100010",
                "connection_type": api_reg,
                "connection_size": size_4_half,
                "upper_section_type": wos,
                "special_features": "Welded over slot design",
                "can_replace_in_ksa": False,
                "remarks": "Cannot be replaced in KSA - requires specialized welding",
            })

        # Add Shankless connection if we have the type
        if shankless and size_4_half and ht:
            connections.append({
                "mat_no": "800100011",
                "connection_type": ht,
                "connection_size": size_4_half,
                "upper_section_type": shankless,
                "special_features": "Integral shankless design",
                "can_replace_in_ksa": False,
                "remarks": "Shankless design - cannot separate upper section",
            })

        created = 0
        for conn_data in connections:
            if conn_data.get("connection_type") and conn_data.get("connection_size"):
                obj, was_created = Connection.objects.update_or_create(
                    mat_no=conn_data["mat_no"],
                    defaults={
                        "connection_type": conn_data["connection_type"],
                        "connection_size": conn_data["connection_size"],
                        "upper_section_type": conn_data.get("upper_section_type"),
                        "special_features": conn_data.get("special_features", ""),
                        "can_replace_in_ksa": conn_data.get("can_replace_in_ksa", True),
                        "remarks": conn_data.get("remarks", ""),
                        "is_active": True,
                    },
                )
                if was_created:
                    created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Connection: {created} created, {len(connections) - created} already exist")
        )
