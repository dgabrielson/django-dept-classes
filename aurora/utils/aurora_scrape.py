#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scrape class schedules from UManitoba Aurora.
Return XML or python data.

This script is designed to either be run from the command line, using python,
or as a python module.  When being run as a module, the ``main`` function is most useful.

When being run as a script, you can run: python aurora_scrape.py for usage information.
(Dependencies are always checked at runtime.  This requires the python lxml module to run.)


Please feel free to submit questions, comments, bug reports, etc.
© Copyright 2013-2019 Dave Gabrielson <dave.gabrielson@gmail.com>
To test this module:
workon stats
PYTHONPATH="$HOME/src/site-stats:$PYTHONPATH" DJANGO_SETTINGS_MODULE='stats.settings' python aurora_scrape.py STAT 2014 winter
"""
#######################
from __future__ import print_function, unicode_literals

import sys
from datetime import date
from pprint import pprint  # only used in the driver.

import lxml.html
from aurora import conf
from django.utils import six
from lxml import etree as ETree

#######################

try:
    # Python 3:
    from urllib.parse import urlparse, urlencode
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError
except ImportError:
    # Python 2:
    from urlparse import urlparse
    from urllib import urlencode
    from urllib2 import urlopen, Request, HTTPError, URLError

try:
    import lxml
except ImportError:
    print(
        """This module requires lxml; try one of the following:
    pip install lxml
    easy_install lxml
    apt-get install python-lxml
(or similar).
(The lxml module is used for parsing the Aurora/Banner HTML.)
"""
    )
    sys.exit(1)

# NOTE: currently, the built-in etree modules do not read Aurora/Banner HTML
"""
Reference defaults in case conf is not available (UofM)
{
    'banner:root_uri': 'http://aurora.umanitoba.ca',
    'banner:course_list_url': '/banprod/bwckschd.p_get_crse_unsec',
    'banner:schedule_detail_url': '/banprod/bwckschd.p_disp_detail_sched',
    'banner:department_list_url': '/banprod/bwckctlg.p_disp_cat_term_date',
}
"""

BANNER_ROOT = conf.get("banner:root_uri")
COURSE_LIST_URI = BANNER_ROOT + conf.get("banner:course_list_url")
CATALOG_ENTRY_URI = BANNER_ROOT + conf.get("banner:catalog_entry_url")
SCHEDULE_DETAIL_URI = BANNER_ROOT + conf.get("banner:schedule_detail_url")
DEPARTMENT_LIST_URI = BANNER_ROOT + conf.get("banner:department_list_url")

URL_DATA = [
    ["term_in", ""],
    ["sel_subj", "dummy"],
    ["sel_day", "dummy"],
    ["sel_schd", "dummy"],
    ["sel_insm", "dummy"],
    ["sel_camp", "dummy"],
    ["sel_levl", "dummy"],
    ["sel_sess", "dummy"],
    ["sel_instr", "dummy"],
    ["sel_ptrm", "dummy"],
    ["sel_attr", "dummy"],
    ["sel_subj", ""],
    ["sel_crse", ""],
    ["sel_title", ""],
    ["sel_from_cred", ""],
    ["sel_to_cred", ""],
    ["sel_camp", "%"],
    ["sel_levl", "%"],
    ["sel_ptrm", "%"],
    ["sel_dunt_code", ""],
    ["sel_dunt_unit", ""],
    ["sel_instr", "%"],
    ["sel_attr", "%"],
    ["begin_hh", "0"],
    ["begin_mi", "0"],
    ["begin_ap", "a"],
    ["end_hh", "0"],
    ["end_mi", "0"],
    ["end_ap", "a"],
]  # ordering is relevant to aurora/banner. *sigh*

TERMS = (("10", "winter"), ("50", "summer"), ("90", "fall"))

##############################################################

# def get_etree(url):
#     """
#     Get the element tree structure for the given page.
#     """
#     page = urlopen(url)
#     html = ETree.HTML(page.read())
#     return html


def get_etree(url):
    """
    Get the element tree structure for the given page.
    """
    page = urlopen(url)
    html = lxml.html.fromstring(page.read())
    return html


################################################################


