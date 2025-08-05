import asyncio
import json
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# ----- CONFIG -----
MONGO_URI = "mongodb+srv://shitalgautam34:XunxpPQTCbNePuUK@cluster0.e7fkuyl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "cluster0"  # use the same DB as main.py
DROP_DB = True   # set True to drop DB before creating (dangerous!)

# ----- JSON Schema validators -----
NICHES_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["slug", "name", "created_at"],
        "properties": {
            "slug": {"bsonType": "string"},
            "name": {"bsonType": "string"},
            "description": {"bsonType": ["string", "null"]},
            "created_at": {"bsonType": "date"}
        }
    }
}

USERS_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["username", "email", "role", "created_at"],
        "properties": {
            "username": {"bsonType": "string"},
            "email": {"bsonType": "string"},
            "role": {"enum": ["founder", "funder"]},
            "profile": {
                "bsonType": "object",
                "properties": {
                    "bio": {"bsonType": ["string", "null"]},
                    "joined_at": {"bsonType": "date"},
                    "main_niche": {"bsonType": ["objectId", "null"]}
                }
            },
            "niche_stats": {
                "bsonType": ["object", "null"]
                # we allow an object with dynamic keys (niche_id -> stats)
            },
            "posts": {"bsonType": ["array", "null"]},
            "liked_posts": {"bsonType": ["array", "null"]},
            "created_at": {"bsonType": "date"}
        }
    }
}

POSTS_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["founder_id", "title", "niche_id", "created_at"],
        "properties": {
            "founder_id": {"bsonType": "objectId"},
            "title": {"bsonType": "string"},
            "description": {"bsonType": ["string", "null"]},
            "niche_id": {"bsonType": "objectId"},
            "media": {
                "bsonType": ["object", "null"],
                "properties": {
                    "images": {"bsonType": ["array", "null"], "items": {"bsonType": "string"}},
                    "youtube_links": {"bsonType": ["array", "null"], "items": {"bsonType": "string"}}
                }
            },
            "gemini_rating": {
                "bsonType": ["object", "null"],
                "properties": {
                    "score": {"bsonType": ["double", "int"]},
                    "scale": {"bsonType": "int"},
                    "computed_at": {"bsonType": "date"},
                    "explain": {"bsonType": ["string", "null"]}
                }
            },
            "user_rating": {
                "bsonType": ["object", "null"],
                "properties": {
                    "total_score": {"bsonType": ["int", "double"]},
                    "count": {"bsonType": "int"},
                    "avg": {"bsonType": ["double", "int"]}
                }
            },
            "combined_rating": {
                "bsonType": ["object", "null"],
                "properties": {
                    "score": {"bsonType": ["double", "int"]},
                    "scale": {"bsonType": "int"},
                    "computed_at": {"bsonType": "date"}
                }
            },
            "likes_count": {"bsonType": "int"},
            "comments_count": {"bsonType": "int"},
            "views_count": {"bsonType": "int"},
            "created_at": {"bsonType": "date"},

            # NEW comments array field
            "comments": {
                "bsonType": ["array", "null"],
                "items": {
                    "bsonType": "object",
                    "required": ["user_id", "username", "comment", "created_at"],
                    "properties": {
                        "user_id": {"bsonType": "objectId"},
                        "username": {"bsonType": "string"},
                        "comment": {"bsonType": "string"},
                        "created_at": {"bsonType": "date"}
                    }
                }
            }
        }
    }
}


REVIEWS_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["post_id", "score", "created_at"],
        "properties": {
            "post_id": {"bsonType": "objectId"},
            "user_id": {"bsonType": ["objectId", "null"]},
            "score": {"bsonType": "int"},
            "text": {"bsonType": ["string", "null"]},
            "created_at": {"bsonType": "date"}
        }
    }
}

# ----- Utility functions -----
def now():
    return datetime.now(timezone.utc)

async def safe_create_collection(db, name, validator=None):
    existing = await db.list_collection_names()
    if name in existing:
        print(f"Collection '{name}' already exists — skipping create.")
        # If validator exists and you want to update it, you'd use collMod (not done here)
        return db[name]
    try:
        if validator:
            coll = await db.create_collection(name, validator=validator)
        else:
            coll = await db.create_collection(name)
        print(f"Created collection '{name}'.")
        return coll
    except Exception as e:
        print(f"Could not create collection '{name}': {e}")
        return db[name]

