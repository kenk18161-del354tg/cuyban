import os

BOT_TOKEN            = os.getenv('BOT_TOKEN', '')
OWNER_ID             = int(os.getenv('OWNER_ID', '0'))
GROUP_ID             = int(os.getenv('GROUP_ID', '0'))
DATABASE_URL         = os.getenv('DATABASE_URL', '')
BOT_NAME             = os.getenv('BOT_NAME', 'BlockAll Bot')
OWNER_USERNAME       = os.getenv('OWNER_USERNAME', '')
TIMEZONE             = os.getenv('TIMEZONE', 'America/Lima')
MAINTENANCE          = os.getenv('MAINTENANCE', 'false').lower() == 'true'
MAIN_IMAGE           = os.getenv('MAIN_IMAGE', 'assets/imagen_principal.jpg')
MAX_REQUESTS_PER_DAY = int(os.getenv('MAX_REQUESTS_PER_DAY', '10'))
REQUIRE_GROUP_MEMBER = os.getenv('REQUIRE_GROUP_MEMBERSHIP', 'true').lower() == 'true'
CHANNEL_ID           = int(os.getenv('CHANNEL_ID', '0'))
LOG_CHANNEL_ID       = int(os.getenv('LOG_CHANNEL_ID', '0'))
NOTIFY_ON_ORDER      = os.getenv('NOTIFY_ON_ORDER', 'true').lower() == 'true'
NOTIFY_ON_NEW_USER   = os.getenv('NOTIFY_ON_NEW_USER', 'true').lower() == 'true'
