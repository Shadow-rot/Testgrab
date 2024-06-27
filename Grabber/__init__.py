import logging
from pyrogram import Client
from telegram.ext import Application
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)

logging.getLogger("apscheduler").setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger("pyrate_limiter").setLevel(logging.ERROR)
LOGGER = logging.getLogger("name")

OWNER_ID = "5116239739"
sudo_users = ["5116239739", "6691228672"]
GROUP_ID = "-1002010986967"
TOKEN = "6770670571:AAF7G93zLKRgKPI9CLf5NqJs0imW2IiVMSM"
mongo_url = "mongodb+srv://Srikanta:srikanta@cluster0.xzbil3m.mongodb.net/?retryWrites=true&w=majority"
PHOTO_URL = ["https://graph.org/file/cafd84de9c790da6ce770.jpg", "https://graph.org/file/407a498548a0f4c6881b3.jpg"]
SUPPORT_CHAT = "https://t.me/slavesupport"
UPDATE_CHAT = "https://t.me/slave_waifu_update"
BOT_USERNAME = "@Slavge_wafiu_bot"
CHARA_CHANNEL_ID = ""
api_id = "27744639"
api_hash = "a5e9da62bcd7cc761de2490c52c89ccf"

application = Application.builder().token(TOKEN).build()
Grabberu = Client("Grabber", api_id, api_hash, bot_token=TOKEN)
client = AsyncIOMotorClient(mongo_url)
db = client['Character_catcher']
collection = db['anime_characters']
user_totals_collection = db['user_totals']
user_collection = db["user_collection"]
group_user_totals_collection = db['group_user_total']
top_global_groups_collection = db['top_global_groups']
