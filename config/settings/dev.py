from pathlib import Path
from decouple import config, Csv
from .base import *
DEBUG = config("DEBUG", cast=bool, default=True)
ALLOWED_HOSTS +=["127.0.0.1" , "localhast"]
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
 