"""
The DEFAULT configuration is loaded when the CONFIG_NAME dictionary
is not present in your settings.

All valid application settings must have a default value.
"""
from __future__ import print_function, unicode_literals

from django.conf import settings
from django.core.files.storage import default_storage

##############################################################

CONFIG_NAME = "CLASSES_CONFIG"  # must be uppercase!

##############################################################
##############################################################


def determine_section_type(section):
    """
    Default implementation for determining the section type.
    If you don't want the section type to change,  return None.
    At the University of Manitoba, the first letter of the section
    name designates it's type:
    Section Number
        Axx - Primary Meet
        Bxx - Secondary meet (lab/tut)
        Dxx - Distance & Online Education
        Exx - Extended Education
        Gxx - Special Fees
        Kxx - Field Trip/Field Work
        Nxx - W. Norrie Centre only
        Txx - Topics Courses
        Rxx - ??? [historical]
        Xxx - ??? [historical]

UNIT,Section No,Description
Extended Education,,
Off Campus Study,G80,Off Campus Study
Aboriginal Focus Programs,G20-29,Aboriginal Environmental Stewardship Program
,G70,Health Career Transition Year
,G71,Nelson House Transition Year
,G74-77,Aboriginal Community Wellness
,G78-79,Aboriginal Child & Family Services Diploma
Access Program,G019610,HEAL 1600
,,
,,ARTS 1110
,,
,,MATH 0500 (remedial course 96 0 bill hours)
,,
,,Faculty of Science/Arts courses
Centre for Ukrainian Studies,G15,Ukrainian Canadian Studies (Arts/Fine Arts)
Prairie Theatre Exchange,G16,Prairie Theatre Exchange
ELC (English Language Centre),G01,"ESLC 0902, 0912, 0922, 0992"
Nursing,,
RRC,"A50, 51",U of M courses taught at RRC (OC campus code)
NURS 0500 course,G01,Preparation for Professional Practice
Work Terms,,
ENVR 3980,G01,Work Term 1
"IDM 2980, 3980, 4980",G01,"Work Term 1, 2, 3 (students prior to 2011-12)"
"IDM 2982, 3982, 4982",G01,"Work Term 1, 2, 3 (students 2011-12 forward)"
Re-registration sections,"A02,03",Students continuing not reassessed96 session G 96 0 bill hrs
Social Work - Cohorts,,
Southeast Cohort,G45,
Michif Cohort,G47,
Brandon Cohort,G48,
Metis Cohort,G49,
Northern Program,G64-66,Thompson
Portage la Prairie Cohort,G67,
SWRK 3150 4120,G68-69,Fall/Winter Terms
,,
Field Instruction/DE students,G46,Winter-Summer spanned term
William NorrieCentre,N01-99,
,,
,,
Education,,
French as 2nd Language STB,G30-31,
Weekend College,G32-35,
Practicum,G36-44,Tui/Fee Waiver box unchecked 96 tuition also assessed
Post-Baccalaureate Diploma (Main Campus),G50-56,
Post-Baccalaureate Diploma (Off Campus),G57-59,
Education (Extended Education),G90,Management Professional & Community Program
Medicine,,
UGME 1500/2500,"G01, 02",BSc Med
UGME 1990/2990,"G01, 02",Summer Early Exposure
UGME 4500,"G01, 02",External Electives
Dentistry,,
"ORLB 1500, 2500","G01, 02",BSc Dent
Other:,,
IUS,I01-I99,Inter-University Services
Lecture Sections,A01-90,
Challenge for Credit,A91-92,
High School Challenge for Credit,A93,
Lab Sections,B01-90,
Lab Exemptions,B98-99,
Distance & On-Line Education,D01-90,
Special Exams (Engineering),A79,
    """
    code = "00"  # default: Unknown
    if section.section_name[0].lower() in ["a", "t"]:
        # Lecture
        code = "cl"
    if section.section_name[0].lower() == "b":
        # Lab
        code = "lb"
    if section.section_name[0].lower() == "d":
        # Online
        code = "on"
    if section.section_name[0].lower() == "k":
        # field work
        code = "fw"
    if section.section_name[0].lower() in ["g", "n", "r", "x"]:
        # Other -- not displayed in default templates!
        code = "zz"
    # Only update if this is a change:
    if code != section.section_type:
        return code
    # Otherwise, do not update:
    return None


##############################################################

DEFAULT = {
    #     'default_class_code': 'STAT',
    "important_dates:days_in_advance": 14,
    "course_outlines:upload_to": "handouts/%Y/%m",
    "course_outlines:storage": default_storage,
    "api:important_dates_src_url": None,  # if this is set, important dates will be pulled
    "semester:advertisement_rules": {
        "in_advance_days": {  # how many days before the start to begin advertising.
            "1": 21,
            "2": 14,
            "3": 14,
        },
        "grace_period": {  # how many days after the end to keep advertised.
            "1": 14,
            "2": 4,
            "3": 14,
        },
        "next": {
            "1": 1,  # in the winter, advertise winter, summer
            "2": 2,  # in the summer, advertise summer, fall, and winter
            "3": 1,  # in the fall, advertise fall and winter
        },
    },
    "section_type:choices": (
        ("00", "Unknown"),
        ("cl", "Lecture"),
        ("lb", "Lab"),
        ("on", "Online"),
        ("fw", "Field work"),
        ("zz", "Other"),
    ),
    "section_type:default": "00",
    "section_type:on_save": determine_section_type,
    # see strftime docs:
    # https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
    "timeslot:display:time_format": "%I:%M %p",
    "timeslot:display:trim_leading_zeros": True,
    # use this if you want MultiSectionFilterField to always have some
    # sane example default.
    # Use None to prevent the default inital value.
    "multisectionfilterfield:default-course-slug": None,
    "sectionhandout:title": "outline",
    "sectionhandout:title:plural": None,  # just add 's'
    "coursehandout:title": "material",
    "coursehandout:title:plural": None,
}

##############################################################


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


##############################################################


def get_all():
    """
    Return all current settings as a dictionary.
    """
    app_settings = getattr(settings, CONFIG_NAME, DEFAULT)
    return dict(
        [(setting, app_settings.get(setting, DEFAULT[setting])) for setting in DEFAULT]
    )


##############################################################
