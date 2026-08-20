import time
import aiosqlite

DB_PATH = "data.sqlite"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            cash INTEGER DEFAULT 0,
            bank INTEGER DEFAULT 0,
            last_cash_change INTEGER DEFAULT 0,
            last_deposit INTEGER DEFAULT 0
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS cooldowns (
            user_id INTEGER,
            command TEXT,
            last_used INTEGER,
            PRIMARY KEY(user_id, command)
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER PRIMARY KEY,
            color TEXT DEFAULT '#5865F2',
            gif_url TEXT DEFAULT '',
            video_url TEXT DEFAULT '',
            title TEXT DEFAULT 'Joueur QLF',
            equipped_item TEXT DEFAULT '',
            frame TEXT DEFAULT 'Cadre QLF classique'
        )
        """)
        try:
            await db.execute("ALTER TABLE profiles ADD COLUMN title TEXT DEFAULT 'Joueur QLF'")
        except aiosqlite.OperationalError:
            pass
        try:
            await db.execute("ALTER TABLE profiles ADD COLUMN video_url TEXT DEFAULT ''")
        except aiosqlite.OperationalError:
            pass
        try:
            await db.execute("ALTER TABLE profiles ADD COLUMN equipped_item TEXT DEFAULT ''")
        except aiosqlite.OperationalError:
            pass
        try:
            await db.execute("ALTER TABLE profiles ADD COLUMN frame TEXT DEFAULT 'Cadre QLF classique'")
        except aiosqlite.OperationalError:
            pass
        await db.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            user_id INTEGER,
            item_id TEXT,
            PRIMARY KEY(user_id, item_id)
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            user_id INTEGER PRIMARY KEY,
            total_gains INTEGER DEFAULT 0,
            total_losses INTEGER DEFAULT 0,
            biggest_gain INTEGER DEFAULT 0,
            steals_success INTEGER DEFAULT 0,
            steals_failed INTEGER DEFAULT 0,
            crimes_success INTEGER DEFAULT 0,
            crimes_failed INTEGER DEFAULT 0
        )
        """)
        await db.commit()

async def ensure_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        row = await cur.fetchone()
        if not row:
            await db.execute("INSERT INTO users(id, cash, bank, last_cash_change, last_deposit) VALUES(?,?,?,?,?)", (user_id, 0, 0, 0, 0))
            await db.commit()

async def get_user(user_id: int):
    await ensure_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT cash, bank, last_cash_change, last_deposit FROM users WHERE id = ?", (user_id,))
        row = await cur.fetchone()
        if row:
            return {"cash": row[0], "bank": row[1], "last_cash_change": row[2], "last_deposit": row[3]}
        return {"cash": 0, "bank": 0, "last_cash_change": 0, "last_deposit": 0}

async def get_profile(user_id: int):
    await ensure_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO profiles(user_id) VALUES(?)", (user_id,))
        await db.commit()
        cur = await db.execute("SELECT color, gif_url, video_url, title, equipped_item, frame FROM profiles WHERE user_id = ?", (user_id,))
        color, gif_url, video_url, title, equipped_item, frame = await cur.fetchone()
        return {"color": color, "gif_url": gif_url, "video_url": video_url, "title": title, "equipped_item": equipped_item, "frame": frame}

async def set_custom_video(user_id: int, video_url: str):
    await ensure_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO profiles(user_id) VALUES(?)", (user_id,))
        await db.execute("UPDATE profiles SET video_url = ? WHERE user_id = ?", (video_url, user_id))
        await db.commit()

async def set_custom_gif(user_id: int, gif_url: str):
    await ensure_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO profiles(user_id) VALUES(?)", (user_id,))
        await db.execute("UPDATE profiles SET gif_url = ? WHERE user_id = ?", (gif_url, user_id))
        await db.commit()

async def get_stats(user_id: int):
    await ensure_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO stats(user_id) VALUES(?)", (user_id,))
        await db.commit()
        cur = await db.execute("SELECT total_gains, total_losses, biggest_gain, steals_success, steals_failed, crimes_success, crimes_failed FROM stats WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        return {
            'total_gains': row[0], 'total_losses': row[1], 'biggest_gain': row[2],
            'steals_success': row[3], 'steals_failed': row[4],
            'crimes_success': row[5], 'crimes_failed': row[6],
        }

async def record_gain(user_id: int, amount: int):
    if amount <= 0:
        return
    await ensure_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO stats(user_id) VALUES(?)", (user_id,))
        await db.execute("UPDATE stats SET total_gains = total_gains + ?, biggest_gain = MAX(biggest_gain, ?) WHERE user_id = ?", (amount, amount, user_id))
        await db.commit()

