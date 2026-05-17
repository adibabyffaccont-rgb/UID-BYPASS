"""
╔══════════════════════════════════════════════════════════════╗
║         Script Kittens — Free Fire UID Bypass                ║
║         MITMPROXY Interceptor + Control Panel                ║
║         Educational / Research Release                       ║
╠══════════════════════════════════════════════════════════════╣
║  Developers  :  1shot  &  Zen                                ║
║  Join us for more projects, tools & community support!       ║
╚══════════════════════════════════════════════════════════════╝

Usage:
    python main.py
    Starts mitmproxy on 0.0.0.0:8082.
"""

import sys
import subprocess
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from dotenv import load_dotenv
load_dotenv()

import os
import time
import asyncio
import threading
import requests
import copy
import json
from collections import deque
from datetime import datetime

from mitmproxy import http

# Use common utils instead of old new_utils
from common.utils import aes_decrypt, encrypt_api, get_available_room, CrEaTe_ProTo
# Import regions from config
from config import regions
import CSGetAccountBriefInfoBeforeLoginRes_pb2

# ===================== CONFIG =====================

CHECK_INTERVAL = 1                                 # seconds between sync checks
UID_TTL_SECONDS = 24 * 60 * 60                     # UID expiry (1 day)

UID_SERVERS = {
    "MAIN":   "http://13.67.77.249/raw/uid",
}

# Always resolve to the same directory as this script — regardless of cwd
JSON_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_data.json")

# ===================== NEW BYPASS LOGIC =====================

MOBILE_PROTO = "25f16c42b17c8239fccb04095cf57404c3b0bb26906e7ba86f20ce787935f3b9eea0e0cf108b16269a322d06d9cadf6b4e6822d26490eb78ac78ea85705321894d288f6517b2a17b6027ebfd00ed9b336a2ec1c6bed513c218e0bb142bbc045782b578328fe0cea774f6e60f3e278794110dc58ed62a87948fc4005882a1ac2a10d18762c6789d2c148d1924b3e04eff87b8538dfc5f8bfe8ff503dc2849f2343fa13bb892005d68bad712508475f1735869b65b24a48f96c95937794363497b7897600cf8786407d6d8bc01d87eaee4a00da554fc96b6f415119e29efe1fe491c244edcc3091e5a2148954e870a3a1c5cddcf022ca8453a030013b4f2a8dd18d8e5e5be88c04cab6c0933d96bcc44600f619b424e89f95f979b46f457e51d6742a4398ca4c8d4b9f5a3e8c9c3c08363bfcd8d072518973c099abf69958e130b027f36dc007d449e544037f61a21fbd7735c2014028c3d29ccefcf3a25f2a65bd574f75a8ac8325106b75155ede5ee1919fbc12b3d86f34e564f3728cdf8165d399f1de23a2cee57ec283d36e1525d2392cbcffd5a3bf7766867eda25720864aeb06c729bc9fe254059376fcd70e4879ea6f77355948843585e6380c220793065084ecb64a8596183815c297d5bf878927a5205c57601ea87bbf7451d3c4d83ffdaec2f891e9da8959cfc5a655c5be056712538eee05518dfa80072a4c27d2203c2fd3c5dd2b20c0fbb1f2fd7db64d5d3e08e7141a3093007909f98c7984dcc940e9000ac573af6cd81f78d8e20f2fb0b34e6bf01dee9100f458019641dc854920cd8be6f5599e239d68e4b5fef9c257710f4b4009b45086391c6cda3314638dae22a96cfeedf97b52d1fa6c30195f2ce4b1064db23929a38a1103d3d4edd6c9e29203a7b1ba975b681fbcff1e4c6d910dc9e98a02339d1d7d748c877a9726dd653547c8442aa12577a62954c19c24857ea605decf1ede72ce5b159398bd4082cafeaad73cdb5563c45f9476b6069f87dec9e0c18fa2c944806f35c8a07f52e3bf66b545f5457e06d04754a869388596f1653cf951caae15f2d48191ec8db0ec813682cbda38b4aaa3defcef332256fa549ff4fcc9f0b7e08f5c71d4ce6bc366f960e15c0018526b93c58f445e339b14ba5b296c546314de30f2c66508bf4436b6787b095603b918aaff638711ddb8255e1e782d299f48aa9fba0b334cff16e3cc1c43225e17cc51f39215e0d2c2afceaed18358787074475d928a6665130bb8cff4a901a7b8f5ec67298fb9b4d665a0182a11abb55109b838c58ebcb56e29c617fb82b1e1a7c49b934de0d12bd4775ae8abd216848a6cea02ebc44fcd14a7aa9ac09b641fee138d5cad7eeb0a3c23df06846f2bfc8c0a87e4a884915909726c34dddd35111a003f524437bdcbe10b3e60b7d442f39666ad7916c784160be8df"

