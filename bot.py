"""
╔══════════════════════════════════════════════════════════════╗
║         AdiCheats — Discord UID Management Bot               ║
║         Slash Commands | Credits | Logging | Setup           ║
╚══════════════════════════════════════════════════════════════╝

Usage:
    python bot.py
    Make sure your BOT_TOKEN is set in .env
"""

import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import threading
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# ===================== OWNER CONFIG =====================
# Paste your Discord User ID here (right-click your name → Copy ID)
OWNER_ID = 1354876648096272384   # <-- CHANGE THIS to your Discord User ID

# ===================== BOT SETUP =====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
# Always resolve to the same directory as this script — regardless of cwd
JSON_FILE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_data.json")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===================== COLORS =====================
COLOR_SUCCESS = 0x2ECC71
COLOR_ERROR   = 0xE74C3C
COLOR_INFO    = 0x3498DB
COLOR_WARNING = 0xF39C12
COLOR_PURPLE  = 0x9B59B6

# ===================== JSON DATA LAYER =====================

_json_lock = threading.Lock()

_DEFAULT_DATA = {
    "users": {},
    "settings": {
        "logs_channel_id":     None,
        "commands_channel_id": None,
        "owner_id":            str(OWNER_ID),
        "setup_complete":      "false",
    },
    "blacklist": [],
    "uid_cache": {},
    "server_rules": {},
    "login_logs": [],
    "stats": {"total": 0, "allowed": 0, "blocked": 0},
}


def _read_json() -> dict:
    """Read bot_data.json from disk. Returns default structure if missing/corrupt."""
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Back-fill any missing top-level keys
        for k, v in _DEFAULT_DATA.items():
            if k not in data:
                data[k] = v
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {k: (v.copy() if isinstance(v, dict) else list(v) if isinstance(v, list) else v)
                for k, v in _DEFAULT_DATA.items()}


def _write_json(data: dict):
    """Write data to bot_data.json atomically (temp file → rename)."""
    tmp = JSON_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, JSON_FILE)


def read_data() -> dict:
    with _json_lock:
        return _read_json()


def write_data(data: dict):
    with _json_lock:
        _write_json(data)


def init_json():
    """Initialise bot_data.json with default values if it doesn't exist."""
    with _json_lock:
        data = _read_json()
        _write_json(data)
    print(f"[BOT] Data file ready: {JSON_FILE}")


# ===================== SETTINGS HELPERS =====================

def get_setting(key: str):
    return read_data()["settings"].get(key)


def set_setting(key: str, value):
    with _json_lock:
        data = _read_json()
        data["settings"][key] = value
        _write_json(data)


def is_setup_done() -> bool:
    return get_setting("setup_complete") == "true"


# ===================== EMBED FACTORY =====================

def make_embed(title, description="", color=COLOR_INFO, fields=None):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="AdiCheats Bot • UID Manager")
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    return embed


def error_embed(msg):
    return make_embed("❌ Error", msg, COLOR_ERROR)


def success_embed(title, msg=""):
    return make_embed(f"✅ {title}", msg, COLOR_SUCCESS)


def info_embed(title, msg=""):
    return make_embed(f"ℹ️ {title}", msg, COLOR_INFO)


# ===================== LOGGING HELPER =====================

async def send_log(description, color=COLOR_INFO, fields=None, title="📋 Bot Log"):
    channel_id = get_setting("logs_channel_id")
    if not channel_id:
        return
    try:
        channel = bot.get_channel(int(channel_id))
        if channel:
            await channel.send(embed=make_embed(title, description, color, fields))
    except Exception as e:
        print(f"[LOG ERROR] {e}")


# ===================== PERMISSION CHECKS =====================

def is_owner(interaction: discord.Interaction) -> bool:
    return interaction.user.id == OWNER_ID


async def require_setup(interaction: discord.Interaction) -> bool:
    if not is_setup_done():
        await interaction.response.send_message(
            embed=make_embed(
                "⚙️ Setup Required",
                "Run **/setup** first to configure the bot.",
                COLOR_WARNING,
            ),
            ephemeral=True,
        )
        return False
    return True


async def require_owner(interaction: discord.Interaction) -> bool:
    if not is_owner(interaction):
        await interaction.response.send_message(
            embed=error_embed("🔒 Restricted to the **bot owner** only."),
            ephemeral=True,
        )
        return False
    return True


