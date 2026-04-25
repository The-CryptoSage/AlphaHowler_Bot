"""
╔══════════════════════════════════════════╗
║            🐺 HOWLER BOT                 ║
║   Contests | Polls | Moderation | Fun    ║
║         @AlphaHowler_Bot                 ║
╚══════════════════════════════════════════╝
100% Free | SQLite | python-telegram-bot
"""

import logging
import sqlite3
import random
import asyncio
from datetime import datetime, timedelta
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ChatPermissions, Poll
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, PollAnswerHandler
)
from telegram.constants import ParseMode

# ─────────────────────────────────────────
#  CONFIG — edit these
# ─────────────────────────────────────────
BOT_TOKEN = "7681018300:AAEtldaxe5hyzQVXWmB8rF_HIAgr75BJ0d4"
ADMIN_IDS = [922946885]

# ─────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
#  DATABASE SETUP
# ─────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("community.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS contests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        title TEXT,
        description TEXT,
        prize TEXT,
        end_time TEXT,
        winner_id INTEGER,
        status TEXT DEFAULT 'active'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS contest_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contest_id INTEGER,
        user_id INTEGER,
        username TEXT,
        full_name TEXT,
        joined_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS polls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        poll_id TEXT,
        question TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS warnings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        user_id INTEGER,
        username TEXT,
        reason TEXT,
        warned_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS points (
        user_id INTEGER,
        chat_id INTEGER,
        username TEXT,
        full_name TEXT,
        points INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, chat_id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS welcome_messages (
        chat_id INTEGER PRIMARY KEY,
        message TEXT
    )""")

    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect("community.db")

# ─────────────────────────────────────────
#  HELPER FUNCTIONS
# ─────────────────────────────────────────
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def is_chat_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if is_admin(user_id):
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False

def add_points(user_id, chat_id, username, full_name, pts):
    db = get_db()
    c = db.cursor()
    c.execute("""INSERT INTO points (user_id, chat_id, username, full_name, points)
                 VALUES (?, ?, ?, ?, ?)
                 ON CONFLICT(user_id, chat_id) DO UPDATE SET
                 points = points + ?, username = ?, full_name = ?""",
              (user_id, chat_id, username, full_name, pts, pts, username, full_name))
    db.commit()
    db.close()

def get_points(user_id, chat_id):
    db = get_db()
    c = db.cursor()
    c.execute("SELECT points FROM points WHERE user_id=? AND chat_id=?", (user_id, chat_id))
    row = c.fetchone()
    db.close()
    return row[0] if row else 0

# ─────────────────────────────────────────
#  /start  /help
# ─────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🐺 *Welcome to HOWLER!*\n\n"
        "Your ultimate community wolf pack manager.\n\n"
        "🏆 *Contests* — create & pick winners\n"
        "📊 *Polls* — quick votes & quizzes\n"
        "⭐ *Points* — reward active members\n"
        "🛡️ *Moderation* — warn, mute, kick\n"
        "🎉 *Fun* — dice, trivia, giveaways\n\n"
        "Use /help to see all commands.\n"
        "_@AlphaHowler\\_Bot_"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *ALL COMMANDS*\n\n"
        "━━━━ 🏆 CONTESTS ━━━━\n"
        "/contest `title | prize | hours` — Start a contest\n"
        "/joincontest `ID` — Join a contest\n"
        "/endcontest `ID` — Pick winner & end\n"
        "/contests — List active contests\n\n"
        "━━━━ 📊 POLLS ━━━━\n"
        "/poll `Question | A | B | C` — Quick poll\n"
        "/quiz `Question | Correct | Wrong1 | Wrong2` — Quiz poll\n"
        "/yesno `Question` — Yes/No poll\n\n"
        "━━━━ ⭐ POINTS ━━━━\n"
        "/points — Your points\n"
        "/leaderboard — Top 10 members\n"
        "/givepoints `@user amount` — Give points (admin)\n\n"
        "━━━━ 🛡️ MODERATION ━━━━\n"
        "/warn `@user reason` — Warn user\n"
        "/warnings `@user` — Check warnings\n"
        "/mute `@user minutes` — Mute user\n"
        "/unmute `@user` — Unmute user\n"
        "/kick `@user` — Kick user\n"
        "/ban `@user` — Ban user\n"
        "/unban `@user` — Unban user\n"
        "/purge `N` — Delete last N messages\n\n"
        "━━━━ 🎉 FUN ━━━━\n"
        "/giveaway `prize | hours` — Start giveaway\n"
        "/roll — Roll a dice 🎲\n"
        "/flip — Flip a coin 🪙\n"
        "/trivia — Random trivia question\n"
        "/pick `A | B | C` — Pick randomly\n\n"
        "━━━━ ⚙️ SETTINGS ━━━━\n"
        "/setwelcome `message` — Set welcome msg\n"
        "/rules — Show group rules\n"
        "/setrules `rules text` — Set rules\n"
        "/stats — Group statistics\n"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ─────────────────────────────────────────
#  CONTESTS
# ─────────────────────────────────────────
async def contest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return await update.message.reply_text("❌ Admins only.")

    args = " ".join(context.args)
    parts = [p.strip() for p in args.split("|")]
    if len(parts) < 3:
        return await update.message.reply_text(
            "Usage: /contest `Title | Prize | Hours`\n"
            "Example: /contest Best Meme | ⭐100 Points | 24",
            parse_mode=ParseMode.MARKDOWN
        )

    title, prize, hours_str = parts[0], parts[1], parts[2]
    try:
        hours = float(hours_str)
    except:
        return await update.message.reply_text("❌ Hours must be a number.")

    end_time = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    chat_id = update.effective_chat.id

    db = get_db()
    c = db.cursor()
    c.execute(
        "INSERT INTO contests (chat_id, title, prize, end_time) VALUES (?,?,?,?)",
        (chat_id, title, prize, end_time)
    )
    contest_id = c.lastrowid
    db.commit()
    db.close()

    keyboard = [[InlineKeyboardButton(f"🏆 Join Contest #{contest_id}", callback_data=f"join_{contest_id}")]]
    text = (
        f"🏆 *NEW CONTEST!*\n\n"
        f"📌 *{title}*\n"
        f"🎁 Prize: {prize}\n"
        f"⏰ Ends in: {hours}h\n"
        f"🆔 ID: #{contest_id}\n\n"
        f"Tap below to enter!"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN,
                                    reply_markup=InlineKeyboardMarkup(keyboard))

async def contests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db = get_db()
    c = db.cursor()
    c.execute("SELECT id, title, prize, end_time FROM contests WHERE chat_id=? AND status='active'", (chat_id,))
    rows = c.fetchall()
    db.close()

    if not rows:
        return await update.message.reply_text("No active contests right now.")

    text = "🏆 *ACTIVE CONTESTS*\n\n"
    for r in rows:
        text += f"#{r[0]} — *{r[1]}*\nPrize: {r[2]} | Ends: {r[3]}\n\n"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def join_contest_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    contest_id = int(query.data.split("_")[1])
    user = query.from_user
    chat_id = query.message.chat_id

    db = get_db()
    c = db.cursor()

    # Check contest active
    c.execute("SELECT status FROM contests WHERE id=?", (contest_id,))
    row = c.fetchone()
    if not row or row[0] != "active":
        db.close()
        return await query.answer("❌ This contest is no longer active.", show_alert=True)

    # Check already joined
    c.execute("SELECT id FROM contest_entries WHERE contest_id=? AND user_id=?", (contest_id, user.id))
    if c.fetchone():
        db.close()
        return await query.answer("✅ You already joined!", show_alert=True)

    c.execute(
        "INSERT INTO contest_entries (contest_id, user_id, username, full_name, joined_at) VALUES (?,?,?,?,?)",
        (contest_id, user.id, user.username or "", user.full_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    db.commit()

    # Count entries
    c.execute("SELECT COUNT(*) FROM contest_entries WHERE contest_id=?", (contest_id,))
    count = c.fetchone()[0]
    db.close()

    # Give points for joining
    add_points(user.id, chat_id, user.username or "", user.full_name, 5)

    await query.answer(f"🎉 You joined! {count} participants so far.", show_alert=True)

async def endcontest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return await update.message.reply_text("❌ Admins only.")

    if not context.args:
        return await update.message.reply_text("Usage: /endcontest ID")

    contest_id = int(context.args[0])
    db = get_db()
    c = db.cursor()

    c.execute("SELECT title, prize FROM contests WHERE id=? AND status='active'", (contest_id,))
    contest_row = c.fetchone()
    if not contest_row:
        db.close()
        return await update.message.reply_text("❌ Contest not found or already ended.")

    c.execute("SELECT user_id, username, full_name FROM contest_entries WHERE contest_id=?", (contest_id,))
    entries = c.fetchall()

    if not entries:
        db.close()
        return await update.message.reply_text("😔 No participants in this contest.")

    winner = random.choice(entries)
    winner_id, winner_username, winner_name = winner

    c.execute("UPDATE contests SET status='ended', winner_id=? WHERE id=?", (winner_id, contest_id))
    db.commit()
    db.close()

    # Give winner big points
    add_points(winner_id, update.effective_chat.id, winner_username, winner_name, 100)

    mention = f"@{winner_username}" if winner_username else winner_name
    text = (
        f"🎊 *CONTEST ENDED!*\n\n"
        f"🏆 Contest: *{contest_row[0]}*\n"
        f"🎁 Prize: {contest_row[1]}\n"
        f"👥 Participants: {len(entries)}\n\n"
        f"🥇 *WINNER: {mention}*\n\n"
        f"Congratulations! 🎉 +100 points awarded!"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def joincontest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual join via command"""
    if not context.args:
        return await update.message.reply_text("Usage: /joincontest ID")
    contest_id = int(context.args[0])
    user = update.effective_user
    chat_id = update.effective_chat.id

    db = get_db()
    c = db.cursor()
    c.execute("SELECT status FROM contests WHERE id=?", (contest_id,))
    row = c.fetchone()
    if not row or row[0] != "active":
        db.close()
        return await update.message.reply_text("❌ Contest not found or ended.")
    c.execute("SELECT id FROM contest_entries WHERE contest_id=? AND user_id=?", (contest_id, user.id))
    if c.fetchone():
        db.close()
        return await update.message.reply_text("✅ You already joined this contest!")
    c.execute(
        "INSERT INTO contest_entries (contest_id, user_id, username, full_name, joined_at) VALUES (?,?,?,?,?)",
        (contest_id, user.id, user.username or "", user.full_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    db.commit()
    db.close()
    add_points(user.id, chat_id, user.username or "", user.full_name, 5)
    await update.message.reply_text(f"🎉 You joined contest #{contest_id}! Good luck!")

# ─────────────────────────────────────────
#  POLLS
# ─────────────────────────────────────────
async def poll_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = " ".join(context.args)
    parts = [p.strip() for p in args.split("|")]
    if len(parts) < 3:
        return await update.message.reply_text(
            "Usage: /poll Question | Option1 | Option2 | ...\n"
            "Example: /poll Favorite color? | Red | Blue | Green"
        )
    question, options = parts[0], parts[1:]
    await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=question,
        options=options,
        is_anonymous=False,
        allows_multiple_answers=False
    )

async def quiz_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = " ".join(context.args)
    parts = [p.strip() for p in args.split("|")]
    if len(parts) < 3:
        return await update.message.reply_text(
            "Usage: /quiz Question | CorrectAnswer | Wrong1 | Wrong2\n"
            "First option after question = correct answer"
        )
    question = parts[0]
    correct = parts[1]
    wrongs = parts[2:]
    options = [correct] + wrongs
    random.shuffle(options)
    correct_idx = options.index(correct)

    await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=question,
        options=options,
        type=Poll.QUIZ,
        correct_option_id=correct_idx,
        is_anonymous=False
    )

async def yesno_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = " ".join(context.args)
    if not question:
        return await update.message.reply_text("Usage: /yesno Your question here")
    await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=question,
        options=["✅ Yes", "❌ No", "🤔 Maybe"],
        is_anonymous=False
    )