def get_child_by_tag(node, tag, class_=None, raise_exception=True):
    """
    Given the DOM node, find it's child with the given tag and class_

    If ``raise_exception`` is True, an AssertionError will be raised
    if the child cannot be found, otherwise, this function returns
    ``None``.
    """
    for child in node.getchildren():
        child_classes = child.attrib.get("class", "").split()
        if child.tag == tag:
            if class_ is None:
                return child
            if class_ in child_classes:
                return child
    if raise_exception:
        assert False, "Could not find child tag {0} with class {1}".format(tag, class_)


################################################################


def print_child_structure(node, depth=0):
    for child in node:
        print("\t" * depth, child.tag, "\t", child.attrib.get("class", ""))
        print_child_structure(child, depth + 1)


##############################################################


def get_term_code(term_name):
    """
    Given a name, like 'winter', return the corresponding code, e.g., '10'
    """
    given_name = term_name.strip().lower()
    for code, name in TERMS:
        if name == given_name:
            return code
    assert False, "term name %r not recognized" % term_name


def get_page_fp(subject, year, term_name):
    """
    Given the initial inputs, get the file object for that page.
    """
    postdata = []
    for name, value in URL_DATA:
        if name == "term_in":
            value = str(year) + get_term_code(term_name)
        if name == "sel_subj" and not value:
            value = subject.upper()
        postdata.append((name, value))
    if six.PY3:
        url_data = bytes(urlencode(postdata), encoding="utf8")
    elif six.PY2:
        url_data = urlencode(postdata)
    else:
        raise RuntimeError("unexpected six python verison")

    url_fp = urlopen(COURSE_LIST_URI, url_data)
    return url_fp


def scrape_row_header(element):
    """
    ``element`` is expected to be an a tag, with a value like:
    Basic Statistical Analaysis 1 - 10796 - STAT 1000 - A01

    NOTE: [observed 2012-Dec-18] Other formats exist...
        Should develop a better heuristic for this.
    """
    result = {}
    assert element.tag == "a", "unexpected input"
    result["schedule_href"] = element.attrib["href"]
    bytes = ETree.tostring(element, encoding="utf-8")
    try:
        text = str(element.text)
    except UnicodeDecodeError:
        # Seen in production data: mixing latin-1 and utf-8.
        # Seen on 2019-Jan-31; data in Summer 2014 (St. Boniface)
        s = bytes.decode("latin1")
        p1 = s.find(">")
        p2 = s.rfind("<")
        if p1 != -1 and p2 != -1:
            text = s[p1 + 1 : p2]
        else:
            assert False, "totally unexpected input"

    classinfo = text.rsplit(" - ", 3)
    result["class_verbosename"] = classinfo[0]
    result["class_crn"] = classinfo[1]
    result["class_name"] = classinfo[2]  # e.g., STAT 1000
    result["class_section"] = classinfo[3]
    return result


def scrape_row_info(element):
    """
    Scrape the element. Return all found info as a dictionary.
    """
    result = {}
    notes = []

    if element.text is not None and element.text.strip():  # initial note
        notes.append(element.text.strip())

    spans = element.findall("span")
    for e in spans:  # labelled info.
        result[e.text.strip().rstrip(":").lower().replace(" ", "_")] = (
            e.tail.strip().rstrip(" (") if e.tail is not None else None
        )
    children = element.getchildren()

    for child in children:
        if child.tag == "p" and len(child) > 0:
            result.update(scrape_row_info(child))

    for child in children:  # extra notes
        if child.tag == "span":
            break
        if child.tail is not None and child.tail.strip():
            notes.append(child.tail.strip())

    for child in children:  # unlabelled info -- annoying.
        if child.tag == "br" and child.tail is not None:
            tail = child.tail.strip()
            if "Campus" in tail:
                result["campus"] = tail
            if "Schedule" in tail:
                result["schedule_type"] = tail
            if "Credits" in tail:
                result["credit_hours"] = tail

    for child in element.findall("a"):
        if (child.text is not None) and ("View Catalog Entry" == child.text.strip()):
            result["catalog_entry_href"] = child.attrib["href"]

    result["note"] = notes

    # the schedule of meeting times.
    schedule = element.find("table")
    if schedule is not None:
        result["schedule"] = []
        headers = schedule[1]
        for row in schedule[2:]:  # 0: title, 1: headers
            sched = {}
            for i in range(len(headers)):
                if row[i].text is not None and row[i].text.strip():
                    key = headers[i].text.strip().lower().replace(" ", "_")
                    value = row[i].text.strip()  # .rstrip(' (')
                    sched[key] = value
                    if key == "instructors":
                        # augument to:
                        #   instructor_primary -> name with (P) mark
                        #   instructors -> list of names, not including primary
                        #   instructors_email -> dict of name: email
                        # src: https://stackoverflow.com/a/15074386
                        nodetext = "".join([x for x in row[i].itertext()])
                        nodelist = []
                        for e in nodetext.split(","):
                            if e.endswith(" (P)"):
                                e = e[:-3].strip()
                                sched["instructor_primary"] = e
                            else:
                                nodelist.append(e.strip())
                        sched[key] = nodelist

                        # get email also.
                        for child in row[i]:
                            if child.tag == "a" and child.attrib["href"].startswith(
                                "mailto:"
                            ):
                                target = child.attrib["target"]
                                mailto = child.attrib["href"]
                                addr = mailto[mailto.find(":") + 1 :]
                                if "instructors_email" not in sched:
                                    sched["instructors_email"] = {}
                                sched["instructors_email"][target] = addr
            result["schedule"].append(sched)

    return result


