# settings.py
TIME_ZONE = "Asia/Colombo"
USE_TZ = True

MONGODB_URI = "mongodb+srv://keshani20001:eLSirljKQERFpY2K@cluster0.yjt01ev.mongodb.net/?retryWrites=true&w=majority"
MONGODB_DB_NAME = "smarthr"
MONGODB_GRIDFS_BUCKET = "faces"

# SFace cosine threshold: 0.40–0.55 is typical (higher = stricter)
ATTENDANCE_SIM_THRESHOLD = 0.45