# ─────────────────────────────────────────
#  POINTS & LEADERBOARD
# ─────────────────────────────────────────
async def points_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pts = get_points(user.id, update.effective_chat.id)
    await update.message.reply_text(
        f"⭐ *{user.full_name}'s Points*\n\nYou have *{pts}* points!\n\n"
        f"Earn points by:\n• Joining contests (+5)\n• Winning contests (+100)\n• Active chatting (+1)",
        parse_mode=ParseMode.MARKDOWN
    )

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db = get_db()
    c = db.cursor()
    c.execute(
        "SELECT full_name, username, points FROM points WHERE chat_id=? ORDER BY points DESC LIMIT 10",
        (chat_id,)
    )
    rows = c.fetchall()
    db.close()

    if not rows:
        return await update.message.reply_text("No points data yet.")

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    text = "🏆 *LEADERBOARD*\n\n"
    for i, (name, username, pts) in enumerate(rows):
        display = f"@{username}" if username else name
        text += f"{medals[i]} {display} — *{pts} pts*\n"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def givepoints(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return await update.message.reply_text("❌ Admins only.")
    if not update.message.reply_to_message or not context.args:
        return await update.message.reply_text("Reply to a user and use: /givepoints 50")
    try:
        pts = int(context.args[0])
    except:
        return await update.message.reply_text("❌ Amount must be a number.")
    target = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id
    add_points(target.id, chat_id, target.username or "", target.full_name, pts)
    await update.message.reply_text(f"⭐ Gave *{pts}* points to {target.full_name}!", parse_mode=ParseMode.MARKDOWN)

# ─────────────────────────────────────────
#  MODERATION
# ─────────────────────────────────────────
async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return await update.message.reply_text("❌ Admins only.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("Reply to a user to warn them.")

    target = update.message.reply_to_message.from_user
    reason = " ".join(context.args) or "No reason given"
    chat_id = update.effective_chat.id

    db = get_db()
    c = db.cursor()
    c.execute(
        "INSERT INTO warnings (chat_id, user_id, username, reason, warned_at) VALUES (?,?,?,?,?)",
        (chat_id, target.id, target.username or "", reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    db.commit()
    c.execute("SELECT COUNT(*) FROM warnings WHERE chat_id=? AND user_id=?", (chat_id, target.id))
    count = c.fetchone()[0]
    db.close()

    text = (
        f"⚠️ *WARNING #{count}*\n\n"
        f"User: {target.full_name}\n"
        f"Reason: {reason}\n\n"
    )
    if count >= 3:
        text += "🚫 *3 warnings reached — consider a ban!*"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def warnings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    else:
        target = update.effective_user
    chat_id = update.effective_chat.id
    db = get_db()
    c = db.cursor()
    c.execute("SELECT reason, warned_at FROM warnings WHERE chat_id=? AND user_id=?", (chat_id, target.id))
    rows = c.fetchall()
    db.close()
    if not rows:
        return await update.message.reply_text(f"✅ {target.full_name} has no warnings.")
    text = f"⚠️ *{target.full_name}'s Warnings ({len(rows)})*\n\n"
    for i, (reason, dt) in enumerate(rows, 1):
        text += f"{i}. {reason} — _{dt}_\n"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return await update.message.reply_text("❌ Admins only.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("Reply to a user to mute them.")
    target = update.message.reply_to_message.from_user
    minutes = int(context.args[0]) if context.args else 10
    until = datetime.now() + timedelta(minutes=minutes)
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id, target.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until
        )
        await update.message.reply_text(f"🔇 {target.full_name} muted for {minutes} minute(s).")
    except Exception as e:
        await update.message.reply_text(f"❌ Could not mute: {e}")

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return await update.message.reply_text("❌ Admins only.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("Reply to a user to unmute.")
    target = update.message.reply_to_message.from_user
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id, target.id,
            permissions=ChatPermissions(
                can_send_messages=True, can_send_media_messages=True,
                can_send_polls=True, can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await update.message.reply_text(f"🔊 {target.full_name} unmuted.")
    except Exception as e:
        await update.message.reply_text(f"❌ Could not unmute: {e}")

async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return await update.message.reply_text("❌ Admins only.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("Reply to a user to kick.")
    target = update.message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await context.bot.unban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(f"👢 {target.full_name} was kicked.")
    except Exception as e:
        await update.message.reply_text(f"❌ Could not kick: {e}")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return await update.message.reply_text("❌ Admins only.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("Reply to a user to ban.")
    target = update.message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(f"🚫 {target.full_name} was banned.")
    except Exception as e:
        await update.message.reply_text(f"❌ Could not ban: {e}")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return await update.message.reply_text("❌ Admins only.")
    if not context.args:
        return await update.message.reply_text("Usage: /unban user_id")
    try:
        await context.bot.unban_chat_member(update.effective_chat.id, int(context.args[0]))
        await update.message.reply_text("✅ User unbanned.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def purge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return await update.message.reply_text("❌ Admins only.")
    n = int(context.args[0]) if context.args else 5
    n = min(n, 100)  # cap at 100
    chat_id = update.effective_chat.id
    msg_id = update.message.message_id
    deleted = 0
    for i in range(msg_id, msg_id - n - 1, -1):
        try:
            await context.bot.delete_message(chat_id, i)
            deleted += 1
        except:
            pass
    confirm = await update.message.reply_text(f"🗑️ Deleted {deleted} messages.")
    await asyncio.sleep(3)
    try:
        await confirm.delete()
    except:
        pass

# ─────────────────────────────────────────
#  GIVEAWAY
# ─────────────────────────────────────────
async def giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return await update.message.reply_text("❌ Admins only.")
    args = " ".join(context.args)
    parts = [p.strip() for p in args.split("|")]
    if len(parts) < 2:
        return await update.message.reply_text("Usage: /giveaway Prize | Hours")
    prize, hours_str = parts[0], parts[1]
    try:
        hours = float(hours_str)
    except:
        return await update.message.reply_text("❌ Hours must be a number.")

    end_time = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    chat_id = update.effective_chat.id

    db = get_db()
    c = db.cursor()
    c.execute(
        "INSERT INTO contests (chat_id, title, prize, end_time) VALUES (?,?,?,?)",
        (chat_id, "🎁 GIVEAWAY", prize, end_time)
    )
    giveaway_id = c.lastrowid
    db.commit()
    db.close()

    keyboard = [[InlineKeyboardButton("🎁 Enter Giveaway!", callback_data=f"join_{giveaway_id}")]]
    text = (
        f"🎊 *GIVEAWAY TIME!*\n\n"
        f"🎁 *Prize:* {prize}\n"
        f"⏰ *Ends in:* {hours}h\n\n"
        f"Click below to enter!\n"
        f"Winner picked randomly when time ends.\n"
        f"_(Admin uses /endcontest {giveaway_id} to draw winner)_"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN,
                                    reply_markup=InlineKeyboardMarkup(keyboard))

# ─────────────────────────────────────────
#  FUN COMMANDS
# ─────────────────────────────────────────
async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    n = random.randint(1, 6)
    dice_faces = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
    await update.message.reply_text(f"🎲 You rolled: *{dice_faces[n]} {n}*", parse_mode=ParseMode.MARKDOWN)
    add_points(update.effective_user.id, update.effective_chat.id,
               update.effective_user.username or "", update.effective_user.full_name, 1)

async def flip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = random.choice(["🪙 Heads!", "🪙 Tails!"])
    await update.message.reply_text(f"Flipping... {result}")

TRIVIA = [
    ("What is the capital of France?", "Paris"),
    ("How many legs does a spider have?", "8"),
    ("What planet is closest to the Sun?", "Mercury"),
    ("Who wrote Romeo and Juliet?", "Shakespeare"),
    ("What is 7 × 8?", "56"),
    ("What gas do plants absorb?", "Carbon dioxide / CO2"),
    ("How many colors in a rainbow?", "7"),
    ("What is the fastest land animal?", "Cheetah"),
]

async def trivia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q, a = random.choice(TRIVIA)
    keyboard = [[InlineKeyboardButton("💡 Show Answer", callback_data=f"trivia_{a}")]]
    await update.message.reply_text(
        f"🧠 *TRIVIA TIME!*\n\n{q}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def trivia_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    answer = query.data.split("_", 1)[1]
    await query.answer(f"✅ Answer: {answer}", show_alert=True)

async def pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = " ".join(context.args)
    choices = [c.strip() for c in args.split("|") if c.strip()]
    if len(choices) < 2:
        return await update.message.reply_text("Usage: /pick Option1 | Option2 | Option3")
    chosen = random.choice(choices)
    await update.message.reply_text(f"🎯 I pick: *{chosen}*", parse_mode=ParseMode.MARKDOWN)

# ─────────────────────────────────────────
#  WELCOME & RULES
# ─────────────────────────────────────────
async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db = get_db()
    c = db.cursor()
    c.execute("SELECT message FROM welcome_messages WHERE chat_id=?", (chat_id,))
    row = c.fetchone()
    db.close()

    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        if row:
            msg = row[0].replace("{name}", member.full_name).replace("{chat}", update.effective_chat.title or "")
        else:
            msg = (
                f"👋 Welcome, *{member.full_name}*!\n\n"
                f"Glad to have you here. Use /help to see what I can do.\n"
                f"Please read /rules and enjoy the community! 🎉"
            )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

async def setwelcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return await update.message.reply_text("❌ Admins only.")
    msg = " ".join(context.args)
    if not msg:
        return await update.message.reply_text(
            "Usage: /setwelcome Your message here\nUse {name} for member name, {chat} for group name"
        )
    chat_id = update.effective_chat.id
    db = get_db()
    c = db.cursor()
    c.execute("INSERT OR REPLACE INTO welcome_messages (chat_id, message) VALUES (?,?)", (chat_id, msg))
    db.commit()
    db.close()
    await update.message.reply_text("✅ Welcome message saved!")

RULES_STORE = {}

async def setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return await update.message.reply_text("❌ Admins only.")
    rules = " ".join(context.args)
    if not rules:
        return await update.message.reply_text("Usage: /setrules Rule 1. No spam. Rule 2. Be kind.")
    RULES_STORE[update.effective_chat.id] = rules
    await update.message.reply_text("✅ Rules saved!")

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    rules_text = RULES_STORE.get(chat_id, "No rules set yet. Admin can set them with /setrules")
    await update.message.reply_text(f"📜 *GROUP RULES*\n\n{rules_text}", parse_mode=ParseMode.MARKDOWN)

# ─────────────────────────────────────────
#  STATS
# ─────────────────────────────────────────
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db = get_db()
    c = db.cursor()
    c.execute("SELECT COUNT(*) FROM contests WHERE chat_id=? AND status='active'", (chat_id,))
    active_contests = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM contests WHERE chat_id=?", (chat_id,))
    total_contests = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM warnings WHERE chat_id=?", (chat_id,))
    total_warnings = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM points WHERE chat_id=?", (chat_id,))
    total_members = c.fetchone()[0]
    db.close()

    text = (
        f"📊 *GROUP STATS*\n\n"
        f"🏆 Active contests: {active_contests}\n"
        f"🏅 Total contests: {total_contests}\n"
        f"⚠️ Total warnings: {total_warnings}\n"
        f"👥 Tracked members: {total_members}\n"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ─────────────────────────────────────────
#  PASSIVE POINTS (chat activity)
# ─────────────────────────────────────────
async def track_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user and not update.effective_user.is_bot:
        u = update.effective_user
        add_points(u.id, update.effective_chat.id, u.username or "", u.full_name, 1)

# ─────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    # Contests
    app.add_handler(CommandHandler("contest", contest))
    app.add_handler(CommandHandler("contests", contests))
    app.add_handler(CommandHandler("joincontest", joincontest))
    app.add_handler(CommandHandler("endcontest", endcontest))

    # Polls
    app.add_handler(CommandHandler("poll", poll_cmd))
    app.add_handler(CommandHandler("quiz", quiz_cmd))
    app.add_handler(CommandHandler("yesno", yesno_cmd))

    # Points
    app.add_handler(CommandHandler("points", points_cmd))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("givepoints", givepoints))

    # Moderation
    app.add_handler(CommandHandler("warn", warn))
    app.add_handler(CommandHandler("warnings", warnings_cmd))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("purge", purge))

    # Fun
    app.add_handler(CommandHandler("giveaway", giveaway))
    app.add_handler(CommandHandler("roll", roll))
    app.add_handler(CommandHandler("flip", flip))
    app.add_handler(CommandHandler("trivia", trivia))
    app.add_handler(CommandHandler("pick", pick))

    # Settings
    app.add_handler(CommandHandler("setwelcome", setwelcome))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("setrules", setrules))
    app.add_handler(CommandHandler("stats", stats))

    # Callbacks
    app.add_handler(CallbackQueryHandler(join_contest_button, pattern=r"^join_\d+$"))
    app.add_handler(CallbackQueryHandler(trivia_answer, pattern=r"^trivia_"))

    # Welcome new members
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))

    # Passive points tracking
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_message))

    logger.info("✅ Howler (@AlphaHowler_Bot) is running! 🐺")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
