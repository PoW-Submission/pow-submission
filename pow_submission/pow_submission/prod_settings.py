from pow_submission.settings import *

ALLOWED_HOSTS = ['plan-of-work.apps.dbmi.cloud', 'plan-of-work-dev.apps.dbmi.cloud']

SECRET_KEY = os.getenv('POW_DJANGO_SECRET_KEY', '^%(#2k$5n08-i2=t8f%w3iy3^)g(=nfjy#%)!!rqx_0q3e#*ym')

DEBUG = False

# Login URL

LOGIN_URL = "https://plan-of-work-dev.apps.dbmi.cloud"

#Email settings

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_FILE_PATH = ''
EMAIL_HOST = 'mail.uams.edu'
EMAIL_PORT = 25

# reCAPTCHA settings

GOOGLE_RECAPTCHA_SECRET_KEY = os.getenv('GOOGLE_RECAPTCHA_SECRET_KEY', 'mysecretkey')
GOOGLE_RECAPTCHA_SITE_KEY = os.getenv('GOOGLE_RECAPTCHA_SITE_KEY', 'mysitekey')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'pow_submission',
        'USER': os.getenv('POW_DATABASE_USER', 'mydatabaseuser'),
        'PASSWORD': os.getenv('POW_DATABASE_PASSWORD', 'mypassword'),
        'HOST': os.getenv('POW_DATABASE_HOST', 'localhost'),
        'PORT': '5432',
    }
}
