"""
ARDT FMS - HSSE Models
Version: 5.4

🔴 P4 - Advanced/Political

Tables:
- hoc_reports (P4) - Hazard Observation Cards
- incidents (P4)
- journeys (P4) - Journey Management
"""

from django.conf import settings
from django.db import models


class HOCReport(models.Model):
    """🔴 P4: Hazard Observation Cards."""

    class Category(models.TextChoices):
        UNSAFE_ACT = "UNSAFE_ACT", "Unsafe Act"
        UNSAFE_CONDITION = "UNSAFE_CONDITION", "Unsafe Condition"
        NEAR_MISS = "NEAR_MISS", "Near Miss"
        POSITIVE = "POSITIVE", "Positive Observation"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        CLOSED = "CLOSED", "Closed"

    hoc_number = models.CharField(max_length=30, unique=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    location = models.CharField(max_length=200)
    description = models.TextField()
    immediate_action = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    reported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "hoc_reports"
        ordering = ["-reported_at"]
        verbose_name = "HOC Report"
        verbose_name_plural = "HOC Reports"
        indexes = [
            models.Index(fields=["status", "reported_by"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return f"{self.hoc_number} - {self.get_category_display()}"


class Incident(models.Model):
    """🔴 P4: Safety incidents."""

    class Severity(models.TextChoices):
        MINOR = "MINOR", "Minor"
        MODERATE = "MODERATE", "Moderate"
        MAJOR = "MAJOR", "Major"
        CRITICAL = "CRITICAL", "Critical"

    class IncidentType(models.TextChoices):
        INJURY = "INJURY", "Injury"
        ILLNESS = "ILLNESS", "Illness"
        PROPERTY_DAMAGE = "PROPERTY_DAMAGE", "Property Damage"
        ENVIRONMENTAL = "ENVIRONMENTAL", "Environmental"
        FIRE = "FIRE", "Fire"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        REPORTED = "REPORTED", "Reported"
        INVESTIGATING = "INVESTIGATING", "Under Investigation"
        CLOSED = "CLOSED", "Closed"

    incident_number = models.CharField(max_length=30, unique=True)
    incident_type = models.CharField(max_length=20, choices=IncidentType.choices)
    severity = models.CharField(max_length=20, choices=Severity.choices)

    occurred_at = models.DateTimeField()
    location = models.CharField(max_length=200)
    description = models.TextField()
    immediate_action = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REPORTED)

    investigation_findings = models.TextField(blank=True)
    root_cause = models.TextField(blank=True)
    corrective_actions = models.TextField(blank=True)

    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "incidents"
        ordering = ["-occurred_at"]
        verbose_name = "Incident"
        verbose_name_plural = "Incidents"
        indexes = [
            models.Index(fields=["status", "reported_by"]),
            models.Index(fields=["severity"]),
            models.Index(fields=["occurred_at"]),
        ]

    def __str__(self):
        return f"{self.incident_number} - {self.get_severity_display()}"


class Journey(models.Model):
    """🔴 P4: Journey Management."""

    class Status(models.TextChoices):
        PLANNED = "PLANNED", "Planned"
        APPROVED = "APPROVED", "Approved"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    journey_number = models.CharField(max_length=30, unique=True)
    purpose = models.CharField(max_length=200)

    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="journeys_as_driver"
    )
    vehicle = models.ForeignKey("dispatch.Vehicle", on_delete=models.SET_NULL, null=True, blank=True)

    departure_location = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    planned_departure = models.DateTimeField()
    planned_arrival = models.DateTimeField()

    actual_departure = models.DateTimeField(null=True, blank=True)
    actual_arrival = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_journeys"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "journeys"
        ordering = ["-planned_departure"]
        verbose_name = "Journey"
        verbose_name_plural = "Journeys"

    def __str__(self):
        driver_name = self.driver.get_full_name() if self.driver else "Unknown"
        return f"{self.journey_number} - {driver_name}"