def scrape_tr_pair(header, info):
    """
    Course information occurs in TR pairs: one TR for a header, and one TR for details.
    """
    result = {}
    result.update(scrape_row_header(header.find("th").find("a")))
    result.update(scrape_row_info(info.find("td")))
    return result


def scrape_page(html):
    """
    Extract the information from the HTML root element.
    """
    # setup.
    body = get_child_by_tag(html, "body")
    pagebodydiv = get_child_by_tag(body, "div", "pagebodydiv")
    datadisplaytable = get_child_by_tag(
        pagebodydiv, "table", "datadisplaytable", raise_exception=False
    )
    if datadisplaytable is None:
        return []
    assert datadisplaytable[0].text == "Sections Found", "no sections found, bailing..."
    tr_list = list(datadisplaytable)[1:]
    assert len(tr_list) % 2 == 0, "expected TRs in pairs... what?"
    results = []
    for header, info in zip(tr_list[::2], tr_list[1::2]):
        results.append(scrape_tr_pair(header, info))
    return results


def main(subject, year, term_name):
    """
    Given ``subject``, ``year``, ``term_name``, do the heavy lifting.
    Return a list of python dictionary.
    """
    page = get_page_fp(subject, year, term_name)
    html = ETree.HTML(page.read())
    info = scrape_page(html)
    return info


def to_xml(info):
    """
    Convert the ``info`` to an etree XML structure.
    """

    def _to_xml_fragment(node, name, data):

        if isinstance(data, list):  # recursive
            # iterate over each item
            for item in data:
                _to_xml_fragment(node, name, item)

        if isinstance(data, dict):  # recursive
            # iterate over key, value pairs
            element = ETree.SubElement(node, name)
            for key, value in data.items():
                _to_xml_fragment(element, key, value)

        if isinstance(data, six.string_types):  # terminal
            element = ETree.SubElement(node, name)
            element.text = data

    root = ETree.Element("classes")
    _to_xml_fragment(root, "class", info)
    return root


##########################################################
####
#### Enrollment specific code
####
##########################################################


def scrape_page_detailed_info(html):
    """
    Extract the information from the HTML root element.
    """
    # setup.
    body = get_child_by_tag(html, "body")
    pagebodydiv = get_child_by_tag(body, "div", "pagebodydiv")
    datadisplaytable = get_child_by_tag(
        pagebodydiv, "table", "datadisplaytable", raise_exception=False
    )
    if datadisplaytable is None:
        return []
    assert (
        datadisplaytable[0].text == "Detailed Class Information"
    ), "no detailed info found, bailing..."
    tr_list = list(datadisplaytable)[1:]
    assert len(tr_list) % 2 == 0, "expected TRs in pairs... what?"
    enrollment_table = tr_list[1][0].find("table")
    # formatting check:
    assert (
        enrollment_table.attrib["class"] == "datadisplaytable"
    ), "Unexpected layout! [3] Aborting..."
    assert (
        enrollment_table.attrib["summary"]
        == "This layout table is used to present the seating numbers."
    ), "Unexpected layout! [4] Aborting..."
    headers = [e[0].text for e in enrollment_table[1][1:]]
    assert headers == [
        "Capacity",
        "Actual",
        "Remaining",
    ], "Unexpected layout! [5] Aborting..."
    enrollment_result = [int(e.text) for e in enrollment_table[2][1:]]
    if enrollment_table[3] is not None:
        waitlist_result = [int(e.text) for e in enrollment_table[3][1:]]
        # pprint(enrollment_table[3][0].text)
        # pprint(waitlist_result)
    else:
        waitlist_result = [0, 0, 0]
    return enrollment_result + waitlist_result