# Initialize template for MajorLogin
try:
    decrypted_bytes = aes_decrypt(MOBILE_PROTO)
    decrypted_hex = decrypted_bytes.hex() if decrypted_bytes else ""
    proto_json = get_available_room(decrypted_hex)
    proto_fields = json.loads(proto_json or "{}")
    proto_template = copy.deepcopy(proto_fields)
    print("✅ Successfully loaded and parsed MOBILE_PROTO template")
except Exception as e:
    print(f"❌ Error loading MOBILE_PROTO template: {e}")
    proto_template = {}

# Initialize second template for GetLoginData (same proto, separate deepcopy)
try:
    decrypted_bytes1 = aes_decrypt(MOBILE_PROTO)
    decrypted_hex1 = decrypted_bytes1.hex() if decrypted_bytes1 else ""
    proto_json1 = get_available_room(decrypted_hex1)
    proto_fields1 = json.loads(proto_json1 or "{}")
    proto_template1 = copy.deepcopy(proto_fields1)
    print("✅ Successfully loaded proto_template1 for GetLoginData")
except Exception as e:
    print(f"❌ Error loading proto_template1: {e}")
    proto_template1 = {}

# ===================== GLOBALS =====================

BLOCK_ENABLED = True
stats = {"total": 0, "allowed": 0, "blocked": 0}
blocked_times = deque(maxlen=50)

uid_caches = {}            # {server_name: set(uids)}
server_states = {}         # {server_name: "up"|"down"|"unknown"}
synced_once = False        # first-time sync flag

# For heavy abuse detection
LAST_ABUSE_ALERT = 0
ABUSE_WINDOW = 10      # seconds
ABUSE_THRESHOLD = 10   # blocked logins needed
ABUSE_COOLDOWN = 60    # seconds between alerts


# ===================== JSON DATA LAYER =====================

_json_lock = threading.Lock()

_DEFAULT_DATA = {
    "users":       {},
    "settings":    {"setup_complete": "false"},
    "blacklist":   [],
    "uid_cache":   {},
    "server_rules": {name: "on" for name in UID_SERVERS.keys()},
    "login_logs":  [],
    "stats":       {"total": 0, "allowed": 0, "blocked": 0},
}


def _read_json() -> dict:
    """Read bot_data.json — returns default structure if missing or corrupt."""
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in _DEFAULT_DATA.items():
            if k not in data:
                data[k] = v
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {k: (v.copy() if isinstance(v, (dict, list)) else v)
                for k, v in _DEFAULT_DATA.items()}


def _write_json(data: dict):
    """Write data atomically: temp file → rename."""
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


# Initialise JSON file on startup
with _json_lock:
    _d = _read_json()
    _write_json(_d)
print(f"[*] Data file ready: {JSON_FILE}")

# ===================== HELPERS =====================

def is_expiry_valid(expiry_str: str) -> bool:
    """Check if expiry date (DD.MM.YYYY format) has not passed."""
    if not expiry_str:
        return True  # No expiry = always valid
    try:
        expiry_date = datetime.strptime(expiry_str.strip(), "%d.%m.%Y")
        current_date = datetime.now()
        return current_date <= expiry_date
    except (ValueError, AttributeError):
        return True  # Invalid format = assume valid

def checkUIDExists(uid: str) -> bool:
    """Check if UID is in the users section of bot_data.json.
    Reads fresh from disk every call so bot.py changes are instantly visible.
    """
    uid = uid.strip()
    print(f"\n[UID CHECK] Checking UID: {uid}")

    # ── PRIMARY: users object in JSON (managed by Discord bot) ───────────────
    try:
        data = read_data()
        if uid in data.get("users", {}):
            print(f"[UID CHECK] ✅ Found in users (JSON)")
            return True
    except Exception as e:
        print(f"[UID CHECK] JSON users error: {e}")

    # ── FALLBACK: uid_cache synced from remote server ───────────────────────
    try:
        current_time = int(time.time())
        data = read_data()
        uid_cache   = data.get("uid_cache", {})
        server_rules = data.get("server_rules", {})
        for server_name, uids in uid_cache.items():
            if server_rules.get(server_name) == "on":
                entry = uids.get(uid)
                if entry:
                    last_seen = entry if isinstance(entry, int) else entry.get("last_seen", 0)
                    if current_time - last_seen <= UID_TTL_SECONDS:
                        print(f"[UID CHECK] ✅ Found in uid_cache ({server_name})")
                        return True
    except Exception as e:
        print(f"[UID CHECK] JSON uid_cache error: {e}")

    print(f"[UID CHECK] ❌ UID {uid} NOT FOUND")
    return False