# ===================== BOT EVENTS =====================

@bot.event
async def on_ready():
    init_json()
    print(f"[BOT] Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"[BOT] Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"[BOT] Sync error: {e}")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="UIDs 👁️")
    )


# ===================== /setup =====================

@bot.tree.command(name="setup", description="Configure the bot channels (run once on first use)")
@app_commands.describe(
    commands_channel="Channel for bot responses",
    logs_channel="Channel for all logs",
)
async def setup(interaction: discord.Interaction,
                commands_channel: discord.TextChannel,
                logs_channel: discord.TextChannel):
    if is_setup_done():
        await interaction.response.send_message(
            embed=error_embed("Setup already completed. Use **/help** to see commands."),
            ephemeral=True,
        )
        return

    with _json_lock:
        data = _read_json()
        data["settings"]["commands_channel_id"] = str(commands_channel.id)
        data["settings"]["logs_channel_id"]     = str(logs_channel.id)
        data["settings"]["setup_complete"]       = "true"
        _write_json(data)

    embed = make_embed(
        "⚙️ Setup Complete!",
        "Bot is now configured and ready.",
        COLOR_SUCCESS,
        fields=[
            ("📨 Commands Channel", commands_channel.mention, True),
            ("📋 Logs Channel",     logs_channel.mention,     True),
            ("👤 Owner ID",         f"`{OWNER_ID}`",           False),
        ]
    )
    await interaction.response.send_message(embed=embed)
    await send_log(
        f"Setup completed by {interaction.user.mention}",
        COLOR_SUCCESS,
        fields=[("Commands", commands_channel.mention, True), ("Logs", logs_channel.mention, True)],
        title="⚙️ Setup Completed",
    )


# ===================== /add =====================

@bot.tree.command(name="add", description="Add a UID to the database")
@app_commands.describe(uid="The Free Fire UID to add")
async def add_uid(interaction: discord.Interaction, uid: str):
    if not await require_setup(interaction):
        return

    uid = uid.strip()
    if not uid.isdigit():
        await interaction.response.send_message(
            embed=error_embed(f"`{uid}` is not a valid UID — must be numeric."),
            ephemeral=True,
        )
        return

    with _json_lock:
        data = _read_json()
        if uid in data["users"]:
            await interaction.response.send_message(
                embed=error_embed(f"UID `{uid}` already exists."),
                ephemeral=True,
            )
            return
        data["users"][uid] = {
            "credits":  0,
            "added_at": datetime.now(timezone.utc).isoformat(),
        }
        _write_json(data)

    embed = success_embed("UID Added", f"UID `{uid}` added successfully.")
    embed.add_field(name="💳 Starting Credits", value="`0`", inline=True)
    await interaction.response.send_message(embed=embed)
    await send_log(
        f"UID added by {interaction.user.mention}",
        COLOR_SUCCESS,
        fields=[("UID", f"`{uid}`", True), ("Credits", "`0`", True)],
        title="➕ UID Added",
    )


# ===================== /remove =====================

@bot.tree.command(name="remove", description="Remove a UID from the database")
@app_commands.describe(uid="The Free Fire UID to remove")
async def remove_uid(interaction: discord.Interaction, uid: str):
    if not await require_setup(interaction):
        return

    uid = uid.strip()

    with _json_lock:
        data = _read_json()
        if uid not in data["users"]:
            await interaction.response.send_message(
                embed=error_embed(f"UID `{uid}` not found."),
                ephemeral=True,
            )
            return
        old_credits = data["users"][uid].get("credits", 0)
        del data["users"][uid]
        _write_json(data)

    embed = success_embed("UID Removed", f"UID `{uid}` removed.")
    embed.add_field(name="💳 Credits at removal", value=f"`{old_credits}`", inline=True)
    await interaction.response.send_message(embed=embed)
    await send_log(
        f"UID removed by {interaction.user.mention}",
        COLOR_ERROR,
        fields=[("UID", f"`{uid}`", True), ("Credits Lost", f"`{old_credits}`", True)],
        title="➖ UID Removed",
    )


# ===================== /change =====================