def enrollment_info(crn, year, term_name):
    """
    Given ``crn``, ``year``, ``term_name``,
    scrape enrollment information.

    Returns the sextet ``capacity``, ``actual``, ``remaining``,
    ``waitlist_capacity``, ``waitlist_actual``, ``waitlist_remaining``
    """
    term = str(year) + get_term_code(term_name)
    uri = SCHEDULE_DETAIL_URI
    uri += "?term_in={0}&crn_in={1}".format(term, crn)
    html = get_etree(uri)
    return scrape_page_detailed_info(html)


##########################################################


def scrape_catalog_desc(html):
    """
    Extract the information from the HTML root element.
    """
    # setup.
    body = get_child_by_tag(html, "body")
    pagebodydiv = get_child_by_tag(body, "div", "pagebodydiv")
    datadisplaytable = get_child_by_tag(
        pagebodydiv, "table", "datadisplaytable", raise_exception=False
    )
    if datadisplaytable is None:
        return ""
    return datadisplaytable[1][0].text.strip()


def fetch_catalog_entry(href):
    uri = BANNER_ROOT + href
    html = get_etree(uri)
    return scrape_catalog_desc(html)


##########################################################


def get_current_termcode():
    today = date.today()
    year = today.year
    term_name = None
    if 1 <= today.month < 5:
        term_name = "winter"
    if 5 <= today.month < 9:
        term_name = "summer"
    if 9 <= today.month < 13:
        term_name = "fall"
    assert term_name is not None, "Could not determine term name from month"
    term = str(year) + get_term_code(term_name)
    return term


##########################################################


def build_catalog_entry_url(department, course):
    uri = CATALOG_ENTRY_URI
    term = get_current_termcode()
    uri += "?term_in={0}".format(term)
    uri += "&one_subj={0}&sel_crse_strt={1}&sel_crse_end={1}".format(department, course)
    uri += "&sel_subj=&sel_levl=&sel_schd=&sel_coll=&sel_divs=&sel_dept=&sel_attr="
    return uri


##########################################################


def fetch_catalog_entry_page_by_course(department, course):
    """
    Where ``department`` and ``course`` are the codes for these;
    e.g., "STAT" and "2400".

    **For now**, just use the current term for the query.
    """
    return get_etree(build_catalog_entry_url(department, course))


##########################################################


def fetch_catalog_entry_by_course(department, course):
    html = fetch_catalog_entry_page_by_course(department, course)
    return scrape_catalog_desc(html)


##########################################################


def scrape_department_list(html):
    """
    Given an html etree, return a list of (code, name) tuples
    for departments.
    """
    select = html.get_element_by_id("subj_id")
    return [
        (child.attrib["value"], child.text.strip())
        for child in select
        if child.tag == "option"
    ]


def fetch_department_list(year, term_name):
    term = str(year) + get_term_code(term_name)
    uri = DEPARTMENT_LIST_URI
    uri += "?cat_term_in={0}".format(term)
    html = get_etree(uri)
    return scrape_department_list(html)


##########################################################

if __name__ == "__main__":
    """
    Program entry point.
    """
    if len(sys.argv) != 4:
        print("Usage: python %r <department_code> <year> <term>" % sys.argv[0])
        print("")
        print("   example: python %r STAT 2011 winter" % sys.argv[0])
        print("   known terms are:", ", ".join(sorted([t[1] for t in TERMS])))
        sys.exit(1)
    subject, year, term_name = sys.argv[1:4]

    if subject.isdigit():  # assume a CRN
        capacity, actual, remaining, wait_cap, wait_act, wait_remain = enrollment_info(
            subject, year, term_name
        )
        print("Enrollment:")
        print("  capacity:", capacity)
        print("    actual:", actual)
        print(" remaining:", remaining)
        print(" waitlist capacity: {0}".format(wait_cap))
        print("   waitlist actual: {0}".format(wait_act))

    else:
        info = main(subject, year, term_name)
        from pprint import pprint

        pprint(info)

#
