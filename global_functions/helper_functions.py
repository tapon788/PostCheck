# ======================== Imports ========================

import sys, os


def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return relative_path
    return os.path.join(base_path, relative_path)


DISPLAY_COLUMNS = [
    "Severity",
    "Alarm Time",
    "Alarm Number",
    "Alarm Text",
    "Supplementary Information",
    "Distinguished Name",
    "Diagnostic Info",
    "Name",
]

DISPLAY_COLUMNS_NEW = [
    "Severity",
    "Alarm Time",
    "Cancel Time",
    "Alarm Number",
    "Alarm Text",
    "Supplementary Information",
    "Distinguished Name",
    "History Match",
    "Status",
    "Resolved",
    "Diagnostic Info",
    "Name",
    "History Count",
]