@bot.tree.command(name="change", description="Change an existing UID to a new UID")
@app_commands.describe(uid="The current UID", new_uid="The new UID")
async def change_uid(interaction: discord.Interaction, uid: str, new_uid: str):
    if not await require_setup(interaction):
        return

    uid     = uid.strip()
    new_uid = new_uid.strip()

    if not new_uid.isdigit():
        await interaction.response.send_message(
            embed=error_embed(f"`{new_uid}` is not a valid UID."),
            ephemeral=True,
        )
        return

    with _json_lock:
        data = _read_json()
        if uid not in data["users"]:
            await interaction.response.send_message(
                embed=error_embed(f"UID `{uid}` not found."),
                ephemeral=True,
            )
            return
        if new_uid in data["users"]:
            await interaction.response.send_message(
                embed=error_embed(f"UID `{new_uid}` already exists."),
                ephemeral=True,
            )
            return
        entry = data["users"].pop(uid)
        data["users"][new_uid] = entry
        _write_json(data)

    credits = entry.get("credits", 0)
    embed = success_embed("UID Changed", "UID updated successfully.")
    embed.add_field(name="🔄 Old UID",      value=f"`{uid}`",     inline=True)
    embed.add_field(name="✅ New UID",      value=f"`{new_uid}`", inline=True)
    embed.add_field(name="💳 Credits Kept", value=f"`{credits}`", inline=False)
    await interaction.response.send_message(embed=embed)
    await send_log(
        f"UID changed by {interaction.user.mention}",
        COLOR_WARNING,
        fields=[("Old UID", f"`{uid}`", True), ("New UID", f"`{new_uid}`", True), ("Credits", f"`{credits}`", True)],
        title="🔄 UID Changed",
    )


# ===================== /credits =====================

@bot.tree.command(name="credits", description="Check credits for a UID")
@app_commands.describe(uid="The Free Fire UID to check")
async def check_credits(interaction: discord.Interaction, uid: str):
    if not await require_setup(interaction):
        return

    uid  = uid.strip()
    data = read_data()

    if uid not in data["users"]:
        await interaction.response.send_message(
            embed=error_embed(f"UID `{uid}` not found."),
            ephemeral=True,
        )
        return

    entry = data["users"][uid]
    embed = info_embed("Credits Balance", f"Balance for UID `{uid}`.")
    embed.add_field(name="🎮 UID",      value=f"`{uid}`",                      inline=True)
    embed.add_field(name="💳 Credits",  value=f"`{entry.get('credits', 0)}`",  inline=True)
    embed.add_field(name="🕐 Added At", value=f"`{entry.get('added_at','?')}`", inline=False)
    await interaction.response.send_message(embed=embed)


# ===================== /add_credits =====================

@bot.tree.command(name="add_credits", description="Add credits to a UID (owner only)")
@app_commands.describe(uid="The Free Fire UID", amount="Credits to add")
async def add_credits(interaction: discord.Interaction, uid: str, amount: int):
    if not await require_setup(interaction):
        return
    if not await require_owner(interaction):
        return

    uid = uid.strip()
    if amount <= 0:
        await interaction.response.send_message(
            embed=error_embed("Amount must be a positive integer."),
            ephemeral=True,
        )
        return

    with _json_lock:
        data = _read_json()
        if uid not in data["users"]:
            await interaction.response.send_message(
                embed=error_embed(f"UID `{uid}` not found."),
                ephemeral=True,
            )
            return
        old = data["users"][uid].get("credits", 0)
        new = old + amount
        data["users"][uid]["credits"] = new
        _write_json(data)

    embed = success_embed("Credits Added", f"Added **{amount}** credits to `{uid}`.")
    embed.add_field(name="💳 Before", value=f"`{old}`", inline=True)
    embed.add_field(name="➕ Added",  value=f"`{amount}`", inline=True)
    embed.add_field(name="✅ After",  value=f"`{new}`", inline=True)
    await interaction.response.send_message(embed=embed)
    await send_log(
        f"Credits added by Owner ({interaction.user.mention})",
        COLOR_PURPLE,
        fields=[("UID", f"`{uid}`", True), ("Added", f"`+{amount}`", True), ("Balance", f"`{new}`", True)],
        title="💳 Credits Added",
    )


# ===================== /remove_credits =====================

