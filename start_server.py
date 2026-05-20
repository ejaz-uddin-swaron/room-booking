#!/usr/bin/env python
import os
import sys
import django
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookings.settings')
django.setup()

logging.basicConfig(level=logging.DEBUG)

from django.core.management import call_command
call_command('runserver', '8000', '--noreload')