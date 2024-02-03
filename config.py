import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    TESTS= os.environ.get('TESTS')
    SYNOLOGY_SERVER= os.environ.get('SYNOLOGY_SERVER')
    SYNOLOGY_FOLDER_NOTES= os.environ.get('SYNOLOGY_FOLDER_NOTES')
    EMAIL_ADDRESS= os.environ.get('EMAIL_ADDRESS')
    EMAIL_SECRET= os.environ.get('EMAIL_SECRET')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')\
        or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
