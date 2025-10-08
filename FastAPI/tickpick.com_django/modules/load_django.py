import os
import sys
import django

# Path to the Django project directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tickpickcom_project')))

os.environ['DJANGO_SETTINGS_MODULE'] = 'tickpickcom_project.settings'

django.setup()
