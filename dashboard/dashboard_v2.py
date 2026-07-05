"""Compatibility wrapper.

Dashboard V2 has been superseded by Dashboard V4.
Existing scripts that import build_dashboard_v2 will continue to work.
"""

from dashboard.dashboard_v4 import build_dashboard_v4


def build_dashboard_v2():
    return build_dashboard_v4()


if __name__ == "__main__":
    build_dashboard_v2()
