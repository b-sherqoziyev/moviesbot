import json

async def load_message_store(conn, message_store):
    rows = await conn.fetch("SELECT * FROM message_store")
    message_store.update({
        row["movie_code"]: {
            "message_id": row["message_id"],
            "video": row["video"],
            "document": row["document"],
            "caption": row["caption"],
            "name": row["name"],
            "views": row["views"]
        } for row in rows
    })

async def load_users(conn, users):
    rows = await conn.fetch("SELECT user_id, data FROM users")
    users.update({row["user_id"]: json.loads(row["data"]) for row in rows})

async def load_channels(conn, channels):
    rows = await conn.fetch("SELECT channel_id, channel_username FROM channels")
    channels[:] = [(row['channel_id'], f"https://t.me/{row['channel_username']}") for row in rows]

async def save_message_store(conn, movie_code, data):
    await conn.execute("""
        INSERT INTO message_store (movie_code, message_id, video, document, caption, name, views)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (movie_code) DO UPDATE 
        SET message_id = EXCLUDED.message_id,
            video = EXCLUDED.video,
            document = EXCLUDED.document,
            caption = EXCLUDED.caption,
            name = EXCLUDED.name,
            views = EXCLUDED.views
    """, movie_code, data["message_id"], data["video"], data["document"],
                       data["caption"], data["name"], data["views"])

async def save_user(conn, user_id, user_data):
    await conn.execute("""
        INSERT INTO users (user_id, data) 
        VALUES ($1, $2)
        ON CONFLICT (user_id) 
        DO UPDATE SET data = EXCLUDED.data
    """, user_id, json.dumps(user_data))