def fetch_uids(server_name: str, url: str) -> set | None:
    """Fetch UIDs from remote server and sync into uid_cache in JSON."""
    try:
        r = requests.get(url, timeout=10, proxies={"http": "", "https": ""})
        r.raise_for_status()
        uids = {
            line.strip()
            for line in r.text.splitlines()
            if line.strip().isdigit()
        }
        now = int(time.time())
        with _json_lock:
            data = _read_json()
            cache = data.setdefault("uid_cache", {})
            server_cache = cache.setdefault(server_name, {})
            # Remove UIDs no longer in server list
            for old_uid in list(server_cache.keys()):
                if old_uid not in uids:
                    del server_cache[old_uid]
            # Add/update UIDs
            for uid in uids:
                server_cache[uid] = now
            # TTL cleanup across all servers
            cutoff = now - UID_TTL_SECONDS
            for sn in list(cache.keys()):
                cache[sn] = {u: ts for u, ts in cache[sn].items() if ts >= cutoff}
            _write_json(data)
        return uids
    except Exception as e:
        print(f"[UID SERVER] {server_name} DOWN: {e}")
        return None


def lookup_geo(ip: str | None):
    if not ip:
        return None, None, None
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}", timeout=5, proxies={"http": "", "https": ""})
        j = r.json()
        return j.get("country"), j.get("regionName"), j.get("city")
    except:
        return None, None, None


def log_login_db(uid: str, ip: str | None, country: str | None, region: str | None, city: str | None, status: str):
    entry = {"uid": uid, "ip": ip, "country": country,
             "region": region, "city": city,
             "ts": int(time.time()), "status": status}
    with _json_lock:
        data = _read_json()
        logs = data.setdefault("login_logs", [])
        logs.append(entry)
        # Keep last 500 logs to avoid unbounded growth
        if len(logs) > 500:
            data["login_logs"] = logs[-500:]
        _write_json(data)


def sync_all_servers():
    """One-shot full sync from all remote UID servers."""
    global uid_caches, server_states
    for name, url in UID_SERVERS.items():
        uids = fetch_uids(name, url)
        if uids is None:
            server_states[name] = "down"
        else:
            server_states[name] = "up"
            uid_caches[name] = uids


def checkUIDStatus(uid: str):
    data  = read_data()
    cache = data.get("uid_cache", {})
    rules = data.get("server_rules", {})
    now   = int(time.time())
    for server_name, uids in cache.items():
        if rules.get(server_name) == "on" and uid in uids:
            last_seen = uids[uid] if isinstance(uids[uid], int) else uids[uid].get("last_seen", 0)
            if now - last_seen <= UID_TTL_SECONDS:
                return "ACTIVE"
            return "EXPIRED"
    return "NOT_FOUND"


def inc_stat(name: str):
    with _json_lock:
        data = _read_json()
        data.setdefault("stats", {})[name] = data["stats"].get(name, 0) + 1
        _write_json(data)


def get_stats() -> dict:
    return read_data().get("stats", {})

# ===================== MITMPROXY INTERCEPTOR =====================

