from django.contrib import admin

from .models import DRSSRequest, DRSSRequestLine


class DRSSRequestLineInline(admin.TabularInline):
    model = DRSSRequestLine
    extra = 0


@admin.register(DRSSRequest)
class DRSSRequestAdmin(admin.ModelAdmin):
    list_display = ["drss_number", "customer", "status", "priority", "required_date"]
    list_filter = ["status", "priority", "customer"]
    search_fields = ["drss_number", "external_reference"]
    inlines = [DRSSRequestLineInline]


@admin.register(DRSSRequestLine)
class DRSSRequestLineAdmin(admin.ModelAdmin):
    list_display = ["drss_request", "line_number", "bit_type", "bit_size", "status", "fulfillment_option"]
    list_filter = ["status", "fulfillment_option", "bit_type"]