@bot.tree.command(name="remove_credits", description="Remove credits from a UID (owner only)")
@app_commands.describe(uid="The Free Fire UID", amount="Credits to remove")
async def remove_credits(interaction: discord.Interaction, uid: str, amount: int):
    if not await require_setup(interaction):
        return
    if not await require_owner(interaction):
        return

    uid = uid.strip()
    if amount <= 0:
        await interaction.response.send_message(
            embed=error_embed("Amount must be a positive integer."),
            ephemeral=True,
        )
        return

    with _json_lock:
        data = _read_json()
        if uid not in data["users"]:
            await interaction.response.send_message(
                embed=error_embed(f"UID `{uid}` not found."),
                ephemeral=True,
            )
            return
        old     = data["users"][uid].get("credits", 0)
        new     = max(0, old - amount)
        removed = old - new
        data["users"][uid]["credits"] = new
        _write_json(data)

    note = f"\n⚠️ Only `{removed}` removed (floored at 0)." if removed < amount else ""
    embed = success_embed("Credits Removed", f"Removed **{removed}** credits from `{uid}`.{note}")
    embed.add_field(name="💳 Before", value=f"`{old}`",     inline=True)
    embed.add_field(name="➖ Removed", value=f"`{removed}`", inline=True)
    embed.add_field(name="✅ After",   value=f"`{new}`",     inline=True)
    await interaction.response.send_message(embed=embed)
    await send_log(
        f"Credits removed by Owner ({interaction.user.mention})",
        COLOR_PURPLE,
        fields=[("UID", f"`{uid}`", True), ("Removed", f"`-{removed}`", True), ("Balance", f"`{new}`", True)],
        title="💳 Credits Removed",
    )


# ===================== /list_users =====================

@bot.tree.command(name="list_users", description="List all UIDs and credits")
async def list_users(interaction: discord.Interaction):
    if not await require_setup(interaction):
        return

    data  = read_data()
    users = data.get("users", {})

    if not users:
        await interaction.response.send_message(
            embed=info_embed("User List", "📭 No UIDs in the database."),
            ephemeral=True,
        )
        return

    lines = ["```", f"{'UID':<20} {'Credits':>8}  Added At", "─" * 50]
    for uid, info in sorted(users.items(), key=lambda x: x[1].get("added_at", ""), reverse=True):
        added = (info.get("added_at") or "")[:10]
        lines.append(f"{uid:<20} {info.get('credits', 0):>8}  {added}")
    lines.append("```")

    description = "\n".join(lines)
    if len(description) > 4000:
        description = description[:3950] + "\n...```"

    await interaction.response.send_message(
        embed=info_embed(f"User List ({len(users)} total)", description)
    )


# ===================== /help =====================

@bot.tree.command(name="help", description="Show all available commands")
async def help_cmd(interaction: discord.Interaction):
    embed = make_embed("📖 AdiCheats Bot — Commands", "All slash commands:", COLOR_INFO)
    embed.add_field(name="⚙️ /setup", value="Configure channels (first-time setup)", inline=False)
    embed.add_field(name="➕ /add `uid`", value="Add a UID", inline=False)
    embed.add_field(name="➖ /remove `uid`", value="Remove a UID", inline=False)
    embed.add_field(name="🔄 /change `uid` `new_uid`", value="Change a UID (credits preserved)", inline=False)
    embed.add_field(name="💳 /credits `uid`", value="Check credits balance", inline=False)
    embed.add_field(name="🟢 /add_credits `uid` `amount` *(Owner)*", value="Add credits", inline=False)
    embed.add_field(name="🔴 /remove_credits `uid` `amount` *(Owner)*", value="Remove credits", inline=False)
    embed.add_field(name="📋 /list_users", value="List all UIDs and balances", inline=False)
    await interaction.response.send_message(embed=embed)


# ===================== GLOBAL ERROR HANDLER =====================

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    msg = str(error)
    if isinstance(error, app_commands.MissingPermissions):
        msg = "You don't have permission to use this command."
    elif isinstance(error, app_commands.CommandOnCooldown):
        msg = f"Cooldown: retry in `{error.retry_after:.1f}s`."
    try:
        await interaction.response.send_message(embed=error_embed(msg), ephemeral=True)
    except discord.InteractionResponded:
        await interaction.followup.send(embed=error_embed(msg), ephemeral=True)
    await send_log(
        f"Error in `/{getattr(interaction.command, 'name', '?')}` by {interaction.user.mention}: `{error}`",
        COLOR_ERROR,
        title="⚠️ Command Error",
    )


# ===================== RUN =====================

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set in .env!")
        exit(1)
    print("[BOT] Starting...")
    bot.run(BOT_TOKEN)
