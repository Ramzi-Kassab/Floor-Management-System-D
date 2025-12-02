"""
ARDT FMS - HR Models
Version: 5.4

🔴 P4 - Advanced/Political

Tables:
- attendance (P4)
- attendance_punches (P4)
- leave_types (P4)
- leave_requests (P4)
- overtime_requests (P4)
"""

from django.db import models
from django.conf import settings


class Attendance(models.Model):
    """🔴 P4: Daily attendance records."""
    
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', 'Present'
        ABSENT = 'ABSENT', 'Absent'
        LEAVE = 'LEAVE', 'On Leave'
        HOLIDAY = 'HOLIDAY', 'Holiday'
        HALF_DAY = 'HALF_DAY', 'Half Day'
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PRESENT)
    
    first_in = models.TimeField(null=True, blank=True)
    last_out = models.TimeField(null=True, blank=True)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'attendance'
        unique_together = ['user', 'date']
        ordering = ['-date', 'user']
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendance Records'

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class AttendancePunch(models.Model):
    """🔴 P4: Individual clock in/out punches."""
    
    class PunchType(models.TextChoices):
        IN = 'IN', 'Clock In'
        OUT = 'OUT', 'Clock Out'
    
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='punches')
    punch_type = models.CharField(max_length=10, choices=PunchType.choices)
    punch_time = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    
    class Meta:
        db_table = 'attendance_punches'
        ordering = ['attendance', 'punch_time']

    def __str__(self):
        return f"{self.attendance.user.username} - {self.get_punch_type_display()} at {self.punch_time}"


class LeaveType(models.Model):
    """🔴 P4: Types of leave."""
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    days_per_year = models.IntegerField(default=0)
    is_paid = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'leave_types'
        ordering = ['name']
        verbose_name = 'Leave Type'
        verbose_name_plural = 'Leave Types'

    def __str__(self):
        return self.name


class LeaveRequest(models.Model):
    """🔴 P4: Leave requests."""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    days = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'leave_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.leave_type.name} ({self.start_date} to {self.end_date})"


class OvertimeRequest(models.Model):
    """🔴 P4: Overtime requests."""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='overtime_requests')
    date = models.DateField()
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_overtime'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'overtime_requests'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.date} ({self.hours}h)"
