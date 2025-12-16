class Config:
    SECRET_KEY = 'nucifera'
    SQLALCHEMY_DATABASE_URI = 'mysql://poc_user:nucifera@localhost/poc_platform'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = 'nucifera'
