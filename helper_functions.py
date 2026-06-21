import sys, os

def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return relative_path
    return os.path.join(base_path, relative_path)