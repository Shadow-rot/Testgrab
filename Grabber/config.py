class Config(object):
    LOGGER = True

    # Get this value from my.telegram.org/apps
    OWNER_ID = "5147822244"
    sudo_users = "5147822244", "6507226414", "7938543259"
    GROUP_ID = -1002191083108
    TOKEN = "7891572866:AAGxHInquTfmwRgJo4NWjnP7I6GHTPUdKc4"
    mongo_url = "mongodb+srv://tiwarireeta004:peqxLEd36RAg7ors@cluster0.furypd3.mongodb.net/?retryWrites=true&w=majority"
    PHOTO_URL =["https://graph.org/file/cafd84de9c790da6ce770.jpg", "https://graph.org/file/407a498548a0f4c6881b3.jpg"]
    SUPPORT_CHAT = "idkkkkkkkkjjlk"
    UPDATE_CHAT = "siya_infoo"
    BOT_USERNAME = "waifukunbot"
    CHARA_CHANNEL_ID = "-1002059929123"
    api_id = 17944283
    api_hash = "03f2f561ca86def71fe88d3ae16ed529"

    
class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
