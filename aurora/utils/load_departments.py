"""
Load Department information
"""
#######################
from __future__ import print_function, unicode_literals

from classes.models import Department

#######################
from django.template.defaultfilters import slugify

from ..models import AuroraDepartment


def load_departments(year, term, data):
    warnings = []
    for code, name in data:
        dept = AuroraDepartment.objects.find(code)
        if dept is None:
            slug = slugify(code)
            dept, created = Department.objects.get_or_create(
                code=code, defaults={"slug": slug, "name": name, "advertised": False}
            )
            AuroraDepartment.objects.create(
                department_code=code, department=dept, synchronize=True
            )
            if created:
                warnings.append("Created new Department: {0}".format(dept))
    return warnings