# ----- Main script -----
async def main():
    client = AsyncIOMotorClient(MONGO_URI)
    if DROP_DB:
        await client.drop_database(DB_NAME)
        print(f"Dropped database '{DB_NAME}'")

    db = client[DB_NAME]

    # Create collections with validators
    await safe_create_collection(db, "niches", NICHES_VALIDATOR)
    await safe_create_collection(db, "users", USERS_VALIDATOR)
    await safe_create_collection(db, "posts", POSTS_VALIDATOR)
    await safe_create_collection(db, "reviews", REVIEWS_VALIDATOR)

    # Create indexes
    try:
        await db["niches"].create_index("slug", unique=True)
        await db["users"].create_index("email", unique=True)
        await db["posts"].create_index([("niche_id", 1), ("combined_rating.score", -1), ("created_at", -1)])
        await db["posts"].create_index([("founder_id", 1), ("created_at", -1)])
        await db["reviews"].create_index([("post_id", 1), ("created_at", -1)])
        print("Indexes created.")
    except Exception as e:
        print("Index creation error:", e)

    # Insert sample data only if empty
    niche_count = await db["niches"].count_documents({})
    if niche_count == 0:
        niche_docs = [
            {"slug": "tech", "name": "Technology", "description": "Hardware, software, AI", "created_at": now()},
            {"slug": "health", "name": "Health", "description": "Healthcare & biotech", "created_at": now()},
            {"slug": "edu", "name": "Education", "description": "EdTech and learning", "created_at": now()}
        ]
        res = await db["niches"].insert_many(niche_docs)
        print("Inserted niches:", res.inserted_ids)
    else:
        print("Niches already present, skipping seed.")

    # Insert sample users if none
    user_count = await db["users"].count_documents({})
    if user_count == 0:
        # get a niche id to set as main_niche
        tech_niche = await db["niches"].find_one({"slug": "tech"})
        tech_id = tech_niche["_id"]

        founder = {
            "username": "alice_founder",
            "email": "alice@example.com",
            "role": "founder",
            "profile": {"bio": "Tech entrepreneur", "joined_at": now(), "main_niche": tech_id},
            "niche_stats": {},  # empty, will be populated by events
            "posts": [],
            "liked_posts": [],
            "created_at": now()
        }
        funder = {
            "username": "bob_funder",
            "email": "bob@example.com",
            "role": "funder",
            "profile": {"bio": "Investor", "joined_at": now(), "main_niche": tech_id},
            "created_at": now()
        }
        r = await db["users"].insert_many([founder, funder])
        print("Inserted sample users:", r.inserted_ids)
        founder_id = r.inserted_ids[0]
        funder_id = r.inserted_ids[1]
    else:
        print("Users already present, skipping seed.")
        founder = await db["users"].find_one({"role": "founder"})
        founder_id = founder["_id"]

    # Insert a sample post if none
    post_count = await db["posts"].count_documents({})
    if post_count == 0:
        # pick a niche id
        tech = await db["niches"].find_one({"slug": "tech"})
        tech_id = tech["_id"]

        sample_post = {
            "founder_id": founder_id,
            "title": "Revolutionary AI Startup",
            "description": "This AI will change the world...",
            "niche_id": tech_id,
            "media": {
                "images": ["https://example.com/img1.jpg"],
                "youtube_links": ["https://youtu.be/dQw4w9WgXcQ"]
            },
            "gemini_rating": {"score": 4.2, "scale": 5, "computed_at": now(), "explain": "Good novelty and feasibility."},
            "user_rating": {"total_score": 0, "count": 0, "avg": 0.0},
            "combined_rating": {"score": 8.4, "scale": 10, "computed_at": now()},
            "likes_count": 0,
            "comments_count": 0,
            "views_count": 0,
            "created_at": now()
        }
        p = await db["posts"].insert_one(sample_post)
        post_id = p.inserted_id
        # push post id to founder.posts
        await db["users"].update_one({"_id": founder_id}, {"$push": {"posts": post_id}})
        print("Inserted sample post:", post_id)
    else:
        print("Posts already present, skipping seed.")

    # Print final DB summary
    print("\n--- DB Summary ---")
    cols = await db.list_collection_names()
    print("Collections:", cols)
    for c in cols:
        cnt = await db[c].count_documents({})
        print(f" - {c}: {cnt} docs")
    print("------------------")

    # Print example documents
    example_niche = await db["niches"].find_one({}, projection={"slug": 1, "name": 1})
    print("Example niche:", example_niche)
    example_user = await db["users"].find_one({}, projection={"username": 1, "email": 1, "role": 1, "posts": 1})
    print("Example user:", example_user)
    example_post = await db["posts"].find_one({}, projection={"title": 1, "niche_id": 1, "combined_rating": 1, "media": 1})
    print("Example post:", example_post)

    client.close()

if __name__ == "__main__":
    asyncio.run(main())
