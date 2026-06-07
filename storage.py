"""SQLite-based storage for users, conversations, and stats."""
import aiosqlite
import time
from typing import Optional
from config import DATABASE_PATH


async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT,
                is_blocked INTEGER DEFAULT 0,
                created_at INTEGER,
                last_seen INTEGER,
                message_count INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT,
                content TEXT,
                tool_used TEXT,
                created_at INTEGER
            );
            CREATE TABLE IF NOT EXISTS tool_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                tool_name TEXT,
                created_at INTEGER
            );
            CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id);
            CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);
        """)
        await db.commit()


async def upsert_user(user):
    now = int(time.time())
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, language_code, created_at, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                last_name=excluded.last_name,
                language_code=excluded.language_code,
                last_seen=excluded.last_seen
        """, (user.id, user.username, user.first_name, user.last_name,
              user.language_code, now, now))
        await db.commit()


async def is_blocked(user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT is_blocked FROM users WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return bool(row and row[0])


async def set_blocked(user_id: int, blocked: bool):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE users SET is_blocked=? WHERE user_id=?",
                         (1 if blocked else 0, user_id))
        await db.commit()


async def log_message(user_id: int, role: str, content: str, tool_used: Optional[str] = None):
    now = int(time.time())
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO messages (user_id, role, content, tool_used, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, role, content, tool_used, now))
        if role == "user":
            await db.execute(
                "UPDATE users SET message_count = message_count + 1, last_seen=? WHERE user_id=?",
                (now, user_id))
        await db.commit()


async def log_tool(user_id: int, tool_name: str):
    now = int(time.time())
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO tool_usage (user_id, tool_name, created_at) VALUES (?, ?, ?)",
            (user_id, tool_name, now))
        await db.commit()


async def get_history(user_id: int, limit: int = 20):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT role, content FROM messages
            WHERE user_id=? AND role IN ('user', 'assistant')
            ORDER BY id DESC LIMIT ?
        """, (user_id, limit)) as cur:
            rows = await cur.fetchall()
            return list(reversed(rows))


async def get_stats():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        stats = {}
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            stats["total_users"] = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_blocked=1") as cur:
            stats["blocked_users"] = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM messages") as cur:
            stats["total_messages"] = (await cur.fetchone())[0]
        day_ago = int(time.time()) - 86400
        async with db.execute("SELECT COUNT(DISTINCT user_id) FROM messages WHERE created_at>?", (day_ago,)) as cur:
            stats["active_24h"] = (await cur.fetchone())[0]
        async with db.execute("""
            SELECT tool_name, COUNT(*) c FROM tool_usage
            GROUP BY tool_name ORDER BY c DESC LIMIT 10
        """) as cur:
            stats["top_tools"] = [{"name": r[0], "count": r[1]} for r in await cur.fetchall()]
        return stats


async def list_users(limit: int = 100):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT user_id, username, first_name, last_name, message_count, is_blocked, last_seen
            FROM users ORDER BY last_seen DESC LIMIT ?
        """, (limit,)) as cur:
            rows = await cur.fetchall()
            return [{
                "user_id": r[0], "username": r[1], "first_name": r[2],
                "last_name": r[3], "message_count": r[4],
                "is_blocked": bool(r[5]), "last_seen": r[6],
            } for r in rows]


async def recent_messages(limit: int = 50):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT m.user_id, u.first_name, u.username, m.role, m.content, m.tool_used, m.created_at
            FROM messages m LEFT JOIN users u ON u.user_id = m.user_id
            ORDER BY m.id DESC LIMIT ?
        """, (limit,)) as cur:
            rows = await cur.fetchall()
            return [{
                "user_id": r[0], "first_name": r[1], "username": r[2],
                "role": r[3], "content": r[4], "tool_used": r[5],
                "created_at": r[6],
            } for r in rows]