async def record_loss(user_id: int, amount: int):
    if amount <= 0:
        return
    await ensure_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO stats(user_id) VALUES(?)", (user_id,))
        await db.execute("UPDATE stats SET total_losses = total_losses + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

async def record_activity(user_id: int, activity: str, success: bool):
    columns = {
        ('steal', True): 'steals_success', ('steal', False): 'steals_failed',
        ('crime', True): 'crimes_success', ('crime', False): 'crimes_failed',
    }
    column = columns.get((activity, success))
    if not column:
        return
    await ensure_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO stats(user_id) VALUES(?)", (user_id,))
        await db.execute(f"UPDATE stats SET {column} = {column} + 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def buy_item(user_id: int, item_id: str, price: int):
    await ensure_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT 1 FROM inventory WHERE user_id = ? AND item_id = ?", (user_id, item_id))
        if await cur.fetchone():
            return "owned"
        cur = await db.execute("UPDATE users SET cash = cash - ?, last_cash_change = ? WHERE id = ? AND cash >= ?", (price, int(time.time()), user_id, price))
        if cur.rowcount != 1:
            return "insufficient"
        await db.execute("INSERT INTO inventory(user_id, item_id) VALUES(?, ?)", (user_id, item_id))
        await db.commit()
        return "bought"

async def equip_item(user_id: int, item_id: str, color: str, gif_url: str = "", title: str = "Joueur QLF", frame: str = "Cadre QLF classique"):
    await ensure_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT 1 FROM inventory WHERE user_id = ? AND item_id = ?", (user_id, item_id))
        if not await cur.fetchone():
            return False
        await db.execute("INSERT OR IGNORE INTO profiles(user_id) VALUES(?)", (user_id,))
        await db.execute("UPDATE profiles SET color = ?, gif_url = ?, title = ?, equipped_item = ?, frame = ? WHERE user_id = ?", (color, gif_url, title, item_id, frame, user_id))
        await db.commit()
        return True

async def get_inventory(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT item_id FROM inventory WHERE user_id = ? ORDER BY item_id", (user_id,))
        return [row[0] for row in await cur.fetchall()]

async def change_cash(user_id: int, delta: int):
    await ensure_user(user_id)
    ts = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET cash = cash + ?, last_cash_change = ? WHERE id = ?", (delta, ts, user_id))
        await db.commit()

async def remove_cash(user_id: int, amount: int):
    await ensure_user(user_id)
    ts = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("UPDATE users SET cash = cash - ?, last_cash_change = ? WHERE id = ? AND cash >= ?", (amount, ts, user_id, amount))
        await db.commit()
        return cur.rowcount == 1

async def get_balances(user_ids):
    if not user_ids:
        return []
    placeholders = ",".join("?" for _ in user_ids)
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(f"SELECT id, cash, bank FROM users WHERE id IN ({placeholders})", tuple(user_ids))
        return await cur.fetchall()

async def transfer_cash(sender_id: int, recipient_id: int, amount: int):
    await ensure_user(sender_id)
    await ensure_user(recipient_id)
    ts = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("UPDATE users SET cash = cash - ?, last_cash_change = ? WHERE id = ? AND cash >= ?", (amount, ts, sender_id, amount))
        if cur.rowcount != 1:
            return False
        await db.execute("UPDATE users SET cash = cash + ?, last_cash_change = ? WHERE id = ?", (amount, ts, recipient_id))
        await db.commit()
        return True

async def deposit_all(user_id: int):
    await ensure_user(user_id)
    ts = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT cash FROM users WHERE id = ?", (user_id,))
        cash = (await cur.fetchone())[0]
        if cash <= 0:
            return 0
        await db.execute("UPDATE users SET cash = 0, bank = bank + ?, last_deposit = ?, last_cash_change = ? WHERE id = ?", (cash, ts, ts, user_id))
        await db.commit()
        return cash

async def deposit(user_id: int, amount: int):
    await ensure_user(user_id)
    ts = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("UPDATE users SET cash = cash - ?, bank = bank + ?, last_deposit = ?, last_cash_change = ? WHERE id = ? AND cash >= ?", (amount, amount, ts, ts, user_id, amount))
        await db.commit()
        return amount if cur.rowcount == 1 else 0

async def withdraw(user_id: int, amount: int):
    await ensure_user(user_id)
    ts = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT bank FROM users WHERE id = ?", (user_id,))
        bank = (await cur.fetchone())[0]
        if amount <= 0 or amount > bank:
            return 0
        await db.execute("UPDATE users SET bank = bank - ?, cash = cash + ?, last_cash_change = ? WHERE id = ?", (amount, amount, ts, user_id))
        await db.commit()
        return amount

async def set_cooldown(user_id: int, command: str):
    ts = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("REPLACE INTO cooldowns(user_id, command, last_used) VALUES(?,?,?)", (user_id, command, ts))
        await db.commit()

async def get_cooldown(user_id: int, command: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT last_used FROM cooldowns WHERE user_id = ? AND command = ?", (user_id, command))
        row = await cur.fetchone()
        return row[0] if row else 0
