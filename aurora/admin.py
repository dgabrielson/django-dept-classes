#######################
from __future__ import print_function, unicode_literals

from aurora.models import (
    AuroraCampus,
    AuroraDateRange,
    AuroraDepartment,
    AuroraInstructor,
    AuroraLocation,
    AuroraTimeslot,
)

#######################
from django.contrib import admin

###############################################################


class AuroraInstructorAdmin(admin.ModelAdmin):
    list_display = ["instructor", "person"]
    search_fields = ["instructor"]


admin.site.register(AuroraInstructor, AuroraInstructorAdmin)

###############################################################


class AuroraLocationAdmin(admin.ModelAdmin):
    list_display = ["location", "classroom"]
    search_fields = ["location"]


admin.site.register(AuroraLocation, AuroraLocationAdmin)

###############################################################


class AuroraTimeslotAdmin(admin.ModelAdmin):
    list_display = ["schedule_days", "schedule_time", "timeslot"]
    search_fields = ["schedule_days", "schedule_time"]


admin.site.register(AuroraTimeslot, AuroraTimeslotAdmin)

###############################################################


class AuroraDateRangeAdmin(admin.ModelAdmin):
    list_display = ["schedule_date_range", "date_range"]
    search_fields = ["schedule_date_range"]


admin.site.register(AuroraDateRange, AuroraDateRangeAdmin)

###############################################################


class AuroraCampusAdmin(admin.ModelAdmin):
    list_display = ["name", "online", "blacklisted"]
    search_fields = ["name"]


admin.site.register(AuroraCampus, AuroraCampusAdmin)

###############################################################


def set_sync(modeladmin, request, queryset):
    """
    Synchronize selected items to automatically 
    """
    queryset.update(synchronize=True)


set_sync.short_description = set_sync.__doc__.strip()

##############################################################


def clear_sync(modeladmin, request, queryset):
    """
    Do not synchronize selected items
    """
    queryset.update(synchronize=False)


clear_sync.short_description = clear_sync.__doc__.strip()

##############################################################


class AuroraDepartmentAdmin(admin.ModelAdmin):
    actions = [set_sync, clear_sync]
    list_display = ["department_code", "synchronize"]
    search_fields = ["department_code"]
    ordering = ["department_code"]


admin.site.register(AuroraDepartment, AuroraDepartmentAdmin)

###############################################################