class MajorLoginInterceptor:

    def request(self, flow: http.HTTPFlow) -> None:
        # Handle GetLoginData (PC logo fix - forces platform to 0)
        self._handle_get_login_data(flow)
        # Handle MajorLogin
        if flow.request.method.upper() == "POST" and "/MajorLogin" in flow.request.path:
            try:
                request_bytes = flow.request.content
                if request_bytes is None:
                    return
                request_hex = request_bytes.hex()
                
                # Decrypt
                decrypted_bytes = aes_decrypt(request_hex)
                decrypted_hex = decrypted_bytes.hex()
                
                # Parse
                proto_json = get_available_room(decrypted_hex)
                proto_fields = json.loads(proto_json or "{}")
                
                uid = None
                access_token = None
                open_id = None
                main_active_platform = None
                version_field = None
                event_time = None

                # Extract fields
                for field_num in ["1", "2", "3"]:
                    if field_num in proto_fields and isinstance(proto_fields[field_num], dict) and "data" in proto_fields[field_num]:
                        potential_uid = str(proto_fields[field_num]["data"])
                        if potential_uid.isdigit() and len(potential_uid) > 5:
                            uid = potential_uid
                            break
                # Field 3 = event_time timestamp (carry from real request)
                if "3" in proto_fields and isinstance(proto_fields["3"], dict) and "data" in proto_fields["3"]:
                    event_time = str(proto_fields["3"]["data"])
                if "7" in proto_fields and isinstance(proto_fields["7"], dict) and "data" in proto_fields["7"]:
                    version_field = str(proto_fields["7"]["data"])
                if "29" in proto_fields and isinstance(proto_fields["29"], dict) and "data" in proto_fields["29"]:
                    access_token = str(proto_fields["29"]["data"])

                if "22" in proto_fields and isinstance(proto_fields["22"], dict) and "data" in proto_fields["22"]:
                    open_id = str(proto_fields["22"]["data"])

                if "99" in proto_fields and isinstance(proto_fields["99"], dict) and "data" in proto_fields["99"]:
                    main_active_platform = str(proto_fields["99"]["data"])
                elif "100" in proto_fields and isinstance(proto_fields["100"], dict) and "data" in proto_fields["100"]:
                    main_active_platform = str(proto_fields["100"]["data"])
                
                # Modify using template
                modified_proto = copy.deepcopy(proto_template)

                # Carry event_time from real request (field 3) — prevents stale timestamp detection
                if event_time:
                    if "3" in modified_proto and isinstance(modified_proto["3"], dict):
                        modified_proto["3"]["data"] = event_time
                    else:
                        modified_proto["3"] = {"wire_type": "string", "data": event_time}

                # Preserve client_version from original request
                if version_field:
                    if "7" in modified_proto and isinstance(modified_proto["7"], dict):
                        modified_proto["7"]["data"] = version_field
                    else:
                        modified_proto["7"] = {"wire_type": "string", "data": version_field}
                else:
                    if "7" in modified_proto and isinstance(modified_proto["7"], dict):
                        modified_proto["7"]["data"] = "1.120.3"
                    else:
                        modified_proto["7"] = {"wire_type": "string", "data": "1.120.3"}

                if "29" in modified_proto and isinstance(modified_proto["29"], dict):
                    modified_proto["29"]["data"] = access_token if access_token else modified_proto["29"].get("data", "")

                if "22" in modified_proto and isinstance(modified_proto["22"], dict):
                    modified_proto["22"]["data"] = open_id if open_id else modified_proto["22"].get("data", "")

                platform_value = main_active_platform or modified_proto.get("99", {}).get("data", "4")
                def set_platform_field(key: str, value: str):
                    wire_type = "string"
                    if key in proto_fields and isinstance(proto_fields[key], dict) and "wire_type" in proto_fields[key]:
                        wire_type = proto_fields[key]["wire_type"]
                    elif key in modified_proto and isinstance(modified_proto[key], dict) and "wire_type" in modified_proto[key]:
                        wire_type = modified_proto[key]["wire_type"]
                    modified_proto[key] = {"wire_type": wire_type, "data": value}

                set_platform_field("99", platform_value)
                set_platform_field("100", platform_value)
                print(f"[+] Fields 99/100 preserved as '{platform_value}'")

                # Re-encrypt
                proto_bytes = CrEaTe_ProTo(modified_proto)
                hex_data = encrypt_api(proto_bytes)
                flow.request.content = bytes.fromhex(hex_data)
                print("[+] Successfully modified and encrypted MajorLogin request")

            except Exception as e:
                print(f"Error processing MajorLogin request: {e}")

    def _handle_get_login_data(self, flow: http.HTTPFlow):
        """Handle /GetLoginData requests — uses proto_template1 with platform=0."""
        if flow.request.method.upper() != "POST" or "/GetLoginData" not in flow.request.path:
            return
        try:
            request_bytes = flow.request.content
            if request_bytes is None:
                return
            request_hex = request_bytes.hex()
            decrypted_bytes = aes_decrypt(request_hex)
            decrypted_hex = decrypted_bytes.hex()
            proto_json = get_available_room(decrypted_hex)
            proto_fields = json.loads(proto_json or "{}")

            uid = None
            access_token = None
            open_id = None
            client_version = None
            main_active_platform = None

            for field_num in ["1", "2", "3"]:
                if field_num in proto_fields and isinstance(proto_fields[field_num], dict) and "data" in proto_fields[field_num]:
                    potential_uid = str(proto_fields[field_num]["data"])
                    if potential_uid.isdigit() and len(potential_uid) > 5:
                        uid = potential_uid
                        break

            if "29" in proto_fields and isinstance(proto_fields["29"], dict) and "data" in proto_fields["29"]:
                access_token = str(proto_fields["29"]["data"])
            if "22" in proto_fields and isinstance(proto_fields["22"], dict) and "data" in proto_fields["22"]:
                open_id = str(proto_fields["22"]["data"])
            if "99" in proto_fields and isinstance(proto_fields["99"], dict) and "data" in proto_fields["99"]:
                main_active_platform = str(proto_fields["99"]["data"])
            elif "100" in proto_fields and isinstance(proto_fields["100"], dict) and "data" in proto_fields["100"]:
                main_active_platform = str(proto_fields["100"]["data"])
            if "7" in proto_fields and isinstance(proto_fields["7"], dict) and "data" in proto_fields["7"]:
                client_version = str(proto_fields["7"]["data"])

            modified_proto = copy.deepcopy(proto_template1)

            if client_version:
                if "7" in modified_proto and isinstance(modified_proto["7"], dict):
                    modified_proto["7"]["data"] = client_version
                else:
                    modified_proto["7"] = {"wire_type": "string", "data": client_version}
            else:
                if "7" in modified_proto and isinstance(modified_proto["7"], dict):
                    modified_proto["7"]["data"] = "1.120.3"
                else:
                    modified_proto["7"] = {"wire_type": "string", "data": "1.120.3"}

            if "29" in modified_proto and isinstance(modified_proto["29"], dict):
                modified_proto["29"]["data"] = access_token if access_token else modified_proto["29"].get("data", "")
            if "22" in modified_proto and isinstance(modified_proto["22"], dict):
                modified_proto["22"]["data"] = open_id if open_id else modified_proto["22"].get("data", "")

            def set_platform_field(key: str, value: str):
                wire_type = "string"
                if key in proto_fields and isinstance(proto_fields[key], dict) and "wire_type" in proto_fields[key]:
                    wire_type = proto_fields[key]["wire_type"]
                elif key in modified_proto and isinstance(modified_proto[key], dict) and "wire_type" in modified_proto[key]:
                    wire_type = modified_proto[key]["wire_type"]
                modified_proto[key] = {"wire_type": wire_type, "data": value}

            platform_value = main_active_platform or modified_proto.get("99", {}).get("data", "0")
            set_platform_field("99", platform_value)
            set_platform_field("100", platform_value)
            print(f"[+] GetLoginData fields 99/100 preserved as '{platform_value}' (preserving original platform if available)")

            proto_bytes = CrEaTe_ProTo(modified_proto)
            hex_data = encrypt_api(proto_bytes)
            flow.request.content = bytes.fromhex(hex_data)
            print("[+] Successfully modified and encrypted GetLoginData request")

        except Exception as e:
            print(f"Error processing GetLoginData request: {e}")

    def response(self, flow: http.HTTPFlow) -> None:
        global LAST_ABUSE_ALERT

        if flow.request.method.upper() != "POST":
            return
        if "majorlogin" not in flow.request.path.lower():
            return

        # ✅ total counter (SQLite)
        inc_stat("total")

        try:
            if flow.response is None or flow.response.content is None:
                return
            respBody = flow.response.content.hex()
            # Decode using new utils
            proto_json = get_available_room(respBody)
            proto_fields = json.loads(proto_json or "{}")
            
            uid = None
            for field_num in ["1", "2", "3"]:
                if field_num in proto_fields and isinstance(proto_fields[field_num], dict) and "data" in proto_fields[field_num]:
                    potential_uid = str(proto_fields[field_num]["data"])
                    if potential_uid.isdigit() and len(potential_uid) > 5:
                        uid = potential_uid
                        break

            print(f"[DEBUG] MajorLogin response — extracted UID: {uid!r} | proto_fields keys: {list(proto_fields.keys())}")

            if not uid:
                print("[DEBUG] No UID found in response — skipping")
                return # No UID found

            # ✅ client IP
            client_ip = None
            try:
                if flow.client_conn and flow.client_conn.peername:
                    client_ip = flow.client_conn.peername[0]
            except:
                pass

            # ✅ geo lookup (your existing helper)
            country, region, city = lookup_geo(client_ip)

            # ================= USERS JSON FAST-PATH =================
            _data = read_data()
            _users = _data.get("users", {})
            print(f"[DEBUG] JSON users keys: {list(_users.keys())}")
            print(f"[DEBUG] Checking if '{uid}' in users: {uid in _users}")
            if uid in _users:
                inc_stat("allowed")
                log_login_db(uid, client_ip, country, region, city, "USERS JSON ✅")
                print(f"[DEBUG] ALLOWED via users JSON")
                return

            # ================= BLACKLIST / UID CHECK =================
            blacklisted = uid in _data.get("blacklist", [])

            if blacklisted or not checkUIDExists(uid):
                inc_stat("blocked")
                blocked_times.append(time.time())

                log_login_db(uid, client_ip, country, region, city, "BLOCKED ❌")

    
                verification_message = (
                    f"[FF0000]⧉───────────────────────────────────────────────⧉\n"
                    f"[FF0000]           [FFFFFF]AdiCheats UID Verification\n"
                    f"[FF0000]⟡  INFO :   [FFFFFF]UID NOT AUTHORISED\n"
                    f"[FF0000]⟡  UID  :   [FFFFFF]{uid}\n"
                    f"[FF0000]⧉───────────────────────────────────────────────⧉\n"
                ).encode()

                if flow.response:
                    flow.response.content = verification_message
                    flow.response.status_code = 500
                return

            # ================= ALLOWED =================
            inc_stat("allowed")
            log_login_db(uid, client_ip, country, region, city, "ALLOWED ✅")
            # No auto-add needed — UIDs are managed exclusively via the Discord bot
            pass

        except Exception as e:
            print(f"Error processing MajorLogin response: {e}")

        # ===== GetAccountBriefInfoBeforeLogin nickname modifier =====
        if flow.request.method.upper() == "POST" and "/GetAccountBriefInfoBeforeLogin" in flow.request.path:
            try:
                if flow.response is None or flow.response.content is None:
                    return
                current_response = CSGetAccountBriefInfoBeforeLoginRes_pb2.CSGetAccountBriefInfoBeforeLoginRes() # type: ignore
                current_response.ParseFromString(flow.response.content)
                old_nickname = current_response.nickname
                current_response.nickname = (
                    f"[c][ff0000]{old_nickname}"
                )
                new_content = current_response.SerializeToString()
                if flow.response:
                    flow.response.content = new_content
                    flow.response.headers["Content-Length"] = str(len(new_content))
            except Exception as e:
                print(f"[GetAccountBriefInfo] Error modifying nickname: {e}")


