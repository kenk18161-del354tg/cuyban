import os

BOT_TOKEN = os.getenv('BOT_TOKEN', '')
OWNER_ID = int(os.getenv('OWNER_ID', '0'))
GROUP_ID = int(os.getenv('GROUP_ID', '0'))
DATABASE_URL = os.getenv('DATABASE_URL', '')
BOT_NAME = os.getenv('BOT_NAME', 'BlockAll Bot')
OWNER_USERNAME = os.getenv('OWNER_USERNAME', '')
TIMEZONE = os.getenv('TIMEZONE', 'America/Lima')
MAINTENANCE = os.getenv('MAINTENANCE', 'false').lower() == 'true'
