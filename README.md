# django-dept-classes

The `classes` app provides core models for
representing course information.  This is typically
*way* more complex than people really think about,
but allows for much greater flexibility.

The `aurora` app provides integration with the
*Aurora/Banner* system.

Of particular interest is the file
`aurora/utils/aurora_scrape.py` which scrapes
the public schedule and provides an intermediate
data representation.

## Scheduled tasks

For, e.g., `cron`:
```
1 4 * * *      /usr/local/sbin/django-admin aurora load_classes --delete
2 4 * * *      /usr/local/sbin/django-admin aurora update_enrollment
@monthly       /usr/local/sbin/django-admin aurora update_course_desc STAT
31 4 * * *     /usr/local/sbin/django-admin classes instructor_beat
30 0 * * *     /usr/local/sbin/django-admin classes semester_beat
```
