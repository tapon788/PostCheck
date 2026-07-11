import sys, os

def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return relative_path
    return os.path.join(base_path, relative_path)


DISPLAY_COLUMNS = [
    "Severity",
    "Alarm Number",
    "Supplementary Information",
    "Distinguished Name",
    "Alarm Time",
    "Alarm Text",
    "Diagnostic Info",
    "Name",
]

DISPLAY_COLUMNS_NEW = [
    "Severity",
    "Alarm Number",
    "Supplementary Information",
    "Distinguished Name",
    "Alarm Time",
    "History Match",
    "Status",
    "Resolved",
    "Cancel Time",
    "Alarm Text",
    "Diagnostic Info",
    "Name",
    "History Count",
]