addons = [MajorLoginInterceptor()]

# ===================== STARTUP =====================

if __name__ == "__main__":
    import os

    script_path = os.path.abspath(__file__).replace('\\', '\\\\')
    bot_path    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.py")

    port = os.environ.get("SERVER_PORT", "8082")
    print(f"[*] Starting mitmdump proxy on port {port}...")
    proxy_proc = subprocess.Popen(
        [
            sys.executable, "-c",
            f"import sys; from mitmproxy.tools.main import mitmdump; sys.argv = ['mitmdump', '-s', '{script_path}', '-p', '{port}', '--listen-host', '0.0.0.0', '--set', 'block_global=false']; mitmdump()",
        ],
        env=os.environ.copy(),
        cwd=os.path.dirname(os.path.abspath(__file__))   # run from backend folder
    )

    print("[*] Starting Discord bot (bot.py)...")
    bot_proc = subprocess.Popen(
        [sys.executable, bot_path],
        env=os.environ.copy(),
        cwd=os.path.dirname(os.path.abspath(__file__))
    )

    print("[*] Both services running. Press Ctrl+C to stop all.")

    try:
        # Wait for either process to exit
        while True:
            # If proxy dies, restart it (optional: just exit)
            if proxy_proc.poll() is not None:
                print("[!] Proxy process exited unexpectedly.")
                break
            if bot_proc.poll() is not None:
                print("[!] Bot process exited unexpectedly.")
                break
            import time as _time
            _time.sleep(2)

    except KeyboardInterrupt:
        print("\n[!] Shutting down all services...")

    finally:
        # Cleanly terminate both processes
        for proc, name in [(proxy_proc, "Proxy"), (bot_proc, "Discord Bot")]:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                    print(f"[✓] {name} stopped.")
                except subprocess.TimeoutExpired:
                    proc.kill()
                    print(f"[!] {name} force-killed.")

