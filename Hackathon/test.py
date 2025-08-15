import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import json
import os

# ----- CONFIG -----
MONGO_URI = "mongodb+srv://shitalgautam34:XunxpPQTCbNePuUK@cluster0.e7fkuyl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "cluster0"
EXPORT_FILE = "db_dump.json"

# JSON encoder for ObjectId and datetime
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

async def main():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    print("\n===== DATABASE EXPORT STARTED =====")
    collections = await db.list_collection_names()
    print(f"Found collections: {collections}\n")

    export_data = {}

    for coll_name in collections:
        coll = db[coll_name]
        docs = await coll.find().to_list(length=None)
        export_data[coll_name] = docs
        print(f"Exported {len(docs)} docs from '{coll_name}'")

    # Save to file
    with open(EXPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=4, cls=MongoJSONEncoder, ensure_ascii=False)

    print(f"\n✅ Export complete! Saved to '{os.path.abspath(EXPORT_FILE)}'")
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
