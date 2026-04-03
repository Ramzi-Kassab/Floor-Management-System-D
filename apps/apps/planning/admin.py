from django.contrib import admin

from .models import (
    PlanningBoard,
    PlanningColumn,
    PlanningItem,
    PlanningLabel,
    Sprint,
    WikiPage,
    WikiPageVersion,
    WikiSpace,
)


@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "status", "start_date", "end_date", "progress_percent"]
    list_filter = ["status"]


class PlanningColumnInline(admin.TabularInline):
    model = PlanningColumn
    extra = 0


@admin.register(PlanningBoard)
class PlanningBoardAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "sprint", "is_active"]
    list_filter = ["is_active"]
    inlines = [PlanningColumnInline]


@admin.register(PlanningLabel)
class PlanningLabelAdmin(admin.ModelAdmin):
    list_display = ["name", "color"]


@admin.register(PlanningItem)
class PlanningItemAdmin(admin.ModelAdmin):
    list_display = ["code", "title", "item_type", "priority", "assignee", "sprint"]
    list_filter = ["item_type", "priority", "sprint"]
    search_fields = ["code", "title"]


@admin.register(WikiSpace)
class WikiSpaceAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_public", "owner"]


@admin.register(WikiPage)
class WikiPageAdmin(admin.ModelAdmin):
    list_display = ["title", "space", "parent", "is_published"]
    list_filter = ["space", "is_published"]
