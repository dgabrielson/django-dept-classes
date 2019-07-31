"""
The DEFAULT configuration is loaded when the CONFIG_NAME dictionary
is not present in your settings.

All valid application settings must have a default value.
"""
#######################
from __future__ import print_function, unicode_literals

from django.conf import settings
from django.core.files.storage import default_storage

#######################

CONFIG_NAME = "AURORA_CONFIG"  # must be uppercase!

DEFAULT = {
    # When synchronizing, should unmatched instructors be created?
    "create_instructors": True,
    # When synchronizing, should unmatched classrooms be created?
    "create_classrooms": True,
    # When synchronizing, should unmatched timeslots be created?
    "create_timeslots": True,
    # When any new objects are automatically created, should a warning
    # message be included in the report?
    "notify_on_create": True,
    # When synchronizing, on delete do NOT delete these section types
    # (challenge for credit by default)
    "delete:ignore_section_types": ["cc"],
    # The root uri of your banner system. (Drop https:// to http://)
    "banner:root_uri": "https://aurora.umanitoba.ca",
    # Presumably, the following urls are for any banner system.
    # They are included in case of version changes or other local differences.
    "banner:course_list_url": "/banprod/bwckschd.p_get_crse_unsec",
    "banner:catalog_entry_url": "/banprod/bwckctlg.p_display_courses",
    "banner:schedule_detail_url": "/banprod/bwckschd.p_disp_detail_sched",
    "banner:department_list_url": "/banprod/bwckctlg.p_disp_cat_term_date",
    # Should records with no campus information be accepted, or rejected?
    "banner:accept_no_campus": True,
}


def get(setting):
    """
    get(setting) -> value

    setting should be a string representing the application settings to
    retrieve.
    """
    if setting not in DEFAULT:
        raise ValueError(
            "The setting key {0!r} is not valid in {1}".format(setting, CONFIG_NAME)
        )
    app_settings = getattr(settings, CONFIG_NAME, DEFAULT)
    return app_settings.get(setting, DEFAULT[setting])


def get_all():
    """
    Return all current settings as a dictionary.
    """
    app_settings = getattr(settings, CONFIG_NAME, DEFAULT)
    return dict(
        [(setting, app_settings.get(setting, DEFAULT[setting])) for setting in DEFAULT]
    )
