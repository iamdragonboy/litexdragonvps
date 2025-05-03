# bot.py
import discord
import subprocess
import json
import os

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

TOKEN = "YOUR_BOT_TOKEN"  # Replace with your token
SETTINGS_FILE = "settings.json"
VPS_USER_FILE = "vps_users.json"
ADMIN_ID = "1159037240622723092,1135898016134463498"
DEFAULT_PREFIX = "./"
FIXED_PASSWORD = "12345678"
FIXED_PORT = 2222
FIXED_USERNAME = "vpsuser"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {"prefix": DEFAULT_PREFIX, "admins": []}

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

settings = load_settings()

def get_ip():
    try:
        return subprocess.check_output(["curl", "-s", "ifconfig.me"]).decode().strip()
    except Exception:
        return "0.0.0.0"

def create_vps_user():
    subprocess.call(["useradd", "-m", FIXED_USERNAME])
    subprocess.call(f"echo '{FIXED_USERNAME}:{FIXED_PASSWORD}' | chpasswd", shell=True)
    subprocess.call(["ufw", "allow", str(FIXED_PORT)])
    
    ssh_config = f"\nMatch User {FIXED_USERNAME}\n    Port {FIXED_PORT}\n"
    with open("/etc/ssh/sshd_config", "a") as f:
        f.write(ssh_config)
    subprocess.call(["systemctl", "restart", "ssh"])

    ip = get_ip()
    return FIXED_USERNAME, FIXED_PASSWORD, FIXED_PORT, ip

def load_users():
    if os.path.exists("vps_users.json"):
        with open("vps_users.json", "r") as f:
            return json.load(f)
    return []

def save_users(data):
    with open("vps_users.json", "w") as f:
        json.dump(data, f, indent=2)

def delete_users():
    data = load_users()
    for u in data:
        subprocess.call(["userdel", "-r", u['user']])
    if os.path.exists("vps_users.json"):
        os.remove("vps_users.json")

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    prefix = settings.get("prefix", DEFAULT_PREFIX)
    msg = message.content.strip()

    if not msg.startswith(prefix):
        return

    command = msg[len(prefix):].strip()

    if command.startswith("ping"):
        await message.channel.send("Pong! Bot is online.")

    elif command.startswith("deploy"):
        if message.author.id not in settings["admins"]:
            await message.channel.send("Admins only.")
            return
        user, password, port, ip = create_vps_user()
        users = load_users()
        users.append({"user": user, "pass": password, "port": port, "owner": str(message.author)})
        save_users(users)
        vps_msg = (
            f"**VPS Ready**\nIP: `{ip}`\nUser: `{user}`\nPass: `{password}`\nPort: `{port}`\n"
            f"Command: `ssh {user}@{ip} -p {port}`"
        )
        try:
            await message.author.send(vps_msg)
            await message.channel.send("VPS details sent in DM.")
        except:
            await message.channel.send("Unable to send DM. Check your privacy settings.")

    elif command.startswith("list"):
        users = load_users()
        if not users:
            await message.channel.send("No VPS users found.")
            return
        msg_list = "**VPS User List:**\n"
        for u in users:
            msg_list += f"User: `{u['user']}` | Port: `{u['port']}`\n"
        await message.channel.send(msg_list)

    elif command.startswith("nodeadmin"):
        if message.author.id not in settings["admins"]:
            await message.channel.send("Admins only.")
            return
        users = load_users()
        if not users:
            await message.channel.send("No VPS details available.")
            return
        full_list = "**All VPS User Details:**\n"
        for u in users:
            full_list += f"User: `{u['user']}` | Pass: `{u['pass']}` | Port: `{u['port']}`\n"
        await message.channel.send(full_list)

    elif command.startswith("delvps"):
        if message.author.id not in settings["admins"]:
            await message.channel.send("Admins only.")
            return
        delete_users()
        await message.channel.send("All VPS users have been deleted.")

    elif command.startswith("botinfo"):
        await message.channel.send("**Bot Info:** Dev: You | Prefix: {}".format(settings.get("prefix")))

    elif command.startswith("prefix"):
        options = ['.', '/', '%', '*']
        msg = "**Available Prefix Options:**\n"
        for opt in options:
            msg += f"Use `{prefix}prefix {opt}` to change to `{opt}`\n"
        if len(command.split()) == 2 and command.split()[1] in options:
            settings["prefix"] = command.split()[1]
            save_settings(settings)
            await message.channel.send(f"Prefix updated to `{settings['prefix']}`")
        else:
            await message.channel.send(msg)

    elif command.startswith("botadmin add"):
        parts = command.split()
        if message.author.id not in settings["admins"]:
            await message.channel.send("Admins only.")
            return
        if len(parts) >= 3:
            try:
                new_admin = int(parts[2])
                if new_admin not in settings["admins"]:
                    settings["admins"].append(new_admin)
                    save_settings(settings)
                    await message.channel.send("Admin added.")
                else:
                    await message.channel.send("User is already an admin.")
            except:
                await message.channel.send("Invalid user ID.")

    elif command.startswith("botadmin remove"):
        parts = command.split()
        if message.author.id not in settings["admins"]:
            await message.channel.send("Admins only.")
            return
        if len(parts) >= 3:
            try:
                remove_id = int(parts[2])
                if remove_id in settings["admins"]:
                    settings["admins"].remove(remove_id)
                    save_settings(settings)
                    await message.channel.send("Admin removed.")
                else:
                    await message.channel.send("User is not an admin.")
            except:
                await message.channel.send("Invalid user ID.")

bot.run(TOKEN)
