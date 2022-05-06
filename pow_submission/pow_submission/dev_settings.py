from icf_navigator.settings import *

INSTALLED_APPS += [
    # BDD testing
    'behave_django',
]

#Email settings

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/Users/whortonjustinm/work/email'

DEBUG = True
