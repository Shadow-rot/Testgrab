class Config(object):
    LOGGER = True

    # Get this value from my.telegram.org/apps
    OWNER_ID = "5116239739"
    sudo_users = "5116239739", "6691228672", "7185106962"
    GROUP_ID = -1002010986967
    TOKEN = "6770670571:AAF7G93zLKRgKPI9CLf5NqJs0imW2IiVMSM"
    mongo_url = "mongodb+srv://tiwarireeta004:peqxLEd36RAg7ors@cluster0.furypd3.mongodb.net/?retryWrites=true&w=majority"
    PHOTO_URL =["https://graph.org/file/cafd84de9c790da6ce770.jpg", "https://graph.org/file/407a498548a0f4c6881b3.jpg"]
    SUPPORT_CHAT = "slavesupport"
    UPDATE_CHAT = "slavesupport"
    BOT_USERNAME = "Slavge_wafiu_bot"
    CHARA_CHANNEL_ID = "-1002233863654"
    api_id = 27744639
    api_hash = "a5e9da62bcd7cc761de2490c52c89ccf"

    
class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
