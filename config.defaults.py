import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    DRIVE_VIEW=''
    DRIVE_ADD=''
    DRIVE_EDIT=''
    DOCS_FILE_ID = ''
    SHEETS_FILE_ID = ''
    SHEETS_RANGE = 'Form Responses 1'
    TEMPLATE_PREFIX = 'Plantenfiche - AUTO - '
    IMAGE_SIZE = 120