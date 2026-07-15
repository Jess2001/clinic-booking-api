# conftest.py
import pytest
from django.conf import settings

def pytest_configure():
    """
    Globally removes WhiteNoise middleware from settings during tests 
    to prevent ModuleNotFoundError in environments where it is not installed.
    """
    settings.MIDDLEWARE = [
        mw for mw in settings.MIDDLEWARE 
        if "whitenoise" not in mw.lower()
    ]