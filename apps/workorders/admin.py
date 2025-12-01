from django.contrib import admin
from .models import (
    DrillBit, WorkOrder, WorkOrderDocument, WorkOrderPhoto,
    WorkOrderMaterial, WorkOrderTimeLog, BitEvaluation
)

@admin.register(DrillBit)
class DrillBitAdmin(admin.ModelAdmin):
    list_display = ['serial_number', 'bit_type', 'design', 'status', 'current_location']
    list_filter = ['bit_type', 'status', 'customer']
    search_fields = ['serial_number', 'qr_code']

class WorkOrderMaterialInline(admin.TabularInline):
    model = WorkOrderMaterial
    extra = 0

class WorkOrderDocumentInline(admin.TabularInline):
    model = WorkOrderDocument
    extra = 0

class WorkOrderPhotoInline(admin.TabularInline):
    model = WorkOrderPhoto
    extra = 0

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ['wo_number', 'wo_type', 'status', 'priority', 'customer', 'due_date']
    list_filter = ['status', 'wo_type', 'priority', 'customer']
    search_fields = ['wo_number', 'customer__name']
    inlines = [WorkOrderMaterialInline, WorkOrderDocumentInline, WorkOrderPhotoInline]

@admin.register(WorkOrderTimeLog)
class WorkOrderTimeLogAdmin(admin.ModelAdmin):
    list_display = ['work_order', 'user', 'start_time', 'duration_minutes', 'activity_type']
    list_filter = ['activity_type']

@admin.register(BitEvaluation)
class BitEvaluationAdmin(admin.ModelAdmin):
    list_display = ['drill_bit', 'evaluation_date', 'overall_condition', 'recommendation']
    list_filter = ['overall_condition', 'recommendation']
