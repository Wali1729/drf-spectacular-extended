import django

# PEP 440-compliant version for PyPI distribution of the extended fork.
__version__ = '0.29.0.post1'

if django.VERSION < (3, 2):
    default_app_config = 'drf_spectacular.apps.SpectacularConfig'
