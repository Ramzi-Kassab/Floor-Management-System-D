"""
Management command to update BitType records with real ARDT data.

Run: python manage.py update_bit_types
"""

from django.core.management.base import BaseCommand

from apps.technology.models import BitSize, BitType


class Command(BaseCommand):
    help = "Update BitType records with real data from ARDT"

    def handle(self, *args, **options):
        # Real data from ARDT spreadsheet
        # Format: (category, size_decimal, smi_name, hdbs_name, series, hdbs_mn, ref_hdbs_mn, body_material, blades, cutter, gage, level)
        bit_types_data = [
            # Fixed Cutter (FC) Types
            ("FC", 3.625, "MMD53DH", "MMD53DH", "MM", "2016920", "2013733", "M", 5, 3, 2.0, "4"),
            ("FC", 3.625, "MMD53DH-2", "MMD53DH", "MM", "2025595", "1228690", "M", 5, 3, 1.5, "4"),
            ("FC", 5.875, "EM65D", "EM65D", "EM", "2017993", "1235768", "M", 6, 5, 1.5, "4"),
            ("FC", 5.875, "EM65DX", "", "EM", "2021067", "", "M", 6, 5, None, "4"),
            ("FC", 6.125, "GTD54H", "GTD54H", "GT", "1145824", "1137349", "M", 5, 4, 1.5, "4"),
            ("FC", 6.125, "GT64KHO", "GT64KHO", "GT", "1198387", "1160951", "M", 6, 4, 1.5, "4"),
            ("FC", 6.125, "GTi54H", "GTi54H", "GT", "1160951", "1137349", "M", 5, 4, 1.5, "4"),
            ("FC", 6.125, "HD54", "HD54", "HD", "1137349", "", "M", 5, 4, 1.5, "3"),
            ("FC", 6.125, "HD54F", "HD54F", "HD", "1228690", "1137349", "M", 5, 4, 1.5, "4"),
            ("FC", 8.375, "GT65DH-1", "GT65DH", "GT", "1246020", "1141517", "M", 6, 5, 2.0, "4"),
            ("FC", 8.375, "EM75D", "EM75D", "EM", "1272920", "1141517", "M", 7, 5, 2.0, "4"),
            ("FC", 8.5, "GT65RHs", "GT65RHs", "GT", "1269498", "1141517", "S", 6, 5, 3.5, "4"),
            ("FC", 8.5, "GT65RHs-1", "GT65RHs-1", "GT", "2022318", "1269498", "S", 6, 5, 3.5, "4"),
            ("FC", 8.5, "HD65", "HD65", "HD", "1141517", "", "M", 6, 5, 2.0, "3"),
            ("FC", 8.5, "HD65Os", "HD65Os", "HD", "1270865", "1218014", "S", 6, 5, 2.5, "4"),
            ("FC", 8.5, "MM64", "MM64", "MM", "1148253", "1141517", "M", 6, 4, 2.0, "4"),
            ("FC", 8.5, "MMD65H", "MMD65H", "MM", "1235768", "1141517", "M", 6, 5, 2.0, "4"),
            ("FC", 12.25, "HD76DF", "HD76DF", "HD", "1266749", "1218014", "M", 7, 6, 3.0, "4"),
            ("FC", 12.25, "GT76H", "GT76H", "GT", "1186452", "1218014", "M", 7, 6, 3.0, "4"),
            ("FC", 16.0, "HD76DF-16", "HD76DF", "HD", "2019988", "1266749", "M", 7, 6, 4.0, "4"),
            ("FC", 17.5, "HD86DF", "HD86DF", "HD", "1289012", "1266749", "M", 8, 6, 4.5, "4"),
            # Tri Cone Inserts (TCI) Types
            ("TCI", 28.0, "EBXT12S", "435W", "", "2023982", "739244", "", None, None, None, ""),
            ("TCI", 17.5, "GX14S", "337W", "", "1198456", "", "", None, None, None, ""),
            ("TCI", 12.25, "GX12S", "317W", "", "1145678", "", "", None, None, None, ""),
            # Mill Tooth (MT) Types
            ("MT", 5.875, "Q4R", "217M", "", "720942", "497455", "", None, None, None, ""),
            ("MT", 6.125, "QH1R", "117W", "", "537077", "", "", None, None, None, ""),
            ("MT", 8.5, "AB1GRC", "217", "", "2027933", "", "", None, None, None, ""),
            ("MT", 12.25, "AB3GRC", "317", "", "1234567", "", "", None, None, None, ""),
        ]

        created = 0
        updated = 0
        errors = []

        for data in bit_types_data:
            try:
                (
                    cat,
                    size_dec,
                    smi,
                    hdbs,
                    series,
                    mn,
                    ref_mn,
                    body,
                    blades,
                    cutter,
                    gage,
                    level,
                ) = data

                # Get BitSize if it exists
                size = None
                if size_dec:
                    size = BitSize.objects.filter(size_decimal=size_dec).first()
                    if not size:
                        # Try to find by approximate match
                        size = BitSize.objects.filter(
                            size_decimal__gte=size_dec - 0.1, size_decimal__lte=size_dec + 0.1
                        ).first()

                # Build defaults dict
                defaults = {
                    "category": cat,
                    "size": size,
                    "smi_name": smi,
                    "hdbs_name": hdbs or smi,  # Use smi_name if hdbs_name is empty
                    "series": series,
                    "ref_hdbs_mn": ref_mn,
                    "body_material": body,
                    "no_of_blades": blades,
                    "cutter_size": cutter,
                    "gage_length": gage,
                    "order_level": level,
                    "is_active": True,
                    "code": smi,  # Also set legacy code field
                }

                # Update or create BitType using hdbs_mn as unique identifier
                if mn:
                    bit_type, was_created = BitType.objects.update_or_create(
                        hdbs_mn=mn, defaults=defaults
                    )
                else:
                    # If no MAT number, use smi_name as lookup
                    bit_type, was_created = BitType.objects.update_or_create(
                        smi_name=smi, defaults={**defaults, "hdbs_mn": ""}
                    )

                if was_created:
                    created += 1
                    self.stdout.write(f"  + Created: {smi} ({mn})")
                else:
                    updated += 1
                    self.stdout.write(f"  ~ Updated: {smi} ({mn})")

            except Exception as e:
                errors.append(f"{smi}: {e!s}")
                self.stdout.write(self.style.ERROR(f"  ✗ Error: {smi} - {e}"))

        # Summary
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(f"✅ BitTypes: {created} created, {updated} updated")
        )
        if errors:
            self.stdout.write(self.style.WARNING(f"⚠️  Errors: {len(errors)}"))
            for err in errors:
                self.stdout.write(self.style.WARNING(f"   - {err}"))
