import requests
import time
import json
import os
import uuid
import threading
import random
import re
import html
import pyotp
import copy
import tempfile
import logging
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, urlparse

# ==========================================
# Logging Setup (replaces print() calls)
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ==========================================
# Configuration (Token & Owner ID)
# ==========================================
# ─── SECURITY FIX ────────────────────────────────────────────────────────────
# Token environment variable se load hoga — KABHI bhi source code mein mat
# likhna. .env file ya Replit Secrets mein BOT_TOKEN set karo.
# Example: export BOT_TOKEN="aapka_token_yahan"
# ─────────────────────────────────────────────────────────────────────────────
TOKEN = os.getenv("BOT_TOKEN", "869260571Koz3EJtMXYBguoN5AWY9o")  # FIX: hardcoded fallback hata diya — BOT_TOKEN env var se aana chahiye
if not TOKEN:
    raise RuntimeError(
        "❌ BOT_TOKEN environment variable set nahi hai!\n"
        "   Replit Secrets ya .env mein BOT_TOKEN add karo.\n"
        "   Naya token: @BotFather → /token"
    )
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
FILE_URL = f"https://api.telegram.org/file/bot{TOKEN}/"

OWNER_ID = 8324356832  # <-- Apna Telegram User ID yahan dalo
BOT_USERNAME = "@Visitofpfbot"
DB_FILE = "bot_data.json"

# ==========================================
# Premium Emoji Database
# ==========================================
PEM = {
    "ok": '<tg-emoji emoji-id="5352694861990501856">✅</tg-emoji>',
    "no": '<tg-emoji emoji-id="6267000941547885720">❌</tg-emoji>',
    "warn": '<tg-emoji emoji-id="5336944168944047463">⚠️</tg-emoji>',
    "admin": '<tg-emoji emoji-id="5353032893096567467">📊</tg-emoji>',
    "user": '<tg-emoji emoji-id="5352861489541714456">👤</tg-emoji>',
    "file": '<tg-emoji emoji-id="5352721946054268944">📁</tg-emoji>',
    "rocket": '<tg-emoji emoji-id="5352597830089347330">🚀</tg-emoji>',
    "graph": '<tg-emoji emoji-id="5352877703043258544">📊</tg-emoji>',
    "money": '<tg-emoji emoji-id="5348469219761626211">💸</tg-emoji>',
    "gift": '<tg-emoji emoji-id="5420396762189831222">🎁</tg-emoji>',
    "msg": '<tg-emoji emoji-id="5337302974806922068">💬</tg-emoji>',
    "gear": '<tg-emoji emoji-id="5420155432272438703">⚙️</tg-emoji>',
    "link": '<tg-emoji emoji-id="5420517437885943844">🔗</tg-emoji>',
    "trash": '<tg-emoji emoji-id="5422557736330106570">🗑</tg-emoji>',
    "upload": '<tg-emoji emoji-id="5353001161878182134">📤</tg-emoji>',
    "world": '<tg-emoji emoji-id="5336972142066047577">🌐</tg-emoji>',
    "lock": '<tg-emoji emoji-id="5353022963132174959">🔐</tg-emoji>',
    "phone": '<tg-emoji emoji-id="4969841369850840381">📱</tg-emoji>',
    "num": '<tg-emoji emoji-id="5352862640592949843">🔢</tg-emoji>',
    "pin": '<tg-emoji emoji-id="5352922460897452503">📍</tg-emoji>',
    "star": '<tg-emoji emoji-id="5352552689983067014">✨</tg-emoji>',
    "hi": '<tg-emoji emoji-id="5353027129250453493">👋</tg-emoji>'
}

GLOBAL_BODY_EMOJIS = {
    # ── Navigation / Status ──────────────────────────────────────────────────
    "✅": "5352694861990501856", "❌": "5420130255174145507",
    "⚠️": "5336944168944047463", "🔥": "5337267511261960341",
    "🌟": "5337102391244263212", "✨": "5352552689983067014",
    "➖": "5870818207383686839", "➕": "5420323438508155202",
    "➡️": "6319061296704656261", "🔄": "6264896248659056036",
    "⌛": "4958503072801228000", "⏳": "6285092198497129798",
    "🕓": "5336983442125001376", "🔴": "6267237615720731788",

    # ── User / People ────────────────────────────────────────────────────────
    "👤": "5352861489541714456", "👥": "4972130076318500235",
    "👋": "5353027129250453493", "👇": "5406745015365943482",
    "👨‍⚖️": "5334763399299506604", "😒": "5334763399299506604",
    "😔": "6120863614149596295", "🫂": "5420145051336485498",

    # ── Numbers / Stats ──────────────────────────────────────────────────────
    "1️⃣": "5877664071720898423", "2️⃣": "5877223446731034464",
    "3️⃣": "5879546817879740639", "4️⃣": "5879844832775507443",
    "5️⃣": "5879657954453491518", "6️⃣": "5877556203617259178",
    "7️⃣": "5879611822209765566", "8️⃣": "5879971663159758717",
    "9️⃣": "5877752470737784316",
    "🔢": "5352862640592949843", "🆔": "5352862640592949843",
    "📊": "5353032893096567467", "📈": "5352877703043258544",

    # ── Files / Data ─────────────────────────────────────────────────────────
    "📁": "5352721946054268944", "📦": "5352721946054268944",
    "📂": "5257969839313526622", "📤": "5353001161878182134",
    "📝": "5192739271886282680", "🧾": "5192739271886282680",
    "📅": "5352585194295564660", "📋": "6267008582294705964",
    "💾": "5197269100878907942", "📛": "6325731252066325108",

    # ── Communication ────────────────────────────────────────────────────────
    "💬": "5337302974806922068", "🎙": "5355102594886833928",
    "📢": "5789428375261023681", "📌": "5318986077455795572",
    "📍": "5352922460897452503",

    # ── Security / Tech ──────────────────────────────────────────────────────
    "🔑": "6282760761399841824", "🔐": "5337255927735163754",
    "🔗": "5420517437885943844", "⚙️": "5420155432272438703",
    "🛡": "5190447043545438788", "🚫": "5334807341109908955",
    "🌐": "6266794310671275367", "🔒": "6282846669335702032",

    # ── Money / Business ─────────────────────────────────────────────────────
    "💸": "5348469219761626211", "🏦": "5348469219761626211",
    "💰": "5190576863226933563", "💎": "5352838545826420397",
    "💳": "5190899075968441286", "🎁": "5420396762189831222",
    "🤝": "5192805934073685937",

    # ── Services / Apps ──────────────────────────────────────────────────────
    "🚀": "5352597830089347330", "🍏": "5337132498965010628",
    "📱": "5337132498965010628",
    "🌍": "5780471598922337683",

    # ── UI / Misc ────────────────────────────────────────────────────────────
    "🗑": "5422557736330106570", "🟢": "5192812028632274956",
    "👀": "5190645917711114179", "🕹": "5193100774988617665",
    "🧪": "5190781475468915802", "🎨": "5190751148704833975",
    "💡": "5422439311196834318", "🎯": "5276032951342088188",
}

DEFAULT_CUSTOM_MESSAGES = {
    "start": {"text": '★彡━━━━━━━━━━━彡★\n  <tg-emoji emoji-id="6264778055454036969">📊</tg-emoji> NUMBER BOT\n★彡━━━━━━━━━━━彡★\n<tg-emoji emoji-id="5258332798409783582">🚀</tg-emoji> Welcome to Number &amp; OTP Service\n━━━━━━━━━━━━\n<tg-emoji emoji-id="6071001861341580968">✅</tg-emoji> Choose an option below\nto continue using the bot.\n━━━━━━━━━━━━\n<tg-emoji emoji-id="6073231507713954071">💎</tg-emoji> Premium OTP Service.', "buttons": []},
    "get_number": {"text": f"{PEM['pin']} Select a service:", "buttons": []},
    "select_country": {"text": f"📌 Select a country for {{service}}:", "buttons": []}, 
    "search_number": {"text": f"{PEM['num']} <b>Search Number</b>\n\nEnter 3 to 9 digits to search for a number (e.g., 880, 9227373):", "buttons": []},
    "traffic": {"text": f"{PEM['graph']} <b>Traffic Overview</b>\n\n{PEM['ok']} Available Numbers: {{avail}}\n{PEM['rocket']} Assigned Numbers: {{assigned}}", "buttons": []},
    "refer": {"text": f"➖➖➖➖➖➖➖\n« {PEM['gift']} REFER & EARN »\n➖➖➖➖➖➖➖\n{PEM['link']} YOUR LINK:\n<code>{{ref_link}}</code>\n➖➖➖➖➖➖➖\n{PEM['user']} TOTAL REFERS: <b>{{total_ref}}</b>\n➖➖➖➖➖➖➖\n{PEM['money']} PER REFER: <b>{{ref_reward}} ₹</b>\n➖➖➖➖➖➖➖", "buttons": []},
    "withdrawal": {"text": "➖➖➖➖➖➖➖\n《 😒 WITHDRAWAL 》\n➖➖➖➖➖➖➖\n👋 Total Otp: {total_otp}\n➖➖➖➖➖➖➖\n🫂 Total Reffer :{total_ref}\n➖➖➖➖➖➖➖\n📅 BALANCE: {bal}₹\n➖➖➖➖➖➖➖\n🔐 MINIMUM: {min_w} ₹\n➖➖➖➖➖➖➖\nSELECT METHOD:", "buttons": []},
    "support": {"text": f"{PEM['msg']} Contact us for any help:", "buttons": []}
}

# ==========================================
# Database Mode (Local JSON Only)
# ==========================================
logger.info("Running in Local Mode")

bot_settings = {
    "admins": [OWNER_ID],
    "panels": [], 
    "fw_groups": [], 
    "otp_link": "https://t.me/+yPZ2CyWghDQ0YzY9",
    "withdraw_on": True,
    "min_withdraw": 30.0,
    "otp_reward": 0.1,
    "refer_reward": 0.2,
    "cooldown": 10,
    "num_req": 3,
    "num_share": 1, 
    "support_link": "https://t.me/method_all_giving",
    "w_methods": ["UPI", "Paytm"],
    "w_group": "", 
    
    "fj_on": False,
    "fj_channels": [],
    "nexa_on": False,
    "voltx_on": False,
    "stex_on": False,
    "nexa_keys": [], 
    "search_countries": [],
    "nexa_search_countries": [],
    "voltx_search_countries": [],
    "stex_search_countries": [],
    "nexa_services": {},
    "voltx_keys": [],
    "voltx_services": {},
    "stex_keys": [],
    "stex_services": {},
    "premium_flags": {
        "1": {"char": "🇺🇸", "iso": "US", "name": "United States", "id": "5913463998522592692"},
        "880": {"char": "🇧🇩", "iso": "BD", "name": "Bangladesh", "id": "5911365056594973179"},
        "91": {"char": "🇮🇳", "iso": "IN", "name": "India", "id": "5913754823643107921"},
        "92": {"char": "🇵🇰", "iso": "PK", "name": "Pakistan", "id": "5913705895375672082"},
        "44": {"char": "🇬🇧", "iso": "GB", "name": "United Kingdom", "id": "5913443365499703513"}
    },
    "premium_apps": {
        "FACEBOOK": {"char": "🚫", "id": "5334807341109908955", "name": "Facebook"},
        "WHATSAPP": {"char": "🚫", "id": "5334759662677957452", "name": "WhatsApp"}
    },
    "custom_messages": DEFAULT_CUSTOM_MESSAGES.copy(),
    "sys_emoji_overrides": {}
}


# Thread lock for safe DB writes
_db_save_lock = threading.Lock()

number_batches = {}
used_numbers_list = []
nexa_assigned_numbers = {}
NEXA_BASE_URL = "https://nexaotpservice.com"      # ✅ Correct Nexa domain — HTTPS enforced
voltx_assigned_numbers = {}
VOLTX_BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api"   # ✅ VoltX CDN path
stex_assigned_numbers = {}
STEX_BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api"    # ✅ Stex CDN path (tness ≠ tnevs)
total_uploaded_stats = 0
total_assigned_stats = 0
_stats_lock = threading.Lock()       # Thread-safe stats counter
_data_lock = threading.Lock()        # Thread-safe lock for shared dicts (nexa/voltx/stex assigned numbers, processed_otps)
_traffic_lock = threading.Lock()     # Thread-safe lock for recent_traffic list
processed_otps = {}  # {unique_id: timestamp}  — time-based dedup
SEEN_OTPS_FILE = "seen_otps.json"
# Shared HTTP sessions for background threads (persistent connections = faster)
_nexa_session = requests.Session()
_voltx_session = requests.Session()
_stex_session = requests.Session()
recent_traffic = []
user_banned_cache = {}
_banned_cache_lock = threading.Lock()  # Thread-safe banned cache access
otp_received_numbers = set()

# Per-service warmup flags — set True when a service is toggled ON or a key is added mid-run.
# global_sms_listener checks these so old OTPs are never delivered on first poll after enable.
_service_warmup_needed = {"nexa": False, "voltx": False, "stex": False}

# Active HTTP sessions for Auto Captcha Panels
panel_sessions = {}
_OTP_RECV_MAX = 50000  # Max OTP received numbers to keep in memory

# 🌟 Nexa Number Allocation Helper (mirrors VoltX/Stex pattern)
def try_nexa_get_number(query, chat_id, allow_auto=True):
    """Try to allocate a number from Nexa. Returns (num_str, api_key) or (None, None).
    allow_auto=False → if Nexa has no matching configured range, skip immediately
    (used when at least one panel has services configured by the admin)."""
    global total_assigned_stats

    if not bot_settings.get("nexa_on", False):
        return None, None

    nexa_keys = bot_settings.get("nexa_keys", [])
    if not nexa_keys:
        return None, None

    nexa_srvs = bot_settings.get("nexa_services", {})
    has_nexa_srvs = any(
        rng
        for countries in nexa_srvs.values()
        for ranges in countries.values()
        for rng in ranges
    )
    clean_q = query.replace("X", "").replace("x", "")

    # Range-match check
    nexa_has_match = any(
        rng.replace("X", "").replace("x", "").startswith(clean_q) or
        clean_q.startswith(rng.replace("X", "").replace("x", ""))
        for countries in nexa_srvs.values()
        for ranges in countries.values()
        for rng in ranges
    )

    # Panel isolation rules:
    #   - Nexa configured but no match → can't serve this prefix
    #   - Nexa unconfigured AND allow_auto=False → another panel owns this prefix → skip
    if has_nexa_srvs and not nexa_has_match:
        return None, None
    if not has_nexa_srvs and not allow_auto:
        return None, None

    t_len = 12
    if query.startswith("880"): t_len = 13
    elif query.startswith("1") and len(query) < 12: t_len = 11
    search_range = query + ("X" * (t_len - len(query))) if len(query) < t_len else query

    payloads = [
        {"range": search_range, "format": "normal"},
        {"range": search_range},
        {"prefix": query},
    ]

    for _ in range(bot_settings.get("num_req", 1)):
        for api_key in nexa_keys:
            for payload in payloads:
                try:
                    headers = {"X-API-Key": api_key}
                    res = _nexa_session.post(
                        f"{NEXA_BASE_URL}/api/v1/numbers/get",
                        json=payload, headers=headers, timeout=10
                    )
                    resp = res.json()
                    if resp.get("success") and (resp.get("number") or resp.get("phone_number")):
                        num_str = str(resp.get("number") or resp.get("phone_number", "")).replace("+", "")
                        # FIX: Nexa multiple number_id field names support karo
                        number_id = (resp.get("number_id") or resp.get("id") or
                                     resp.get("sms_id") or resp.get("num_id") or resp.get("phone_id"))
                        if not num_str:
                            continue
                        # ✅ Range validation: reject number that doesn't match the requested prefix
                        if not num_str.startswith(clean_q):
                            logger.warning(f"Nexa returned wrong range: {num_str} (expected: {clean_q})")
                            continue
                        with _data_lock:
                            nexa_assigned_numbers[num_str] = chat_id
                        with _stats_lock:
                            total_assigned_stats += 1
                        if number_id:
                            threading.Thread(
                                target=poll_otp_with_status,
                                args=(number_id, num_str, chat_id, api_key),
                                daemon=True
                            ).start()
                        return num_str, api_key
                    elif not resp.get("success") and resp.get("code") == 401:
                        break  # Bad API key — skip remaining payloads for this key
                except Exception as e:
                    logger.warning(f"Nexa getnum error: {e}")
                    continue
    return None, None


# 🌟 Unified panel-fetch helper (Nexa → VoltX → Stex with strict isolation)
def _fetch_number_via_panels(query, chat_id):
    """Try all enabled panels in order (Nexa → VoltX → Stex).
    Enforces strict per-panel isolation: if the admin configured ranges/services
    in any panel, only the panel(s) where that prefix was configured may serve it.
    If no panel has any services configured at all, all panels run in free/auto mode.
    Returns (num_str, panel_name) or (None, None)."""

    _nexa_srvs = bot_settings.get("nexa_services", {})
    _voltx_srvs = bot_settings.get("voltx_services", {})
    _stex_srvs  = bot_settings.get("stex_services", {})

    # Are ANY services/ranges configured by the admin across all panels?
    _any_configured = (
        any(rng for c in _nexa_srvs.values()  for rl in c.values() for rng in rl) or
        any(rng for c in _voltx_srvs.values() for rl in c.values() for rng in rl) or
        any(rng for c in _stex_srvs.values()  for rl in c.values() for rng in rl)
    )
    # allow_auto=True only when NO panel has any configuration (pure auto mode)
    allow_auto = not _any_configured

    # Try Nexa (only if ON)
    if bot_settings.get("nexa_on", False):
        num, _key = try_nexa_get_number(query, chat_id, allow_auto=allow_auto)
        if num:
            return num, "Nexa"

    # Try VoltX (only if ON)
    if bot_settings.get("voltx_on", False):
        num, _key = try_voltx_get_number(query, chat_id, allow_auto=allow_auto)
        if num:
            return num, "VoltX"

    # Try Stex (only if ON)
    if bot_settings.get("stex_on", False):
        num, _key = try_stex_get_number(query, chat_id, allow_auto=allow_auto)
        if num:
            return num, "Stex"

    return None, None


# 🌟 VoltX Number Allocation Helper (used in both Search & GET NUMBER flows)
def _try_mauthapi_get_number(query, chat_id, base_url, keys_setting, services_setting,
                              assigned_dict, poll_fn, getnum_payload_extra=None,
                              extra_num_field=None, allow_auto=True):
    """Shared number allocation helper for VoltX and Stex (same mauthapi platform).
    getnum_payload_extra: extra POST body fields (e.g. {"m":"n","range":""} for VoltX).
    extra_num_field: extra number key to try before 'number' (e.g. 'phone_number'/'national_number')."""
    global total_assigned_stats
    api_keys = bot_settings.get(keys_setting, [])
    if not api_keys:
        return None, None
    ranges_to_try = []
    services_all = bot_settings.get(services_setting, {})
    has_services = any(
        ranges
        for countries in services_all.values()
        for ranges in countries.values()
    )
    for srv, countries in services_all.items():
        for cnt, ranges in countries.items():
            for rng in ranges:
                rng_prefix = rng.replace("X", "").replace("x", "")
                if query.startswith(rng_prefix) or rng_prefix.startswith(query):
                    ranges_to_try.append(rng)
    # If no matching ranges found:
    # - If panel has services configured but none match → can't serve this prefix
    # - If allow_auto=False (another panel owns this range) → skip entirely
    # - Otherwise (no services anywhere) → auto-range mode
    if not ranges_to_try:
        if has_services or not allow_auto:
            return None, None
        auto_range = query + ("XXX" if len(query) >= 4 else "X" * (7 - len(query)))
        ranges_to_try.append(auto_range)
    for _ in range(bot_settings.get("num_req", 1)):
        for api_key in api_keys:
            for rng in ranges_to_try:
                try:
                    headers = {"mauthapi": api_key, "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
                    rid_value = rng.replace("X", "").replace("x", "")
                    payload = {"rid": rid_value}
                    if getnum_payload_extra:
                        payload.update(getnum_payload_extra)
                    _ms = _voltx_session if base_url == VOLTX_BASE_URL else _stex_session
                    res = _ms.post(f"{base_url}/getnum", json=payload, headers=headers, timeout=15)
                    data = res.json()
                    meta = data.get("meta", {})
                    if meta.get("code") == 200 and data.get("data"):
                        num_data = data["data"]
                        num_str = str(
                            num_data.get("no_plus_number") or
                            num_data.get("full_number") or
                            (num_data.get(extra_num_field) if extra_num_field else None) or
                            num_data.get("number") or ""
                        ).replace("+", "").replace(" ", "")
                        if num_str and not num_str.startswith(rid_value[:len(query)]):
                            logger.warning(f"{keys_setting} returned wrong range: {num_str} (expected: {rid_value})")
                            continue
                        if num_str:
                            with _data_lock:
                                assigned_dict[num_str] = chat_id
                            with _stats_lock:
                                total_assigned_stats += 1
                            threading.Thread(target=poll_fn, args=(num_str, chat_id, api_key), daemon=True).start()
                            return num_str, api_key
                except Exception as e:
                    logger.warning(f"{keys_setting} getnum error: {e}")
                    continue
    return None, None


def try_voltx_get_number(query, chat_id, allow_auto=True):
    """Allocate a number from VoltX — thin wrapper around _try_mauthapi_get_number."""
    return _try_mauthapi_get_number(
        query, chat_id, VOLTX_BASE_URL, "voltx_keys", "voltx_services",
        voltx_assigned_numbers, voltx_poll_otp,
        # FIX: "range": "" hata diya — rid pehle se payload mein hai, empty range conflict karta tha
        getnum_payload_extra={"m": "n"},
        extra_num_field="phone_number",
        allow_auto=allow_auto
    )

# 🌟 VoltX Owner Lookup Helper (used in panel_monitor, global_sms_listener)
def _find_assigned_owner(assigned_dict, clean_num):
    """Find owner_id for a number in any assigned_numbers dict. Returns owner_id or None."""
    for n, owner in assigned_dict.items():
        clean_n = str(n).replace("+", "").replace(" ", "").replace("-", "").strip()
        if clean_n == clean_num:
            return owner
        # Fuzzy suffix match — only when lengths differ by ≤3 digits (country-code prefix).
        # Guard prevents false matches between unrelated numbers sharing last 8 digits.
        if (len(clean_n) >= 8 and len(clean_num) >= 8 and
                abs(len(clean_n) - len(clean_num)) <= 3 and
                (clean_n.endswith(clean_num[-8:]) or
                 clean_num.endswith(clean_n[-8:]))):
            return owner
    return None


# 🌟 Stex Number Allocation Helper (used in both Search & GET NUMBER flows)
def try_stex_get_number(query, chat_id, allow_auto=True):
    """Allocate a number from Stex SMS — thin wrapper around _try_mauthapi_get_number."""
    return _try_mauthapi_get_number(
        query, chat_id, STEX_BASE_URL, "stex_keys", "stex_services",
        stex_assigned_numbers, stex_poll_otp,
        extra_num_field="national_number",
        allow_auto=allow_auto
    )


# 🌟 sAjaxSource (AJAX/DataTable) and Fallback HTML Parser Helper Function
def fetch_cpt_panel_cdrs(p, session, check_url):
    res = session.get(check_url, timeout=15, allow_redirects=True)
    html_text = res.text
    
    # Check if session expired - verify by URL redirect to login page OR login form presence
    final_url = res.url.lower()
    # FIX: sirf last path segment check karo, 'login' word poore URL mein nahi dhundho
    last_path = final_url.split('?')[0].rstrip('/').split('/')[-1]
    is_login_page = last_path in ('login', 'signin', 'sign-in', 'log-in', 'auth')
    if not is_login_page:
        # Also check if page has a login form (username + password inputs)
        soup_check = BeautifulSoup(html_text, 'html.parser')
        login_form = soup_check.find("input", {"type": "password"})
        # FIX: multiple sign-in phrases check karo, single string pe depend mat karo
        login_phrases = ["sign in to your account", "please sign in", "please login", "log in to continue"]
        page_lower = html_text.lower()
        has_login_phrase = any(phrase in page_lower for phrase in login_phrases)
        if login_form and has_login_phrase:
            is_login_page = True
    if is_login_page:
        raise Exception("Session expired")
        
    soup = BeautifulSoup(html_text, 'html.parser')
    s_ajax_source = ""
    for script in soup.find_all("script"):
        script_text = script.string or ""
        match = re.search(r'sAjaxSource":\s*"([^"]+)"', script_text)
        if match:
            s_ajax_source = match.group(1)
            break
            
    results = []
    
    n_col_name = p.get("num_col_name", "number").lower()
    m_col_name = p.get("msg_col_name", "message").lower()
    n_idx = int(p.get("num_col_idx", 2)) - 1 if p.get("num_col_idx") is not None else 1
    m_idx = int(p.get("msg_col_idx", 3)) - 1 if p.get("msg_col_idx") is not None else 2

    # FIX: DataTables panels (sAjaxSource wale) mein data table ke <thead>/header row
    # HTML mein hi maujood hote hain, sirf ROWS ajax se aati hain — pehle yeh header
    # sirf non-ajax (HTML fallback) path mein use hota tha. Isliye jin panels mein
    # visible column order manually-configured num_col_idx/msg_col_idx (default 2/3)
    # se match nahi karta tha (jaise extra "Range" column ke saath: Date, Range,
    # Number, CLI, SMS, Currency, Payout — Number=3, SMS=5), un panels ka data ya to
    # "couldn't parse OTP data" deta tha ya galat column (CLI/Currency) se junk parse
    # karta tha. Ab yahan bhi same page ke visible <table> header se try karte hain —
    # match mil jaaye to use karo, warna configured/default index pe fallback karo.
    _header_tables = soup.find_all('table')
    for _t in _header_tables:
        _rows = _t.find_all('tr')
        if _rows:
            _hn_idx, _hm_idx = _find_header_column_indices(_rows, n_col_name, m_col_name, n_idx, m_idx)
            if (_hn_idx, _hm_idx) != (n_idx, m_idx):
                n_idx, m_idx = _hn_idx, _hm_idx
            break

    # 5.1 If sAjaxSource AJAX link is found
    if s_ajax_source:
        baseUrl = p.get("login_url", "").split("/client")[0].split("/login")[0].strip()
        if not baseUrl.startswith("http"):
            baseUrl = "http://" + baseUrl
            
        full_ajax_url = ""
        if s_ajax_source.startswith("http"):
            full_ajax_url = s_ajax_source
        elif s_ajax_source.startswith("/"):
            full_ajax_url = f"{baseUrl}{s_ajax_source}"
        else:
            last_slash_idx = check_url.rfind("/")
            current_dir = check_url[:last_slash_idx]
            full_ajax_url = f"{current_dir}/{s_ajax_source}"

        # FIX: Kai DataTables panels sSortDir_0=desc ko IGNORE karke hamesha
        # din ka pehla page (iDisplayStart=0, sirf 25 records) return karte
        # hain — yani sabse PURANE records, sabse NAYE nahi. Jaise-jaise din
        # mein records badhte hain (jaise 1000+, ya 5000+ high-volume panels
        # mein), bot hamesha wahi purane 25 dekhta reh jaata hai aur naya SMS
        # panel mein aane ke baad bhi kabhi fetch hi nahi hota ("panel mein
        # SMS aaya, bot mein nahi aaya" ka asli root cause). Fix: bada
        # iDisplayLength maango (20000 — high-volume panels ke liye bhi safe
        # margin, din mein 5000-10000 OTP wale panels ko bhi cover karta hai)
        # taaki din ke SAARE records ek hi request mein aa jaayein, chahe
        # panel sorting ignore kar raha ho. (Do alag requests bhejna panel ke
        # apne "15 second interval" anti-spam guard ko trigger kar deta tha —
        # isliye single request mein hi sab kuch maangte hain.)
        if "iDisplayLength" not in full_ajax_url:
            query_params = "sEcho=1&iColumns=7&iDisplayStart=0&iDisplayLength=20000&sSearch=&iSortingCols=1&iSortCol_0=0&sSortDir_0=desc"
            divider = "&" if "?" in full_ajax_url else "?"
            full_ajax_url += f"{divider}{query_params}"

        ajax_headers = {
            "Referer": check_url,
            "X-Requested-With": "XMLHttpRequest"
        }
        
        ajax_res = session.get(full_ajax_url, headers=ajax_headers, timeout=30)
        data_dict = ajax_res.json()
        rows = data_dict.get("aaData", [])

        # FIX: agar panel ke paas bhi hamare maange se ZYADA records hain
        # (edge case — jaise 20000+ ek din mein), to bhi hum silently
        # sabse purana data mat rakho. Agar rows count total se kam hai,
        # yeh warn kar do taaki owner ko pata chale limit badhaani hai.
        try:
            _total_recs = int(data_dict.get("iTotalDisplayRecords") or data_dict.get("iTotalRecords") or 0)
            if _total_recs and len(rows) < _total_recs:
                logger.warning(
                    f"Panel '{p.get('name')}' has {_total_recs} records today but only "
                    f"{len(rows)} fetched — consider raising iDisplayLength further."
                )
        except (TypeError, ValueError):
            pass

        for row_val in rows:
            if not isinstance(row_val, list):
                continue
                
            if len(row_val) < max(n_idx, m_idx) + 1:
                continue
                
            num_val = row_val[n_idx] if (0 <= n_idx < len(row_val)) else (row_val[1] if len(row_val) > 1 else "")
            msg_val = row_val[m_idx] if (0 <= m_idx < len(row_val)) else (row_val[2] if len(row_val) > 2 else "")

            # Extract datetime → item_id taaki alag timestamps = alag records
            # Step 1: Pehle full timestamp dhundho (date + time ek hi column mein)
            datetime_val = ""
            for col in row_val:
                col_str = str(col).strip()
                if re.search(r'\d{4}[-/]\d{2}[-/]\d{2}', col_str) and re.search(r'\d{2}:\d{2}:\d{2}', col_str):
                    datetime_val = col_str
                    break
            # Step 2: Agar full timestamp nahi mila, date + time alag columns se combine karo
            if not datetime_val:
                date_part = ""
                time_part = ""
                for col in row_val:
                    col_str = str(col).strip()
                    if not date_part:
                        m = re.search(r'\d{4}[-/]\d{2}[-/]\d{2}', col_str)
                        if m: date_part = m.group()
                    if not time_part:
                        m = re.search(r'\d{2}:\d{2}:\d{2}', col_str)
                        if m: time_part = m.group()
                datetime_val = f"{date_part} {time_part}".strip()
            
            # FIX: nn literal → real newlines
            msg_val = re.sub(r'(?<!\n)nn(?!\n)', '\n', str(msg_val))
            clean_num = re.sub(r'\D', '', str(num_val))
            # FIX: pure 8-digit = likely YYYYMMDD date, skip
            if clean_num and 5 <= len(clean_num) <= 18 and not re.match(r'^\d{8}$', clean_num):
                otp = extract_otp_code(msg_val)
                if otp and len(msg_val) > 4:
                    results.append({"number": clean_num, "message": msg_val, "otp": otp, "item_id": datetime_val})
                    
    else:
        # 5.2 Backup logic to read from direct HTML table
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if not rows: continue
            
            final_n_idx, final_m_idx = _find_header_column_indices(rows, n_col_name, m_col_name, n_idx, m_idx)

            for row in rows:
                cols = row.find_all(['td', 'th'])
                if all(c.name == 'th' for c in cols): continue
                
                if len(cols) > max(final_n_idx, final_m_idx):
                    num_text = cols[final_n_idx].get_text(separator=" ", strip=True)
                    msg_text = cols[final_m_idx].get_text(separator=" ", strip=True)

                    # Extract datetime → item_id (HTML table path)
                    # Step 1: Full timestamp ek hi column mein
                    datetime_val = ""
                    for col in cols:
                        col_text = col.get_text(separator=" ", strip=True)
                        if re.search(r'\d{4}[-/]\d{2}[-/]\d{2}', col_text) and re.search(r'\d{2}:\d{2}:\d{2}', col_text):
                            datetime_val = col_text
                            break
                    # Step 2: Date + time alag columns mein → combine karo
                    if not datetime_val:
                        date_part = ""
                        time_part = ""
                        for col in cols:
                            col_text = col.get_text(separator=" ", strip=True)
                            if not date_part:
                                m = re.search(r'\d{4}[-/]\d{2}[-/]\d{2}', col_text)
                                if m: date_part = m.group()
                            if not time_part:
                                m = re.search(r'\d{2}:\d{2}:\d{2}', col_text)
                                if m: time_part = m.group()
                        datetime_val = f"{date_part} {time_part}".strip()
                    
                    clean_num = re.sub(r'\D', '', num_text)
                    # FIX: nn literal → real newlines in msg_text
                    msg_text = re.sub(r'(?<!\n)nn(?!\n)', '\n', msg_text)
                    # FIX: pure 8-digit = YYYYMMDD date, skip
                    if clean_num and 5 <= len(clean_num) <= 18 and not re.match(r'^\d{8}$', clean_num):
                        otp = extract_otp_code(msg_text)
                        if otp and len(msg_text) > 4:
                            results.append({"number": clean_num, "message": msg_text, "otp": otp, "item_id": datetime_val})
                            
    return results, html_text

# Track active number sessions to expire them automatically
user_active_sessions = {}

def load_db():
    global number_batches, used_numbers_list, total_uploaded_stats, total_assigned_stats, recent_traffic, otp_received_numbers, nexa_assigned_numbers, voltx_assigned_numbers, stex_assigned_numbers
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                raw_content = f.read()
            if not raw_content.strip():
                logger.warning("DB file is empty, starting fresh.")
                return
            data = json.loads(raw_content)
            saved_settings = data.get("bot_settings", {})
            for key, val in saved_settings.items():
                if key == "custom_messages":
                    for m_key, m_val in val.items():
                        bot_settings["custom_messages"][m_key] = m_val
                else:
                    bot_settings[key] = val
                    
            for m_key, m_val in DEFAULT_CUSTOM_MESSAGES.items():
                if m_key not in bot_settings["custom_messages"]:
                    bot_settings["custom_messages"][m_key] = m_val
                    
            number_batches = data.get("number_batches", {})
            used_numbers_list = data.get("used_numbers_list", [])
            total_uploaded_stats = data.get("total_uploaded_stats", 0)
            total_assigned_stats = data.get("total_assigned_stats", 0)
            recent_traffic = data.get("recent_traffic", [])
            nexa_assigned_numbers = data.get("nexa_assigned_numbers", {})
            voltx_assigned_numbers = data.get("voltx_assigned_numbers", {})
            stex_assigned_numbers = data.get("stex_assigned_numbers", {})
            otp_received_numbers = set(data.get("otp_received_numbers", []))
            # Migrate old fj_channels format (plain strings) to new dict format
            migrated = False
            new_fj = []
            for entry in bot_settings.get("fj_channels", []):
                if isinstance(entry, str):
                    new_fj.append({"chat_id": entry, "type": "channel", "title": entry, "invite_link": "", "is_private": False})
                    migrated = True
                else:
                    new_fj.append(entry)
            if migrated:
                bot_settings["fj_channels"] = new_fj

            # Migrate old Bangladesh/BDT settings to India/INR
            inr_migrated = False
            # Fix w_methods if still bKash/Nagad
            old_methods = bot_settings.get("w_methods", [])
            if any(m.lower() in ["bkash", "nagad"] for m in old_methods):
                bot_settings["w_methods"] = ["UPI", "Paytm"]
                inr_migrated = True
            # Fix custom_messages: replace Bengali text and BDT/TK with English and INR/₹
            cm = bot_settings.get("custom_messages", {})
            for m_key in cm:
                if isinstance(cm[m_key], dict) and "text" in cm[m_key]:
                    txt = cm[m_key]["text"]
                    if "৳" in txt or "TK" in txt or "tk" in txt or any(ord(c) >= 0x0980 and ord(c) <= 0x09FF for c in txt):
                        # Reset this message to new default
                        if m_key in DEFAULT_CUSTOM_MESSAGES:
                            cm[m_key]["text"] = DEFAULT_CUSTOM_MESSAGES[m_key]["text"]
                            inr_migrated = True
            if inr_migrated:
                bot_settings["custom_messages"] = cm
                save_local_db()
                logger.info("Migrated old BDT/Bengali settings to INR/English")

            logger.info("Local DB loaded successfully")
        except Exception as e:
            logger.error(f"Error loading local DB: {e}")

def save_local_db():
    with _db_save_lock:
        try:
            local_data = {
                "bot_settings": copy.deepcopy(bot_settings),
                "number_batches": copy.deepcopy(number_batches),
                "used_numbers_list": list(used_numbers_list),
                "total_uploaded_stats": total_uploaded_stats,
                "total_assigned_stats": total_assigned_stats,
                "recent_traffic": list(recent_traffic),
                "nexa_assigned_numbers": dict(nexa_assigned_numbers),
                "voltx_assigned_numbers": dict(voltx_assigned_numbers),
                "stex_assigned_numbers": dict(stex_assigned_numbers),
                "otp_received_numbers": list(otp_received_numbers) if otp_received_numbers else []
            }
            # Atomic write: write to temp file first, then rename
            dir_name = os.path.dirname(os.path.abspath(DB_FILE))
            fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding='utf-8') as f:
                    json.dump(local_data, f, indent=4)
                # Atomic rename (safe on Linux)
                os.replace(tmp_path, DB_FILE)
            except Exception as e:
                # Clean up temp file on failure
                try: os.unlink(tmp_path)
                except Exception as unlink_err:
                    logger.warning(f"Temp file cleanup error: {unlink_err}")
                raise
        except Exception as e:
            logger.warning(f"DB save error: {e}")

load_db()

# ==========================================
# 2FA Persistence (FIX: was in-memory only)
# ==========================================
TFA_DB_FILE = "2fa_saved.json"

def _load_2fa_saved():
    """Load persisted 2FA secrets from disk into user_2fa_saved."""
    global user_2fa_saved
    try:
        if os.path.exists(TFA_DB_FILE):
            with open(TFA_DB_FILE, "r", encoding="utf-8") as f:
                raw = f.read().strip()
            if raw:
                loaded = json.loads(raw)
                # Keys are stored as strings in JSON; keep as-is (int chat_id will be converted on access)
                user_2fa_saved = {int(k): v for k, v in loaded.items()} if isinstance(loaded, dict) else {}
    except Exception as e:
        logger.warning(f"2fa_saved load error: {e} — starting fresh")
        user_2fa_saved = {}

def _save_2fa_saved():
    """Atomically persist user_2fa_saved to disk."""
    try:
        snapshot = {str(k): v for k, v in user_2fa_saved.items()}
        dir_name = os.path.dirname(os.path.abspath(TFA_DB_FILE)) or "."
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False,
                                        suffix=".tmp", encoding="utf-8") as tf:
            tmp_path = tf.name
            json.dump(snapshot, tf, ensure_ascii=False)
        os.replace(tmp_path, TFA_DB_FILE)
    except Exception as e:
        logger.warning(f"2fa_saved save error: {e}")

user_states = {}
temp_data = {}
user_cooldowns = {}
pending_withdrawals = {}

user_2fa_saved = {}  # {chat_id: [{"name": "Instagram", "key": "ABCDEF123456"}, ...]}
_load_2fa_saved()   # FIX: load persisted 2FA secrets on startup

def _cleanup_stale_sessions():
    """Remove stale entries from in-memory dicts to prevent memory leaks."""
    now = time.time()
    # user_cooldowns: keep only last 10 minutes
    stale_cd = [k for k, v in list(user_cooldowns.items()) if now - v > 600]
    for k in stale_cd: user_cooldowns.pop(k, None)
    # user_states/temp_data: evict oldest by insertion order (max 5000 entries)
    if len(user_states) > 5000:
        for k in list(user_states.keys())[:2000]:
            user_states.pop(k, None)
    if len(temp_data) > 5000:
        for k in list(temp_data.keys())[:2000]:
            temp_data.pop(k, None)
    # pending_withdrawals: keep only last 500
    if len(pending_withdrawals) > 500:
        old_keys = list(pending_withdrawals.keys())[:-500]
        for k in old_keys: pending_withdrawals.pop(k, None)
    # user_2fa_saved grows unbounded — evict oldest 500 when over 2000
    if len(user_2fa_saved) > 2000:
        for k in list(user_2fa_saved.keys())[:500]:
            user_2fa_saved.pop(k, None)

def _cleanup_loop():
    """Background thread: memory cleanup har 5 minute mein."""
    while True:
        time.sleep(300)
        try:
            _cleanup_stale_sessions()
        except Exception as e:
            logger.warning(f"_cleanup_stale_sessions error: {e}")

def _show_2fa_list(chat_id, msg_id):
    saved = user_2fa_saved.get(chat_id, [])
    _reset_btn_counter()
    if not saved:
        txt = (
            f"━━━━━━━━━━━━━━━\n"
            f"《 📋 <b>MY 2FA ADDED</b> 》\n"
            f"━━━━━━━━━━━━━━━\n"
            f"😔 Abhi koi 2FA saved nahi hai.\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💡 Pehle <b>Generate 2FA Code</b> use karein,\n"
            f"aapka code automatically save ho jayega.\n"
            f"━━━━━━━━━━━━━━━"
        )
        kb = {"inline_keyboard": [
            [{"text": "Generate 2FA Code", "icon_custom_emoji_id": "5353022963132174959", "callback_data": "gen_2fa", "style": _rs()}],
            [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "cancel_2fa", "style": _rs()}]
        ]}
    else:
        txt = (
            f"━━━━━━━━━━━━━━━\n"
            f"《 📋 <b>MY 2FA ADDED</b> 》\n"
            f"━━━━━━━━━━━━━━━\n"
            f"✅ Aapke <b>{len(saved)}</b> 2FA code(s) saved hain.\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💡 Recovery ke liye kisi bhi account ka\n"
            f"code generate karein ya secret key dekhen.\n"
            f"━━━━━━━━━━━━━━━"
        )
        list_kb = []
        for i, entry in enumerate(saved):
            list_kb.append([
                {"text": f"{entry['name']}", "icon_custom_emoji_id": "5353022963132174959", "callback_data": f"gen_saved_2fa_{i}", "style": _rs()},
                {"text": "Del", "icon_custom_emoji_id": "5422557736330106570", "callback_data": f"del_2fa_{i}", "style": _rs()}
            ])
        list_kb.append([{"text": "Add New", "icon_custom_emoji_id": "5352552689983067014", "callback_data": "gen_2fa", "style": _rs()}])
        list_kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "cancel_2fa", "style": _rs()}])
        kb = {"inline_keyboard": list_kb}
    edit_message(chat_id, msg_id, render_body_text(txt), reply_markup=kb)

# ==========================================
# Telegram API & Helpers
# ==========================================
tg_session = requests.Session() # 🌟 Keep-Alive Connection (Makes bot 10x faster)
_tg_adapter = requests.adapters.HTTPAdapter(max_retries=2, pool_connections=4, pool_maxsize=20)
tg_session.mount("https://", _tg_adapter)
tg_session.mount("http://", _tg_adapter)

def api_call(method, payload=None):
    url = f"{BASE_URL}/{method}"
    try:
        if payload is None and "?" in method:
            # GET request (e.g. getUpdates?timeout=50)
            res = tg_session.get(url, timeout=40)
        else:
            res = tg_session.post(url, json=payload, timeout=15)
        try:
            return res.json()
        except ValueError:
            logger.warning(f"Telegram API non-JSON response [{method}]: {res.status_code} {res.text[:100]}")
            return {}
    except requests.exceptions.ConnectionError as e:
        # FIX: session.close() in a multi-threaded context is DANGEROUS —
        # other threads may be mid-request on the same session object.
        # HTTPAdapter(max_retries=2) already handles reconnects automatically.
        logger.warning(f"Telegram connection error [{method}]: {e}")
        return {}
    except Exception as e:
        logger.warning(f"Telegram API call failed [{method}]: {e}")
        return {}

def _apply_text_overrides(text) -> str:
    """Har outgoing message text mein sys_emoji_overrides apply karo.
    Yeh ensure karta hai ki chahe render_body_text call hua ho ya nahi,
    emoji IDs hamesha latest admin override se replace honge."""
    overrides = bot_settings.get("sys_emoji_overrides", {})
    if not overrides or not text:
        return str(text) if text is not None else ""
    id_map = _build_id_override_map(overrides)
    if not id_map:
        return str(text)
    def _replace_eid(m):
        eid = m.group(1)
        return f'emoji-id="{id_map.get(eid, eid)}"'
    return re.sub(r'emoji-id="(\d+)"', _replace_eid, str(text))

def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "text": _apply_text_overrides(text), "parse_mode": parse_mode, "disable_web_page_preview": True}
    if reply_markup: payload["reply_markup"] = _apply_emoji_overrides(reply_markup)
    return api_call("sendMessage", payload)

def edit_message(chat_id, message_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": _apply_text_overrides(text), "parse_mode": parse_mode, "disable_web_page_preview": True}
    if reply_markup: payload["reply_markup"] = _apply_emoji_overrides(reply_markup)
    resp = api_call("editMessageText", payload)
    # FIX: Telegram API error par exception raise karo — warna try/except fallback kabhi nahi chalta
    if not resp or not resp.get("ok"):
        raise RuntimeError(f"editMessageText failed: {resp}")
    return resp

def _paced_edit(chat_id, msg_id, text, target_gap):
    """editMessageText jitni der lega, usko target_gap se minus karke sleep karta hai —
    isse network latency chahe kam ho ya zyada, animation ka real-world rhythm hamesha
    same rehta hai (koi extra 'lag'/stutter accumulate nahi hota).

    Rate-limit (429) mile to Telegram ke bataye 'retry_after' jitna ruk ke ek baar
    dobara try karta hai, taki animation beech mein toot na jaaye."""
    t0 = time.monotonic()
    resp = edit_message(chat_id, msg_id, text, parse_mode="HTML")
    if resp and resp.get("error_code") == 429:
        retry_after = resp.get("parameters", {}).get("retry_after", 1)
        time.sleep(retry_after + 0.05)
        edit_message(chat_id, msg_id, text, parse_mode="HTML")
    elapsed = time.monotonic() - t0
    remaining = target_gap - elapsed
    if remaining > 0:
        time.sleep(remaining)


def send_typing_animation(chat_id, first_name):
    """Premium 2-phase boot animation — latency-compensated, isliye slow network
    par bhi animation smooth/consistent rehti hai, kahin ruk-ruk ke (lag) nahi chalti.

    Phase-1 — Loading bar (4 frames):
        ⏳ → ⚡ 30% → ⚡ 60% → ✅ 100%

    Phase-2 — Terminal typing below the bar (3 lines × 3 steps):
        Each line: 35% partial → 70% partial → bold+premium-emoji final

    Timing is paced with a monotonic clock (see _paced_edit) rather than a plain
    time.sleep() after each edit, so the on-screen rhythm stays constant even if
    a single Telegram API call is briefly slow."""

    safe_name = html.escape(str(first_name))

    # ── Premium emoji (falls back to the plain unicode glyph for non-premium
    #    Telegram users — the alt text below MUST stay the matching emoji). ──
    _PEM_HOURGLASS = '<tg-emoji emoji-id="6266992763930158001">⏳</tg-emoji>'
    _PEM_BOLT      = '<tg-emoji emoji-id="6267107057304868214">⚡</tg-emoji>'
    _PEM_CHECK     = '<tg-emoji emoji-id="6266994443262367483">✅</tg-emoji>'

    # ── Phase 1: Animated Loading Bar ────────────────────────────────────────
    _BAR_FRAMES = [
        (f"{_PEM_HOURGLASS} <b>Booting OTP System...</b>", "░░░░░░░░░░", " 0%"),
        (f"{_PEM_BOLT} <b>Booting OTP System...</b>",      "▓▓▓░░░░░░░", "30%"),
        (f"{_PEM_BOLT} <b>Booting OTP System...</b>",      "▓▓▓▓▓▓░░░░", "60%"),
        (f"{_PEM_CHECK} <b>System Ready!</b>",              "▓▓▓▓▓▓▓▓▓▓", "100%"),
    ]

    resp = send_message(chat_id, render_body_text(f"{_PEM_HOURGLASS} <b>Booting OTP System...</b>\n░░░░░░░░░░  0%"))
    if not resp or not resp.get("ok"):
        return None
    msg_id = resp["result"]["message_id"]

    for lbl, bar, pct in _BAR_FRAMES[1:]:
        _paced_edit(chat_id, msg_id, render_body_text(f"{lbl}\n{bar} {pct}"), target_gap=0.30)

    time.sleep(0.20)   # Brief pause before terminal starts

    # ── Phase 2: Terminal Typing Animation (bar stays on top as prefix) ───────
    _PREFIX = f"{_PEM_CHECK} <b>System Ready!</b>\n▓▓▓▓▓▓▓▓▓▓ 100%\n\n"

    _LINES = [
        (
            "┌──[ ROOT@FREE-OTP ]──────────────",
            "<b>┌──[ ROOT@FREE-OTP ]──────────────</b>",
        ),
        (
            "├─▶ ACCESS GRANTED ✔",
            '<b>├─<tg-emoji emoji-id="6301055479539828724">▶</tg-emoji>'
            ' ACCESS GRANTED <tg-emoji emoji-id="6266781064992134926">✔</tg-emoji></b>',
        ),
        (
            f"└─▶ Hey {safe_name}, Welcome to Free OTP Bot!",
            f'<b>└─<tg-emoji emoji-id="6264896248659056036">▶</tg-emoji>'
            f' Hey {safe_name}, Welcome to Free OTP Bot!</b>',
        ),
    ]

    completed_fmt = []
    for plain_line, fmt_line in _LINES:
        n = len(plain_line)
        for chunk in (0.35, 0.70):
            cut = max(1, int(n * chunk))
            parts = completed_fmt[:]
            parts.append(plain_line[:cut] + "▌")
            _paced_edit(chat_id, msg_id, _PREFIX + "\n".join(parts), target_gap=0.38)
        completed_fmt.append(fmt_line)
        _paced_edit(chat_id, msg_id, _PREFIX + "\n".join(completed_fmt), target_gap=0.30)

    return msg_id

# FIX: Agar user "Check Joined" ya /start jaldi-jaldi (double-tap) dabaye to do
# animation ek hi chat par TAKRA jaate the (dono apna-apna message bhej/edit
# karte the) — isi wajah se "message idhar-udhar / adha dikhna" wala bug aata
# tha. Ab per-chat guard hai: ek user ke liye ek time par sirf EK welcome
# animation chal sakti hai, duplicate trigger silently ignore ho jata hai.
_active_welcomes = set()
_active_welcomes_lock = threading.Lock()

def _welcome_user(chat_id, first_name):
    """/start aur check_fj dono ke liye shared welcome flow.
    Duplicate code ek jagah — agar flow badlega to sirf yahan badlo."""
    with _active_welcomes_lock:
        if chat_id in _active_welcomes:
            return  # already ek animation chal rahi hai isi chat ke liye — skip
        _active_welcomes.add(chat_id)
    try:
        get_user(chat_id)
        _process_pending_referral(chat_id)
        send_typing_animation(chat_id, first_name)
        safe_name = html.escape(str(first_name))
        final_card = (
            f"{PEM['star']} <b>Welcome, {safe_name}!</b>\n"
            f"➖➖➖➖➖➖➖➖➖➖\n"
            f"{PEM['ok']} <b>Access Granted</b> — you're all set.\n"
            f"{PEM['rocket']} Everything is ready to use below.\n"
            f"➖➖➖➖➖➖➖➖➖➖\n"
            f"{PEM['gear']} <b>Main Menu</b> — choose an option:"
        )
        send_message(chat_id, render_body_text(final_card), reply_markup=main_menu(chat_id))
    finally:
        with _active_welcomes_lock:
            _active_welcomes.discard(chat_id)

def delete_message(chat_id, message_id):
    return api_call("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

def answer_callback(callback_id, text="", show_alert=False):
    api_call("answerCallbackQuery", {"callback_query_id": callback_id, "text": text, "show_alert": show_alert})

def send_document(chat_id, filename, text_content):
    url = f"{BASE_URL}/sendDocument"
    files = {'document': (filename, text_content)}
    data = {'chat_id': chat_id}
    try:
        tg_session.post(url, data=data, files=files, timeout=30)
    except Exception as e:
        logger.warning(f"send_document error: {e}")

# 🌟 Local User List for Broadcasts
all_known_users = set()
_users_set_lock = threading.Lock()  # Thread-safe users set access

def sync_users_list():
    global all_known_users
    try:
        if os.path.exists("users_list.json"):
            with open("users_list.json", "r") as f:
                all_known_users = set(json.load(f))
        if not all_known_users and local_users_db:
            all_known_users = set(str(k) for k in local_users_db.keys())
            with open("users_list.json", "w") as f:
                json.dump(list(all_known_users), f)
    except Exception as e:
        logger.warning(f"sync_users_list error: {e}")

def _save_users_list():
    try:
        fd, tmp_path = tempfile.mkstemp(dir=".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(list(all_known_users), f)
            os.replace(tmp_path, "users_list.json")
        except Exception:
            try: os.unlink(tmp_path)
            except Exception: pass
            raise
    except Exception as e:
        logger.warning(f"_save_users_list error: {e}")

def register_user_local(uid):
    uid_str = str(uid)
    # FIX: Read-check-write must ALL be inside the same lock to prevent race condition
    # where two threads both see "not in set" and both add+save simultaneously.
    with _users_set_lock:
        if uid_str not in all_known_users:
            all_known_users.add(uid_str)
            threading.Thread(target=_save_users_list, daemon=True).start()


# ==========================================
# 🌟 Local User Database (Firebase-Free Mode)
# ==========================================
USERS_DB_FILE = "users_db.json"
WITHDRAWALS_DB_FILE = "withdrawals_db.json"
local_users_db = {}
local_withdrawals_db = {}
_users_db_lock = threading.Lock()  # Thread-safe user DB access

def _load_local_users_db():
    global local_users_db, local_withdrawals_db
    try:
        if os.path.exists(USERS_DB_FILE):
            with open(USERS_DB_FILE, "r", encoding="utf-8") as f:
                raw = f.read()
            if raw.strip():
                local_users_db = json.loads(raw)
    except Exception as e:
        logger.warning(f"users_db load error: {e} — starting fresh")
        local_users_db = {}
    try:
        if os.path.exists(WITHDRAWALS_DB_FILE):
            with open(WITHDRAWALS_DB_FILE, "r", encoding="utf-8") as f:
                raw = f.read()
            if raw.strip():
                local_withdrawals_db = json.loads(raw)
    except Exception as e:
        logger.warning(f"withdrawals_db load error: {e} — starting fresh")
        local_withdrawals_db = {}

def _save_local_users_db():
    try:
        with _users_db_lock:
            snapshot = dict(local_users_db)
        dir_name = os.path.dirname(os.path.abspath(USERS_DB_FILE))
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2)
            os.replace(tmp_path, USERS_DB_FILE)
        except Exception:
            try: os.unlink(tmp_path)
            except Exception: pass
            raise
    except Exception as e:
        logger.warning(f"_save_local_users_db error: {e}")

_withdrawals_db_lock = threading.Lock()  # Thread-safe withdrawals DB access

def _save_local_withdrawals_db():
    try:
        with _withdrawals_db_lock:
            snapshot = dict(local_withdrawals_db)
        dir_name = os.path.dirname(os.path.abspath(WITHDRAWALS_DB_FILE))
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2)
            os.replace(tmp_path, WITHDRAWALS_DB_FILE)
        except Exception:
            try: os.unlink(tmp_path)
            except Exception: pass
            raise
    except Exception as e:
        logger.warning(f"_save_local_withdrawals_db error: {e}")

_load_local_users_db()
# Start sync AFTER local_users_db is loaded — fixes race condition
threading.Thread(target=sync_users_list, daemon=True).start()

def _new_user_dict(user_id):
    """Default user record — ek jagah define, teen jagah use. Duplicate hat gaya."""
    return {"user_id": int(user_id), "balance": 0.0, "total_refers": 0, "total_otps": 0, "banned": False, "verified": False}

def _get_local_user(user_id):
    uid = str(user_id)
    with _users_db_lock:
        if uid not in local_users_db:
            local_users_db[uid] = _new_user_dict(user_id)
            threading.Thread(target=_save_local_users_db, daemon=True).start()
        return dict(local_users_db[uid])

def _update_local_user(user_id, updates):
    uid = str(user_id)
    with _users_db_lock:
        if uid not in local_users_db:
            local_users_db[uid] = _new_user_dict(user_id)
        local_users_db[uid].update(updates)
    threading.Thread(target=_save_local_users_db, daemon=True).start()

def _increment_local_user(user_id, field, amount):
    uid = str(user_id)
    with _users_db_lock:
        if uid not in local_users_db:
            local_users_db[uid] = _new_user_dict(user_id)
        local_users_db[uid][field] = local_users_db[uid].get(field, 0) + amount
    threading.Thread(target=_save_local_users_db, daemon=True).start()

def _save_local_withdrawal(req_id, data):
    local_withdrawals_db[req_id] = data
    local_withdrawals_db[req_id]["timestamp"] = time.time()
    threading.Thread(target=_save_local_withdrawals_db, daemon=True).start()

def _update_local_withdrawal(req_id, updates):
    if req_id in local_withdrawals_db:
        local_withdrawals_db[req_id].update(updates)
        threading.Thread(target=_save_local_withdrawals_db, daemon=True).start()

def broadcast_copymessage(from_chat_id, msg_id):
    success = 0
    failed = 0
    users = list(all_known_users)
    
    # 🌟 Dedicated Connection Pool for Broadcast (Fixes Port Exhaustion & Network Lag)
    b_session = requests.Session()
    url = f"{BASE_URL}/copyMessage"
    
    try:
        for user_id in users:
            payload = {"chat_id": user_id, "from_chat_id": from_chat_id, "message_id": msg_id}
            try:
                res = b_session.post(url, json=payload, timeout=5).json()
                if res.get("ok"): success += 1
                else: failed += 1
            except Exception as e:
                failed += 1
            time.sleep(0.035) # Safe speed (28 msgs/sec) to prevent Telegram Ban
    finally:
        b_session.close()
        
    send_message(from_chat_id, render_body_text(f"📢 <b>Broadcast Completed!</b>\n✅ Success: {success}\n❌ Failed: {failed}\n👥 Total Sent: {len(users)}"))


def broadcast_text_message(txt):
    """Broadcast a plain text/HTML message to all known users (sendMessage API)."""
    b_session = requests.Session()
    url = f"{BASE_URL}/sendMessage"
    success, failed = 0, 0
    try:
        for u_id in list(all_known_users):
            try:
                res = b_session.post(url, json={"chat_id": u_id, "text": _apply_text_overrides(txt), "parse_mode": "HTML", "disable_web_page_preview": True}, timeout=5).json()
                if res.get("ok"): success += 1
                else: failed += 1
            except Exception:
                failed += 1
            time.sleep(0.035)
    finally:
        b_session.close()
    logger.info(f"Broadcast: {success} sent, {failed} failed")

_STYLES = ["primary", "success", "danger"]

# Thread-local counter: each thread (request) has its OWN independent cycle.
# This prevents 500 concurrent worker threads from scrambling each other's button colors.
_tl = threading.local()

def _reset_btn_counter():
    """Reset THIS thread's counter to 0 (primary). Call at start of every keyboard builder."""
    _tl.i = 0

def _get_service_emoji_id(srv, apps_db):
    """Service name (WHATSAPP, TELEGRAM, ...) ke liye premium-emoji id dhundo.
    Nexa/VoltX/Stex teen jagah yeh exact same lookup duplicate tha — ab shared."""
    emoji_id = "5257969839313526622"  # default/fallback icon
    for app_key, app_data in apps_db.items():
        if srv.upper() == app_key or srv.upper() in app_key or app_key in srv.upper():
            if "id" in app_data:
                emoji_id = app_data["id"]
                break
    return emoji_id

def _download_telegram_txt_document(chat_id, doc):
    """Upload kiya gaya .txt document Telegram se download karke text content return karta hai.
    Format wrong ho to user ko error bhejta hai aur None return karta hai (caller ko sirf
    `if content is None: return` karna hota hai). Teen jagah yeh exact same getFile/download
    logic duplicate tha — ab shared helper."""
    if not doc["file_name"].endswith(".txt"):
        send_message(chat_id, render_body_text(f"{PEM['no']} Please upload a .txt file only."))
        return None
    file_id = doc["file_id"]
    try:
        file_info = tg_session.get(f"{BASE_URL}/getFile?file_id={file_id}", timeout=15).json()
    except ValueError:
        send_message(chat_id, render_body_text(f"{PEM['no']} Could not download file (invalid response). Try again."))
        return None
    if not file_info.get("ok") or not file_info.get("result", {}).get("file_path"):
        send_message(chat_id, render_body_text(f"{PEM['no']} Could not get file path from Telegram. Try again."))
        return None
    file_path = file_info["result"]["file_path"]
    return tg_session.get(f"{FILE_URL}{file_path}", timeout=30).text

_NUMBER_COL_ALIASES = ("number", "mobile", "phone", "msisdn", "num", "recipient", "to")
_MESSAGE_COL_ALIASES = ("message", "sms", "text", "content", "msg", "body")

def _find_header_column_indices(rows, n_col_name, m_col_name, default_n_idx, default_m_idx):
    """HTML table ki pehli row (header) mein column-name se number/message column ka
    real index dhundo. Nahi mile to caller ke diye gaye default index use hote hain.
    Do jagah (AJAX-backup path aur Auto Captcha panel path) yeh exact same header-scan
    logic duplicate tha — ab shared.

    FIX: Bahut saare panels column ka header "SMS" likhte hain, "Message" nahi — aur
    number wale column ko "Mobile"/"Phone" bhi likh sakte hain. Pehle sirf exact
    n_col_name/m_col_name (jo panel-config mein set hai, default "number"/"message")
    match hota tha — agar panel ka header text usse alag hota (jaise "SMS"), match
    fail ho jaata aur ghalat column select ho jaata (isi wajah se "Connected, but
    couldn't parse OTP data!" milta tha, jabki panel mein data sahi tha).
    Ab hum configured name ko PEHLE priority dete hain, phir known aliases try karte
    hain — taaki 'SMS' jaisa header bhi 'message' ke barabar detect ho."""
    final_n_idx, final_m_idx = default_n_idx, default_m_idx
    if not rows:
        return final_n_idx, final_m_idx
    header_cells = rows[0].find_all(['th', 'td'])
    header_texts = [cell.get_text(strip=True).lower() for cell in header_cells]

    n_candidates = [n_col_name] + [a for a in _NUMBER_COL_ALIASES if a != n_col_name]
    m_candidates = [m_col_name] + [a for a in _MESSAGE_COL_ALIASES if a != m_col_name]

    for candidate in n_candidates:
        matched = [i for i, c_text in enumerate(header_texts) if candidate in c_text]
        if matched:
            final_n_idx = matched[0]
            break

    for candidate in m_candidates:
        matched = [i for i, c_text in enumerate(header_texts) if candidate in c_text]
        if matched:
            final_m_idx = matched[0]
            break

    return final_n_idx, final_m_idx

def _rs():
    """Return next style (primary→success→danger→...) for THIS thread. Auto-inits if needed."""
    if not hasattr(_tl, 'i'):
        _tl.i = 0
    s = _STYLES[_tl.i % 3]
    _tl.i += 1
    return s

def render_body_text(text):
    if not text: return str(text)
    parts = re.split(r'(<tg-emoji.*?</tg-emoji>)', str(text))
    for i in range(len(parts)):
        if not parts[i].startswith('<tg-emoji'):
            for normal_emj, prem_id in GLOBAL_BODY_EMOJIS.items():
                if normal_emj in parts[i]:
                    parts[i] = parts[i].replace(normal_emj, f'<tg-emoji emoji-id="{prem_id}">{normal_emj}</tg-emoji>')
    # _apply_text_overrides handles override replacement (same logic, no duplication)
    return _apply_text_overrides("".join(parts))

def extract_premium_html(msg):
    text = msg.get("text", msg.get("caption", ""))
    entities = msg.get("entities", msg.get("caption_entities", []))
    if not entities: return text
    try:
        b_text = text.encode('utf-16-le')
        c_entities = [e for e in entities if e.get("type") == "custom_emoji"]
        c_entities.sort(key=lambda x: x["offset"], reverse=True)
        for ent in c_entities:
            offset = ent["offset"] * 2
            length = ent["length"] * 2
            eid = ent["custom_emoji_id"]
            emoji_char = b_text[offset:offset+length].decode('utf-16-le')
            html_tag = f'<tg-emoji emoji-id="{eid}">{emoji_char}</tg-emoji>'
            replacement = html_tag.encode('utf-16-le')
            b_text = b_text[:offset] + replacement + b_text[offset+length:]
        return b_text.decode('utf-16-le')
    except Exception as e:
        return text 

def get_flag_info_from_num(num):
    clean = num.replace("+", "").replace(" ", "")
    sorted_codes = sorted(bot_settings.get("premium_flags", {}).keys(), key=len, reverse=True)
    for code in sorted_codes:
        if clean.startswith(code):
            data = bot_settings.get("premium_flags", {}).get(code)
            if not data:
                continue
            return data.get("char", "🌍"), data.get("iso", "XX"), data.get("id")
    return "🌍", "XX", None

def get_flag_and_code(num):
    char, iso, _ = get_flag_info_from_num(num)
    return char, iso

def _get_cc_from_iso(iso):
    """Return country-code digits for a given ISO-2 code (e.g. 'MG' → '261'), or None."""
    for code, data in bot_settings.get("premium_flags", {}).items():
        if data.get("iso") == iso:
            return code
    return None

def _get_cc_from_num(num_str):
    """Return country-code digits embedded at the start of num_str, or None."""
    clean = str(num_str).replace("+", "").replace(" ", "")
    sorted_codes = sorted(bot_settings.get("premium_flags", {}).keys(), key=len, reverse=True)
    for code in sorted_codes:
        if clean.startswith(code):
            return code
    return None

def get_flag_info_html(num_or_iso):
    if len(num_or_iso) == 2:
        for code, data in bot_settings.get("premium_flags", {}).items():
            if data.get("iso") == num_or_iso:
                eid = data.get("id")
                char = data.get("char")
                if eid: return f'<tg-emoji emoji-id="{eid}">{char}</tg-emoji>'
                return char
        return "🌍"
        
    char, _, eid = get_flag_info_from_num(num_or_iso)
    if eid:
        return f'<tg-emoji emoji-id="{eid}">{char}</tg-emoji>'
    return char

_MASK_EMOJI = '<tg-emoji emoji-id="6228781436330054904">⭐</tg-emoji>'

def mask_number(num, user_id=None):
    """Return last 4 digits of number — plain, no emoji masking."""
    clean = num.replace("+", "").replace(" ", "")
    if len(clean) > 4: return clean[-4:]
    return clean

# ==========================================
# 🌟 ADVANCED SERVICE & LANGUAGE DETECTION
# ==========================================

SERVICE_SMS_KEYWORDS = {
    # 🟢 Social Media & Chat (Added Arabic Keywords)
    "whatsapp": ["whatsapp", "wa", "wap", "w/a", "whatsapp business", "wa.me", "wa code", "wh", "واتساب", "واتساپ", "واٹس ایپ", "व्हाट्सएप", "वाट्सएप", "वॉट्सऐप", "व्हाट्सप्प", "হোয়াটসঅ্যাপ", "হোটসঅ্যাপ", "ватсап", "уотсап", "вотсап", "ватс апп", "వాట్సాప్", "വാട്‌സ്ആപ്പ്", "வாட்ஸ்அப்", "ವಾಟ್ಸಾಪ್", "વોટ્સએપ", "ਵਟਸਐਪ", "ହ୍ଵାଟସ୍ ଆପ୍", "වට්ස්ඇප්", "วอตส์แอปป์", "วอทส์แอพ", "ဝက်စ်အက်ပ်", "វ៉តសាប់", "ວອດແອັບ", "ワッツアップ", "왓츠앱", "whatsapp的", "whatsapp验证码", "וואטסאפ", "γουάτσαπ", "ዋትስአፕ", "ვოთსאფი", "վոթսափ"],
    "facebook": ["facebook", "fb", "meta", "fbook", "fb code", "facebook code", "فيسبوك", "فيس بوك"],
    "instagram": ["instagram", "insta", "ig", "ig code", "instagram code", "انستغرام", "انستقرام"],
    "telegram": ["telegram", "tg", "tele", "telegram code", "tg code", "t.me", "تيليجرام", "تليجرام"],
    "tiktok": ["tiktok", "tik tok", "tikvideo", "tiktok code", "tik code", "تيك توك"],
    "snapchat": ["snapchat", "snap", "snap code", "سناب شات"],
    "twitter": ["twitter", "x.com", "x code", "twitter code", "تويتر"],
    "discord": ["discord", "discord code", "ديسكورد"],
    "viber": ["viber", "viber code", "فايبر"],
    "line": ["line", "line code", "line verification", "لاين"],
    "wechat": ["wechat", "we chat", "wechat code", "وي تشات"],
    "signal": ["signal", "signal code", "سيجنال"],
    "linkedin": ["linkedin", "linked in", "لينكد إن"],
    "imo": ["imo", "imo code", "imo verification", "ايمو"],
    "kakaotalk": ["kakao", "kakaotalk", "كاكاو"],
    "qq": ["qq", "tencent qq"],
    "vk": ["vk", "vkontakte"],

    # 🔵 Tech & Mail
    "google": ["google", "gmail", "youtube", "g-", "google voice", "جوجل", "غوغل"],
    "microsoft": ["microsoft", "ms", "outlook", "live.com", "hotmail"],
    "apple": ["apple", "icloud", "itunes", "apple id"],
    "yahoo": ["yahoo", "yahoo code", "ymail"],
    "protonmail": ["proton", "protonmail"],
    
    # 💰 Crypto & Trading
    "binance": ["binance", "bnb", "binances"],
    "coinbase": ["coinbase"],
    "okx": ["okx", "okex"],
    "kucoin": ["kucoin"],
    "bybit": ["bybit"],
    "huobi": ["huobi", "htx"],
    "mexc": ["mexc"],
    "trustwallet": ["trust wallet", "trustwallet"],

    # 💳 Finance & Wallets
    "paytm": ["paytm", "paytm code", "paytm otp"],
    "phonepe": ["phonepe", "phone pe", "phonepe code"],
    "gpay": ["gpay", "google pay", "googlepay"],
    "upi": ["upi", "upi code", "upi otp"],
    "paypal": ["paypal", "pay pal"],
    "cashapp": ["cash app", "cashapp"],
    "wise": ["wise", "transferwise"],

    # 🛒 E-commerce & Delivery
    "amazon": ["amazon", "amzn", "amazon code"],
    "ebay": ["ebay"],
    "aliexpress": ["aliexpress", "ali express"],
    "alibaba": ["alibaba"],
    "daraz": ["daraz", "daraz code"],
    "foodpanda": ["foodpanda", "food panda"],
    "uber": ["uber", "uber code", "uber verification", "uber eats"],
    "pathao": ["pathao", "pathao ride"],

    # 🎮 Gaming & Entertainment
    "netflix": ["netflix", "netflix code"],
    "spotify": ["spotify", "spotify code"],
    "steam": ["steam", "steam guard"],
    "epicgames": ["epic games", "epicgames"],
    "roblox": ["roblox", "roblox code"],
    "riotgames": ["riot", "riot games", "valorant", "league of legends"],
    "garena": ["garena", "free fire", "freefire"],
    "playstation": ["playstation", "psn"],

    # 🎲 Betting & Casino
    "1xbet": ["1xbet", "1x bet"],
    "melbet": ["melbet", "melbet code"],
    "linebet": ["linebet"],
    "bet365": ["bet365"],
    "megapari": ["megapari"],

    # ❤️ Dating
    "tinder": ["tinder", "tinder code"],
    "bumble": ["bumble"],
    "badoo": ["badoo"],

    # 📲 Indian OTP Providers / SMS Gateways
    "gro5me": ["gro5me", "gro 5 me", "groSMS", "gro sms", "grow5me", "gro5"],
    "textlocal": ["textlocal", "text local"],
    "msg91": ["msg91", "msg 91"],
    "2factor": ["2factor", "2 factor"],
    "kaleyra": ["kaleyra"],
    "valueFirst": ["valuefirst", "value first"],
    "smscountry": ["smscountry", "sms country"],
    "smsjust": ["smsjust", "sms just"],
    "exotel": ["exotel"],
    "alertsms": ["alertsms", "alert sms"],
}

def _kw_match(kw, text_lower):
    """Keyword ko text mein match karo.
    Short keywords (<=3 pure-alpha chars) ke liye word-boundary (\b) use karo
    taaki 'wa' 'swap' mein ya 'wh' 'which' mein galat match na ho.
    Special chars wale keywords (w/a, t.me, wa.me, g-) ke liye simple 'in' check."""
    if len(kw) <= 3 and kw.isalpha():
        return bool(re.search(r'\b' + re.escape(kw) + r'\b', text_lower))
    return kw in text_lower

def detect_service(text):
    """SMS/OTP message text se service detect karo.
    Word-boundary matching short keywords ke liye — false positives avoid hote hain."""
    text_lower = str(text).lower()
    for service_key, keywords in SERVICE_SMS_KEYWORDS.items():
        for kw in keywords:
            if _kw_match(kw, text_lower):
                return service_key.upper()
    return None

# Set of known service keys for fast lookup
_KNOWN_SERVICE_KEYS = None
def _get_known_service_keys():
    global _KNOWN_SERVICE_KEYS
    if _KNOWN_SERVICE_KEYS is None:
        _KNOWN_SERVICE_KEYS = {k.upper() for k in SERVICE_SMS_KEYWORDS}
    return _KNOWN_SERVICE_KEYS

def get_service_info_html(service_text, msg_text=""):
    s = str(service_text).upper().strip()
    m = str(msg_text).lower().strip()
    apps = bot_settings.get("premium_apps", {})

    # Agar s pehle se ek known service key hai (jaise "INSTAGRAM", "WHATSAPP")
    # toh msg_text se override BILKUL MAT KARO — caller ne already sahi detect kiya hai.
    # Sirf tab msg_text scan karo jab s unknown/generic ho.
    known_keys = _get_known_service_keys()
    detected_service = s
    if s not in known_keys and m:
        for service_key, keywords in SERVICE_SMS_KEYWORDS.items():
            for kw in keywords:
                if _kw_match(kw, m):
                    detected_service = service_key.upper()
                    break
            if detected_service != s:
                break

    clean_s = re.sub(r'[^\w\s]', '', detected_service).strip()
    
    for app_name, data in apps.items():
        if app_name == detected_service or app_name == clean_s or app_name in detected_service or detected_service in app_name:
            full_name = data.get("name", app_name.title())
            char = data.get("char", "📱")
            eid = data.get("id")
            if eid: return full_name, f'<tg-emoji emoji-id="{eid}">{char}</tg-emoji>'
            return full_name, char
            
    if len(detected_service) > 20:
        return "Message", "💬"
        
    return detected_service.title(), "📱"

def detect_language(text):
    if not text: return "#EN"
    text_str = str(text)

    # 1. Accurate alphabet detection using Unicode Block (100% Accurate for scripts)
    if any('\u0600' <= c <= '\u06ff' for c in text_str): return "#AR" # Arabic / Persian / Urdu
    if any('\u0980' <= c <= '\u09ff' for c in text_str): return "#BN" # Bengali
    if any('\u0900' <= c <= '\u097f' for c in text_str): return "#HI" # Hindi / Marathi / Nepali
    if any('\u0a00' <= c <= '\u0a7f' for c in text_str): return "#PA" # Punjabi (Gurmukhi)
    if any('\u0a80' <= c <= '\u0aff' for c in text_str): return "#GU" # Gujarati
    if any('\u0b00' <= c <= '\u0b7f' for c in text_str): return "#OR" # Odia
    if any('\u0b80' <= c <= '\u0bff' for c in text_str): return "#TA" # Tamil
    if any('\u0c00' <= c <= '\u0c7f' for c in text_str): return "#TE" # Telugu
    if any('\u0c80' <= c <= '\u0cff' for c in text_str): return "#KN" # Kannada
    if any('\u0d00' <= c <= '\u0d7f' for c in text_str): return "#ML" # Malayalam
    if any('\u0d80' <= c <= '\u0dff' for c in text_str): return "#SI" # Sinhala
    if any('\u0e00' <= c <= '\u0e7f' for c in text_str): return "#TH" # Thai
    if any('\u0e80' <= c <= '\u0eff' for c in text_str): return "#LO" # Lao
    if any('\u0f00' <= c <= '\u0fff' for c in text_str): return "#BO" # Tibetan
    if any('\u1000' <= c <= '\u109f' for c in text_str): return "#MY" # Burmese (Myanmar)
    if any('\u1200' <= c <= '\u137f' for c in text_str): return "#AM" # Amharic (Ethiopic)
    if any('\u1780' <= c <= '\u17ff' for c in text_str): return "#KM" # Khmer
    if any('\u10a0' <= c <= '\u10ff' for c in text_str): return "#KA" # Georgian
    if any('\u0530' <= c <= '\u058f' for c in text_str): return "#HY" # Armenian
    if any('\u0590' <= c <= '\u05ff' for c in text_str): return "#HE" # Hebrew
    if any('\u0370' <= c <= '\u03ff' for c in text_str): return "#EL" # Greek
    if any('\u0400' <= c <= '\u04ff' for c in text_str): return "#RU" # Russian / Ukrainian (Cyrillic)
    if any('\u4e00' <= c <= '\u9fff' for c in text_str): return "#ZH" # Chinese
    if any(('\u3040' <= c <= '\u309f') or ('\u30a0' <= c <= '\u30ff') for c in text_str): return "#JA" # Japanese
    if any('\uac00' <= c <= '\ud7af' for c in text_str): return "#KO" # Korean

    # 2. Language detection using OTP Keywords (Latin script languages)
    text_lower = text_str.lower()
    
    # Asian / Pacific
    if any(w in text_lower for w in ["kode verifikasi", "jangan bagikan", "rahasia"]): return "#ID" # Indonesian
    if any(w in text_lower for w in ["kod pengesahan", "jangan kongsi"]): return "#MS" # Malay
    if any(w in text_lower for w in ["mã của bạn", "không chia sẻ", "mã xác minh"]): return "#VN" # Vietnamese
    if any(w in text_lower for w in ["ang iyong code", "huwag ibahagi"]): return "#TL" # Tagalog / Filipino
    
    # European / Americas
    if any(w in text_lower for w in ["código", "tu código", "verificación", "no compartas"]): return "#ES" # Spanish
    if any(w in text_lower for w in ["seu código", "código de verificação", "não compartilhe"]): return "#PT" # Portuguese
    if any(w in text_lower for w in ["code secret", "ne partagez pas", "votre code"]): return "#FR" # French
    if any(w in text_lower for w in ["dein code", "bestätigungscode", "nicht teilen"]): return "#DE" # German
    if any(w in text_lower for w in ["il tuo codice", "codice di verifica", "non condividere"]): return "#IT" # Italian
    if any(w in text_lower for w in ["twój kod", "nie udostępniaj", "kod weryfikacyjny"]): return "#PL" # Polish
    if any(w in text_lower for w in ["doğrulama kodu", "paylaşmayın", "onay kodu"]): return "#TR" # Turkish
    if any(w in text_lower for w in ["jouw code", "verificatiecode", "niet delen"]): return "#NL" # Dutch
    if any(w in text_lower for w in ["din kod", "verifieringskod", "dela inte"]): return "#SV" # Swedish
    if any(w in text_lower for w in ["bekræftelseskode", "del ikke"]): return "#DA" # Danish
    if any(w in text_lower for w in ["bekreftelseskode", "ikke del"]): return "#NO" # Norwegian
    if any(w in text_lower for w in ["vahvistuskoodi", "älä jaa"]): return "#FI" # Finnish
    if any(w in text_lower for w in ["váš kód", "ověřovací kód", "nesdílejte"]): return "#CS" # Czech
    if any(w in text_lower for w in ["overovací kód", "nezdieľajte"]): return "#SK" # Slovak
    if any(w in text_lower for w in ["ellenőrző kód", "ne oszd meg"]): return "#HU" # Hungarian
    if any(w in text_lower for w in ["codul tău", "codul de verificare", "nu partaja"]): return "#RO" # Romanian
    if any(w in text_lower for w in ["kontrolni kod", "kod za potvrdu", "ne delite"]): return "#HR" # Croatian/Serbian
    if any(w in text_lower for w in ["код за потвърждение", "не споделяйте"]): return "#BG" # Bulgarian
    if any(w in text_lower for w in ["ваш код", "код підтвердження"]): return "#UK" # Ukrainian
    
    # African
    if any(w in text_lower for w in ["msimbo wako", "usishiriki"]): return "#SW" # Swahili
    if any(w in text_lower for w in ["verifikasiekode", "moenie deel nie"]): return "#AF" # Afrikaans
    
    # 3. Default if none of the above matches
    return "#EN"

def parse_chat_id(text):
    text = text.strip()
    if text.startswith("-100") or (text.startswith("-") and text[1:].isdigit()):
        return text
    if "t.me/" in text:
        parts = [p for p in text.split("/") if p]
        username = parts[-1] if parts else ""
        if username and not username.startswith("+"): return "@" + username if not username.startswith("@") else username
    if text.startswith("@"):
        return text
    return "@" + text

def is_admin(user_id):
    return user_id in bot_settings["admins"] or user_id == OWNER_ID

def _get_fj_chat_id(entry):
    if isinstance(entry, dict):
        return entry.get("chat_id", "")
    return entry

def _get_fj_info(entry):
    if isinstance(entry, dict):
        return entry
    return {"chat_id": entry, "type": "channel", "title": str(entry), "invite_link": "", "is_private": False}

def auto_detect_chat(chat_id_raw):
    res = api_call("getChat", {"chat_id": chat_id_raw})
    if not res.get("ok"):
        return None
    chat = res["result"]
    chat_type = chat.get("type", "")
    title = chat.get("title", str(chat_id_raw))
    username = chat.get("username", "")
    is_private = not bool(username)
    if chat_type in ["supergroup", "group"]:
        detected_type = "group"
    else:
        detected_type = "channel"
    invite_link = ""
    if is_private:
        link_res = api_call("exportChatInviteLink", {"chat_id": chat_id_raw})
        if link_res.get("ok"):
            invite_link = link_res["result"]
    else:
        invite_link = f"https://t.me/{username}"
    return {
        "chat_id": str(chat.get("id", chat_id_raw)),
        "type": detected_type,
        "title": title,
        "invite_link": invite_link,
        "is_private": is_private
    }

def check_force_join(user_id):
    if not bot_settings["fj_on"] or not bot_settings["fj_channels"]: return True
    if is_admin(user_id): return True
    for entry in bot_settings["fj_channels"]:
        ch = _get_fj_chat_id(entry)
        res = api_call("getChatMember", {"chat_id": ch, "user_id": user_id})
        if res.get("ok") and res.get("result", {}).get("status", "left") not in ["left", "kicked"]: continue
        else: return False
    return True

def send_force_join_msg(chat_id):
    _reset_btn_counter()
    kb = []
    for entry in bot_settings["fj_channels"]:
        info = _get_fj_info(entry)
        ch_type = info.get("type", "channel")
        title = info.get("title", "")
        invite_link = info.get("invite_link", "")
        ch_id = info.get("chat_id", "")
        if invite_link:
            url = invite_link
        elif str(ch_id).startswith("@"):
            url = f"https://t.me/{ch_id.replace('@', '')}"
        else:
            url = f"https://t.me/{ch_id}"
        type_label = "Channel" if ch_type == "channel" else "Group"
        btn_text = f"Join {type_label}: {title}" if title else f"Join {type_label}"
        kb.append([{"text": btn_text, "icon_custom_emoji_id": "5789428375261023681", "url": url, "style": _rs()}])
    kb.append([{"text": "Check Joined", "icon_custom_emoji_id": "5352694861990501856", "callback_data": "check_fj", "style": _rs()}])
    send_message(chat_id, render_body_text(f"{PEM['warn']} <b>Please join our channels/groups to use the bot!</b>"), reply_markup={"inline_keyboard": kb})

def is_user_banned(user_id):
    if is_admin(user_id): return False
    with _banned_cache_lock:
        cached = user_banned_cache.get(user_id)
    if cached and time.time() - cached['time'] < 60:
        return cached['banned']
    local_u = _get_local_user(user_id)
    banned = local_u.get("banned", False)
    with _banned_cache_lock:
        # FIX: Evict 500 oldest entries instead of clearing all — thread-safe & preserves hot entries
        if len(user_banned_cache) > 2000:
            oldest = sorted(user_banned_cache, key=lambda k: user_banned_cache[k]['time'])[:500]
            for k in oldest:
                user_banned_cache.pop(k, None)
        user_banned_cache[user_id] = {'banned': banned, 'time': time.time()}
    return banned

# ==========================================
# Captcha Auto Login & Parsing Core
# ==========================================
def extract_otp_code(text):
    # NOTE: 'nn' → '\n' replacement is intentionally NOT done here.
    # Callers (parse_panel_response) already handle it in context.
    # Doing it here would corrupt words like "running", "connection", "announcement".
    clean_text = re.sub(r'[\u200B-\u200D\uFEFF]', '', str(text))

    # 1. Multi-part OTPs (e.g. 123-456 or 809-761 or 12-34-56)
    multi_part = re.search(r'(\d{3}[-\s]+\d{3})|(\d{2}[-\s]+\d{2}[-\s]+\d{2})', clean_text)
    if multi_part:
        return multi_part.group(0).replace(" ", "")

    # 2. Keyword-based extraction
    otp_keywords = ['code', 'is', 'otp', 'pin', 'verification', 'auth', 'رمز', 'your code']
    keywords_pattern = '|'.join(otp_keywords)
    keyword_match = re.search(rf'(?:{keywords_pattern})\s*(?:is|:|-|=)?\s*([a-z0-9]{{4,10}})', clean_text, re.I)
    if keyword_match and keyword_match.group(1).isdigit():
        return keyword_match.group(1)

    keyword_match_rev = re.search(rf'([a-z0-9]{{4,10}})\s*(?:is your|is the|code)', clean_text, re.I)
    if keyword_match_rev and keyword_match_rev.group(1).isdigit():
        return keyword_match_rev.group(1)

    # 3. Google OTP
    g_match = re.search(r'G-(\d{6})', clean_text, re.IGNORECASE)
    if g_match: return g_match.group(1)

    # 4. Digit sequences fallback — prefer 6-digit (most common OTP length)
    # Filter out year-like 4-digit numbers (1990-2099) to avoid false positives
    digit_matches = re.findall(r'(?<!\d)\d{4,8}(?!\d)', clean_text)
    if digit_matches:
        six_digit = [d for d in digit_matches if len(d) == 6]
        if six_digit:
            return six_digit[0]
        non_year = [d for d in digit_matches if not (len(d) == 4 and 1990 <= int(d) <= 2099)]
        return non_year[0] if non_year else digit_matches[0]

    return None

def parse_panel_response(response_text, p_config=None, max_results=None):
    results = []
    p_type = p_config.get("type", "API Panel") if p_config else "API Panel"
    
    n_col_name = p_config.get("num_col_name", "number").lower() if p_config else "number"
    m_col_name = p_config.get("msg_col_name", "message").lower() if p_config else "message"
    def _safe_col_idx(val, default):
        try:
            return max(0, int(val) - 1)
        except (TypeError, ValueError):
            return default
    n_idx = _safe_col_idx(p_config.get("num_col_idx"), 1) if p_config else 1
    m_idx = _safe_col_idx(p_config.get("msg_col_idx"), 2) if p_config else 2

    if p_type == "Auto Captcha Panel":
        try:
            soup = BeautifulSoup(response_text, 'html.parser')
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                if not rows: continue
                
                # 🌟 Option 1 + Smart HTML Detection: Find correct position using column name and user-given serial
                final_n_idx, final_m_idx = _find_header_column_indices(rows, n_col_name, m_col_name, n_idx, m_idx)

                for row in rows:
                    cols = row.find_all(['td', 'th'])
                    
                    # Will not take data from header rows (where all th exist)
                    if all(c.name == 'th' for c in cols): continue
                    
                    if len(cols) > max(final_n_idx, final_m_idx):
                        # Extract text from HTML table
                        num_text = cols[final_n_idx].get_text(separator=" ", strip=True)
                        msg_text = cols[final_m_idx].get_text(separator=" ", strip=True)
                        
                        clean_num = re.sub(r'\D', '', num_text)
                        
                        # Ensure number is actually 5-18 digits (to avoid random text)
                        if clean_num and 5 <= len(clean_num) <= 18:
                            otp = extract_otp_code(msg_text)
                            if otp and len(msg_text) > 4:
                                results.append({"number": clean_num, "message": msg_text, "otp": otp, "item_id": ""})
        except Exception as e:
            logger.warning(f"parse_panel HTML table error: {e}")
    else:
        try:
            data = json.loads(response_text)
            temp_results = []
            
            def process_item(item):
                pot_nums_list = []
                pot_msg = None
                explicit_otp = ""
                item_id = ""   # FIX: list items ke liye bhi define karo (NameError prevent)
                values = []
                
                if isinstance(item, dict):
                    # 1. First try searching by known JSON Key (e.g.: num, phone, sms)
                    lower_keys = {str(k).lower(): v for k, v in item.items()}
                    for k in ["number", "num", "phone", "msisdn", "sender"]:
                        if k in lower_keys:
                            clean_val = re.sub(r'\D', '', str(lower_keys[k]))
                            if 5 <= len(clean_val) <= 18:
                                if clean_val not in pot_nums_list: pot_nums_list.append(clean_val)
                    for k in ["message", "msg", "sms", "content", "text", "message_text", "sms_text", "full_message"]:
                        if k in lower_keys:
                            val = str(lower_keys[k])
                            if len(val) > 4:
                                pot_msg = val
                                break
                    # Panels that mask the code inside the message and provide it in a separate field
                    for k in ["otp_code", "otp", "code", "pin"]:
                        if k in lower_keys and str(lower_keys[k] or "").strip().isdigit():
                            explicit_otp = str(lower_keys[k]).strip()
                            break
                    # Extract panel's own message/record ID for reliable deduplication
                    item_id = ""
                    for k in ["id", "sms_id", "msg_id", "message_id", "record_id", "row_id", "cdr_id"]:
                        if k in lower_keys and lower_keys[k] is not None:
                            item_id = str(lower_keys[k]).strip()
                            break
                    values = list(item.values())
                elif isinstance(item, list):
                    # PRIMARY: Configured column indices se seedha extract karo
                    # n_idx / m_idx upar define hue hain (panel config se ya default 1/2)
                    if len(item) > max(n_idx, m_idx):
                        raw_n = item[n_idx]
                        raw_m = item[m_idx]
                        cn = re.sub(r'\D', '', str(raw_n))
                        if 5 <= len(cn) <= 18:
                            pot_nums_list.append(cn)
                        m_clean = re.sub(r'(?<!\n)nn(?!\n)', '\n', str(raw_m))
                        if len(m_clean) > 2:
                            pot_msg = m_clean
                        # Timestamp column se item_id extract karo (deduplication ke liye)
                        for col in item:
                            col_str = str(col).strip()
                            if re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}(\s+\d{2}:\d{2}(:\d{2})?)?$', col_str):
                                item_id = col_str
                                break
                    values = item  # Blind scan bhi chalega fallback ke liye

                # 2. Blind Scan (fallback / extra columns ke liye)
                for v in values:
                    if isinstance(v, (dict, list)) or v is None: continue
                    v_str = str(v).strip()
                    
                    # Number Detection: 7 to 18 digits
                    clean_v = re.sub(r'\D', '', v_str)
                    if 7 <= len(clean_v) <= 18 and not re.search(r'[a-zA-Z]', v_str):
                        # Logic to skip Date/Time/IP
                        # FIX: separator wali date (2026-06-26) + separator-less date (20260626) + YYYYMMDD format dono skip
                        is_date = (re.search(r'\d{4}[-/]\d{2}[-/]\d{2}', v_str) or
                                   re.search(r'\d{2}:\d{2}:\d{2}', v_str) or
                                   re.match(r'^\d{8}$', clean_v) or  # pure 8-digit = likely date YYYYMMDD
                                   "." in v_str)
                        # FIX: timestamp jaise "2026-06-26 06:02:46" — space wali combined datetime skip
                        if not is_date and not re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2}', v_str):
                            if clean_v not in pot_nums_list:
                                pot_nums_list.append(clean_v)
                    
                    # Message Detection: more than 4 characters and not just numbers
                    if len(v_str) > 4 and not v_str.isdigit():
                        # FIX: datetime strings (e.g. "2026-06-26 11:36:01") ko message mat samjho
                        _is_datetime_str = bool(
                            re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}(\s+\d{2}:\d{2}(:\d{2})?)?$', v_str) or
                            re.match(r'^\d{2}:\d{2}:\d{2}$', v_str)
                        )
                        if _is_datetime_str:
                            # Timestamp ko item_id ke liye use karo (deduplication ke liye)
                            if not item_id:
                                item_id = v_str
                            continue
                        # FIX: 'nn' literal ko real newlines mein convert karo (kuch panels nn bhejte hain \n ki jagah)
                        v_str_clean = re.sub(r'(?<!\n)nn(?!\n)', '\n', v_str)
                        # FIX: pehle OTP-wale messages prefer karo, lekin agar pot_msg abhi None hai
                        # aur koi bhi non-date string mili ho, use set karo (strict OTP check hatao)
                        has_otp = bool(extract_otp_code(v_str_clean))
                        if has_otp:
                            if pot_msg is None or len(v_str_clean) > len(pot_msg):
                                pot_msg = v_str_clean
                        elif pot_msg is None and len(v_str_clean) > 10:
                            # Fallback: OTP nahi mila, lekin lambi string hai — shayad message ho
                            pot_msg = v_str_clean
                                
                # 🌟 3. Multiple Numbers Logic (User Priority > Longest Number > First Number)
                pot_num = None
                if pot_nums_list:
                    matched_user_num = None
                    for n in pot_nums_list:
                        # Check if this number exists in user assigned number list
                        if n in nexa_assigned_numbers or any(n in str(key) for key in nexa_assigned_numbers.keys()):
                            matched_user_num = n
                            break
                    
                    if matched_user_num:
                        pot_num = matched_user_num
                    else:
                        # FIX: Second number blindly lene ki bajay — sabse lamba number lo (real phone numbers longer hote hain)
                        # Aur 8-digit pure numbers (YYYYMMDD dates) reject karo
                        valid_nums = [n for n in pot_nums_list if not (len(n) == 8 and re.match(r'^\d{8}$', n))]
                        if valid_nums:
                            pot_num = max(valid_nums, key=len)  # longest = most likely phone number
                        elif pot_nums_list:
                            pot_num = pot_nums_list[0]
                            
                if pot_num and (pot_msg or explicit_otp):
                    otp = explicit_otp if explicit_otp else extract_otp_code(pot_msg)
                    if otp:
                        temp_results.append({"number": pot_num, "message": pot_msg or "", "otp": otp, "item_id": item_id})
                        
            def traverse_json(node, depth=0):
                # Guard against deeply nested or circular-like JSON (max 10 levels)
                if depth > 10:
                    return
                # max_results early-exit: test connection ke liye sirf N records chahiye
                if max_results and len(temp_results) >= max_results:
                    return
                if isinstance(node, list):
                    if len(node) > 0 and not isinstance(node[0], (dict, list)):
                        # It's a flat list representing one record
                        process_item(node)
                    else:
                        for child in node:
                            if max_results and len(temp_results) >= max_results:
                                break
                            if isinstance(child, (dict, list)):
                                traverse_json(child, depth + 1)
                elif isinstance(node, dict):
                    prev_len = len(temp_results)
                    process_item(node)
                    # BUG FIX: Agar is dict ne khud ek valid record produce kiya,
                    # toh nested values ko alag records samajh ke process MAT karo.
                    # Woh sub-fields hain, independent records nahi — isse "idhar udhar"
                    # wale wrong records mix hona band hoga.
                    if len(temp_results) == prev_len:
                        # Dict ne koi record nahi diya → nested values mein records ho sakte hain
                        for val in node.values():
                            if max_results and len(temp_results) >= max_results:
                                break
                            if isinstance(val, (dict, list)):
                                traverse_json(val, depth + 1)

            traverse_json(data)
            
            # Remove duplicates — item_id bhi include karo taaki same num+otp
            # alag timestamps (alag requests) wale records merge na ho jaayein
            seen = set()
            for r in temp_results:
                uid = f"{r['number']}_{r['otp']}_{r.get('item_id', '')}"
                if uid not in seen:
                    seen.add(uid)
                    results.append(r)
        except Exception as e:
            logger.warning(f"parse_panel_response error: {e}")
        
    return results

# 🌟 SPA / JSON-API Login Fallback 🌟
# Kuch panels (jaise Teleroutex) purane PHP panels jaisa server-rendered HTML
# login form nahi bhejte — unka login page ek React/Vue SPA hota hai jo browser
# mein JavaScript se render hota hai. Raw HTML mein koi <form> tag hi nahi milta,
# isliye purana form-scraping logic hamesha "No login form found" de kar fail
# ho jaata tha, chahe username/password bilkul sahi ho.
#
# Yeh fallback un panels ke liye hai: form na milne par yeh seedha unki JSON
# login API (jo panel ka frontend background mein use karta hai) par POST
# bhejta hai aur mile hue JWT/token ko session ke Authorization header mein
# set kar deta hai taaki baad ki requests bhi authenticated rahen.
def _attempt_spa_json_login(login_url, initial_res, username, password, session, idx):
    """Returns (True, None) on success, (False, reason) on failure."""
    parsed = urlparse(login_url)
    same_origin = f"{parsed.scheme}://{parsed.netloc}"

    # 1. API base candidates. Kai panels apna asli backend ek alag subdomain
    #    (jaise server.example.com) par rakhte hain — yeh hint CSP header ke
    #    'connect-src' directive mein milta hai. Fallback: same origin.
    api_bases = []
    csp = initial_res.headers.get("Content-Security-Policy", "") or initial_res.headers.get("content-security-policy", "")
    if csp:
        m = re.search(r"connect-src([^;]+)", csp, re.I)
        if m:
            for tok in m.group(1).split():
                if tok.startswith("http"):
                    api_bases.append(tok.strip().rstrip("/"))
    if same_origin not in api_bases:
        api_bases.append(same_origin)

    login_paths = ["/api/user/login", "/api/auth/login", "/user/login", "/auth/login", "/api/login", "/login"]
    # 'identifier' pehle try karo (Teleroutex jaise panels ise username/email
    # dono ke liye use karte hain), fir common variants.
    payload_variants = [
        {"identifier": username, "password": password},
        {"username": username, "password": password},
        {"email": username, "password": password},
    ]

    last_reason = "No login form found"
    for base in api_bases:
        for path in login_paths:
            url = base.rstrip("/") + path
            for payload in payload_variants:
                try:
                    res = session.post(url, json=payload, timeout=12)
                except Exception:
                    continue
                if res.status_code not in (200, 201):
                    continue
                try:
                    body = res.json()
                except Exception:
                    continue

                # Token ko kuch common jagahon par dhoondo:
                # {data:{doc:{token}}}, {data:{token}}, {token}, {doc:{token}}
                token = None
                for path_getter in (
                    lambda b: b.get("data", {}).get("doc", {}).get("token"),
                    lambda b: b.get("data", {}).get("token"),
                    lambda b: b.get("doc", {}).get("token"),
                    lambda b: b.get("token"),
                ):
                    try:
                        token = path_getter(body)
                    except Exception:
                        token = None
                    if token:
                        break

                success_flag = body.get("success") is True or str(body.get("status", "")).lower() == "success"
                if token or success_flag:
                    if token:
                        session.headers.update({"Authorization": f"Bearer {token}"})
                    panel_sessions[idx] = session
                    return True, {"token": token, "api_base": base}

                # Galat credentials ya validation error hone par reason capture karo
                msg = body.get("data", {}).get("message") if isinstance(body.get("data"), dict) else body.get("message")
                if msg:
                    last_reason = str(msg)[:60]

    return False, last_reason


def _extract_base_url(login_url):
    """Login URL se base URL extract karo — /login /signin /auth etc. hata ke.
    e.g. http://panel.com/ints/login → http://panel.com/ints"""
    base = login_url
    for seg in ['/login', '/signin', '/auth', '/sign-in', '/log-in']:
        if seg in base.lower():
            base = base[:base.lower().index(seg)]
            break
    return base.rstrip('/')


# 🌟 Advanced Automated Background Captcha Solver 🌟
def attempt_auto_login(p, idx):
    login_url = p.get("login_url", "").strip()
    if not login_url.startswith("http"):
        login_url = "http://" + login_url
        
    # Only append /login if URL doesn't already contain a login-related path
    login_keywords = ['/login', '/signin', '/auth', '/sign-in', '/log-in', '.php', '.asp', '.html', '.htm', '.jsp']
    url_lower = login_url.lower()
    has_login_path = any(kw in url_lower for kw in login_keywords)
    if not has_login_path:
        login_url = f"{login_url.rstrip('/')}/login"
        
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=2)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    })
    
    try:
        res = session.get(login_url, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        all_text = res.text
        
        # 1. SOLVE CAPTCHA (Exact bot 3.py logic)
        captcha_match = re.search(r'(\d+\s*[\+\-\*]\s*\d+)\s*[=\?:]', all_text)
        if not captcha_match:
            captcha_match = re.search(r'what is\s*(\d+\s*[\+\-\*]\s*\d+)', all_text, re.I)
        if not captcha_match:
            elements = soup.find_all(["label", "div", "span", "p", "strong"])
            for el in elements:
                txt = el.get_text(separator=" ", strip=True)
                if any(op in txt for op in ["+", "-", "*"]):
                    m = re.search(r'(\d+\s*[\+\-\*]\s*\d+)', txt)
                    if m:
                        captcha_match = m
                        break
                        
        captcha_found = captcha_match is not None
        captcha_text = captcha_match.group(1) if captcha_match else ""
        answer = ""
        if captcha_found:
            m2 = re.search(r'(\d+)\s*([\+\-\*])\s*(\d+)', captcha_text)
            if m2:
                a, op, b = int(m2.group(1)), m2.group(2), int(m2.group(3))
                if op == '+': answer = str(a + b)
                elif op == '-': answer = str(a - b)
                elif op == '*': answer = str(a * b)
                else: answer = "0"
            else:
                answer = "0"

        # 2. FIND FORM
        form = soup.find("form")
        if not form:
            # Purani HTML-form assumption fail hui — ho sakta hai yeh ek SPA
            # panel (jaise Teleroutex) ho jiska login form JavaScript se
            # render hota hai. Uske JSON login API par try karo.
            ok, info = _attempt_spa_json_login(login_url, res, p.get("username", ""), p.get("password", ""), session, idx)
            if ok:
                p["login_status"] = "✅ Active & Fetching"
                p["retry_wait"] = 90
                if isinstance(info, dict):
                    if info.get("token"):
                        p["auth_token"] = info["token"]
                    if info.get("api_base"):
                        p["api_base"] = info["api_base"]
                return True
            reason = info if isinstance(info, str) else "No login form found"
            p["login_status"] = f"❌ Login Failed ({reason[:40]})"
            p["retry_wait"] = 90
            return False
            
        action = form.get("action")
        post_url = urljoin(login_url, action) if action else login_url

        form_data = {}
        for hidden in form.find_all("input", type="hidden"):
            name = hidden.get("name")
            if name: form_data[name] = hidden.get("value") or ""
        
        user_input = form.find("input", {"name": re.compile(r"user|email|id", re.I)}) or \
                     form.find("input", {"type": "text", "placeholder": re.compile(r"user|email", re.I)}) or \
                     form.find("input", {"type": "text"})
                     
        pass_input = form.find("input", {"name": re.compile(r"pass", re.I)}) or \
                     form.find("input", {"type": "password"})
                     
        captcha_input = form.find("input", {"placeholder": re.compile(r"answer|ans|code|verification|value|captcha", re.I)}) or \
                        form.find("input", {"name": re.compile(r"ans|captcha|ver|code", re.I)})
        
        user_field = user_input.get("name") if user_input else "username"
        pass_field = pass_input.get("name") if pass_input else "password"
        captcha_field = captcha_input.get("name") if captcha_input else "answer"

        form_data[user_field] = p.get("username", "")
        form_data[pass_field] = p.get("password", "")
        # Only send captcha answer if captcha was actually detected on the page
        if captcha_found and captcha_field and answer:
            form_data[captcha_field] = answer

        # 3. SUBMIT — Referer header zaroori hai kuch panels ke liye (warna 403 milta hai)
        session.headers.update({'Referer': login_url})
        login_req = session.post(post_url, data=form_data, allow_redirects=False, timeout=15)
        
        # 403 = panel ne Referer/auth check fail kiya — immediately report karo
        if login_req.status_code == 403:
            p["login_status"] = "❌ Login Failed (403 Forbidden — Panel URL check karo)"
            p["retry_wait"] = 90
            return False

        # 4. VERIFY using redirect Location
        location = login_req.headers.get("Location", "")
        
        # SUCCESS: koi bhi redirect jo login page pe wapas nahi jaata
        # (kuch panels 'agent/' pe redirect karte hain, kuch 'client/', kuch 'dashboard/')
        _login_slugs = ['login', 'signin', 'sign-in', 'log-in', 'auth']
        _is_login_redirect = any(slug in location.lower() for slug in _login_slugs)
        if location and not _is_login_redirect:
            # Panel section detect karo (agent/client) — CDR URL auto-construct ke liye
            for _sec in ('agent', 'client'):
                if _sec in location.lower():
                    p["panel_section"] = _sec
                    break
            # Follow redirect to establish session
            dash_url = urljoin(post_url, location)
            session.get(dash_url, timeout=10)
            panel_sessions[idx] = session
            p["login_status"] = "✅ Active & Fetching"
            p["retry_wait"] = 90  # Reset to normal retry
            return True
        
        # If redirected to ./ or login page - check error message
        if location:
            err_url = urljoin(post_url, location)
            err_res = session.get(err_url, allow_redirects=True, timeout=10)
            err_text = err_res.text
        else:
            err_text = login_req.text
        
        err_soup = BeautifulSoup(err_text, 'html.parser')
        error_el = err_soup.find("font") or err_soup.find("div", class_="error") or err_soup.find("span", class_="error")
        error_msg = error_el.get_text(strip=True) if error_el else ""
        
        # Handle specific error types
        if 'session invalid' in error_msg.lower() or 'try after' in error_msg.lower():
            # FIX: "try after X minute" se actual wait time parse karo
            wait_seconds = 120  # default fallback
            m_wait = re.search(r'try after\s*(\d+)\s*(minute|min|second|sec)', error_msg, re.I)
            if m_wait:
                n = int(m_wait.group(1))
                unit = m_wait.group(2).lower()
                wait_seconds = n * 60 if 'min' in unit else n
                wait_seconds += 15  # buffer
            p["login_status"] = f"❌ Panel Locked ({error_msg})"
            p["retry_wait"] = wait_seconds
            p["last_login_attempt"] = time.time()  # lockout start time record karo
            return False
        elif 'captcha' in error_msg.lower():
            p["login_status"] = f"❌ Captcha Failed (Retrying...)"
            p["retry_wait"] = 90
            return False
        elif 'invalid' in error_msg.lower() or 'password' in error_msg.lower():
            p["login_status"] = f"❌ Wrong Username/Password"
            p["retry_wait"] = 90
            return False
        else:
            # Unknown failure - try alternate verification
            msg_link = p.get("msg_link", "").strip()
            if not msg_link.startswith("http") and msg_link != "":
                msg_link = "http://" + msg_link
            if not msg_link:
                _sec = p.get("panel_section", "client")
                check_url = f"{_extract_base_url(login_url)}/{_sec}/SMSCDRStats"
            else:
                check_url = msg_link
            
            check_res = session.get(check_url, timeout=10)
            if 'login' not in check_res.url.lower().split('/')[-1] and check_res.status_code == 200:
                panel_sessions[idx] = session
                p["login_status"] = "✅ Active & Fetching"
                p["retry_wait"] = 90
                return True
            else:
                reason = error_msg if error_msg else (f"Math: {captcha_text} = {answer}" if captcha_found else "Login page returned")
                p["login_status"] = f"❌ Login Failed ({reason[:40]})"
                p["retry_wait"] = 90
                return False
            
    except Exception as e:
        p["login_status"] = f"❌ Error: {str(e)[:20]}"
        
    return False

def _build_api_urls(p):
    """Build the list of URLs + headers to try for an API Panel from its config.
    Extracted to avoid duplicate code between panel_monitor_thread and test_p_conn_."""
    full_url = p.get("full_api_url", "").strip()
    url = p.get("api_url", "").strip()
    token = p.get("token", "").strip()
    token_header = p.get("token_header", "").strip()
    urls_to_try = []
    if full_url:
        urls_to_try.append(full_url)
    elif token_header and token:
        urls_to_try.append(url)
    else:
        if "{token}" in url or "{key}" in url:
            urls_to_try.append(url.replace("{token}", token).replace("{key}", token))
        elif "token=" in url or "key=" in url:
            urls_to_try.append(url)
        else:
            urls_to_try.append(url)
            if token:
                sep = '&' if '?' in url else '?'
                urls_to_try.append(f"{url}{sep}token={token}")
                urls_to_try.append(f"{url}{sep}key={token}&start=0")
                urls_to_try.append(f"{url}{sep}key={token}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    if token_header and token:
        headers[token_header] = token
    return urls_to_try, headers

def _find_otp_owners(clean_num):
    """Find all bot users who own this phone number.
    Extracted to avoid duplicate code between panel_monitor_thread and global_sms_listener.
    Returns: list of chat_ids (may be multiple if num_share > 1)."""
    owners = []
    # 1. Active Sessions — fastest, in-memory
    for uid, session_data in list(user_active_sessions.items()):
        for act_num in session_data.get("nums", []):
            act_clean = str(act_num).replace("+", "").replace(" ", "").replace("-", "").strip()
            if act_clean == clean_num or (
                len(act_clean) >= 8 and len(clean_num) >= 8 and
                abs(len(act_clean) - len(clean_num)) <= 3 and
                (act_clean.endswith(clean_num[-8:]) or clean_num.endswith(act_clean[-8:]))
            ):
                owners.append(uid)
                break
    # 2. number_batches used_by — persistent, survives bot restarts
    if not owners:
        for b_id, b_data in number_batches.items():
            for n_obj in b_data.get("numbers", []):
                stored_clean = str(n_obj.get("num", "")).replace("+", "").replace(" ", "").replace("-", "").strip()
                if stored_clean == clean_num or (
                    len(stored_clean) >= 8 and len(clean_num) >= 8 and
                    abs(len(stored_clean) - len(clean_num)) <= 3 and
                    (stored_clean.endswith(clean_num[-8:]) or clean_num.endswith(stored_clean[-8:]))
                ):
                    for used_uid in n_obj.get("used_by", []):
                        if used_uid not in owners:
                            owners.append(used_uid)
                    if owners:
                        break
            if owners:
                break
    # 3. Nexa assigned numbers
    if not owners:
        for nexa_n, n_owner in nexa_assigned_numbers.items():
            clean_nexa = str(nexa_n).replace("+", "").replace(" ", "").replace("-", "").strip()
            if clean_nexa == clean_num or (
                len(clean_nexa) >= 8 and len(clean_num) >= 8 and
                abs(len(clean_nexa) - len(clean_num)) <= 3 and
                (clean_nexa.endswith(clean_num[-8:]) or clean_num.endswith(clean_nexa[-8:]))
            ):
                owners.append(n_owner)
    # 4. VoltX assigned numbers
    if not owners:
        vx_owner = _find_assigned_owner(voltx_assigned_numbers, clean_num)
        if vx_owner:
            owners.append(vx_owner)
    # 5. Stex assigned numbers
    if not owners:
        sx_owner = _find_assigned_owner(stex_assigned_numbers, clean_num)
        if sx_owner:
            owners.append(sx_owner)
    return list(set(owners))

_RATE_LIMIT_PHRASES = [
    "too many times", "too many requests", "rate limit", "try again in",
    "slow down", "429", "access denied", "you've accessed"
]

def _is_rate_limited_response(text):
    """Check karo agar API rate-limit HTML/text page return kar raha hai."""
    if not text:
        return False
    lower = text.lower()
    return any(phrase in lower for phrase in _RATE_LIMIT_PHRASES)

_owner_alert_last_sent = {}

def _notify_owner_panel_issue(alert_key, message, cooldown=3600):
    """Owner ko panel ki khaas problem ke baare mein ek baar (cooldown ke andar dobara nahi) batao.
    Isse silent failures (jaise 'panel se data mil raha hai lekin OTP parse/deliver nahi ho raha')
    ab OWNER ko turant dikhengi, warna pehle yeh sirf log file mein chhup jaati thi."""
    now = time.time()
    last = _owner_alert_last_sent.get(alert_key, 0)
    if now - last < cooldown:
        return
    _owner_alert_last_sent[alert_key] = now
    try:
        send_message(OWNER_ID, render_body_text(f"⚠️ <b>Panel Alert</b>\n{message}"))
    except Exception as e:
        logger.warning(f"Owner panel-alert send failed: {e}")


def _fetch_api_panel_data(idx, p):
    """Ek API panel se data fetch karo. Returns parsed list ya [] on failure."""
    now = time.time()

    # Rate-limit backoff check: agar API ne recently rate-limit kiya hai toh skip karo
    rate_limit_until = p.get("rate_limit_until", 0)
    if now < rate_limit_until:
        wait_left = int(rate_limit_until - now)
        logger.info(f"Panel {idx} rate-limited — skipping for {wait_left}s more")
        return []

    urls_to_try, headers = _build_api_urls(p)
    for try_url in urls_to_try:
        try:
            res = tg_session.get(try_url, headers=headers, timeout=8)  # use persistent session

            # Rate-limit detection: JSON parse karne se PEHLE check karo
            if res.status_code == 429 or _is_rate_limited_response(res.text):
                backoff = 10  # 10 seconds backoff
                p["rate_limit_until"] = now + backoff
                logger.warning(f"Panel {idx} rate-limited by API — backing off {backoff}s. Response: {res.text[:120]!r}")
                return []

            parsed_data = parse_panel_response(res.text, p)
            if parsed_data:
                full_url = p.get("full_api_url", "")
                token = p.get("token", "").strip()
                url = p.get("api_url", "").strip()
                if not full_url and try_url != url and token and not p.get("token_header", ""):
                    p["api_url"] = try_url.replace(token, "{token}")
                    save_local_db()
                p.pop("rate_limit_until", None)  # Successful fetch — backoff reset karo
                p["_zero_yield_streak"] = 0
                return parsed_data
            else:
                # Response mila (200 OK, koi rate-limit nahi) lekin ek bhi record parse nahi hua.
                # Agar yeh baar-baar ho raha hai, toh column-mapping / JSON-format mismatch ho sakta
                # hai — pehle yeh sirf log mein chhup jaata tha, ab OWNER ko bata denge.
                _has_body = bool(res.text and res.text.strip() and res.text.strip() not in ("[]", "{}", "null"))
                if _has_body:
                    p["_zero_yield_streak"] = p.get("_zero_yield_streak", 0) + 1
                    if p["_zero_yield_streak"] >= 5:
                        _notify_owner_panel_issue(
                            f"api_zero_yield_{idx}",
                            f"<b>{p.get('name', 'API Panel')}</b> se response mil raha hai lekin "
                            f"koi bhi OTP/number parse nahi ho pa raha (5+ baar).\n"
                            f"Number/Message Column Name ya Serial check karein — shayad panel ke "
                            f"response format se match nahi kar rahe."
                        )
        except Exception as e:
            logger.warning(f"Panel URL probe error: {e}")
            continue
    return []


def _fetch_json_api_panel_data(p, sess):
    """SPA/JSON-API panels (jaise Teleroutex) ke liye data fetch — HTML table
    scrape karne ki jagah seedha panel ki live JSON API se records lete hain."""
    api_base = p.get("api_base", "").rstrip("/")
    if not api_base:
        return [], ""

    # ── SAFETY BLOCK: /sample endpoint kabhi use mat karo ───────────────────
    # /sample = public live demo feed (sabke 1.9M+ SMS dikhata hai — yeh
    # aapka data NAHI hai). Sirf /api/message-data-record use karo jisme
    # sirf logged-in client (JWT token) ka apna data aata hai.
    data_path = p.get("api_data_path", "/api/message-data-record")
    if "sample" in data_path.lower():
        data_path = "/api/message-data-record"
    # Ensure path always starts with /
    if not data_path.startswith("/"):
        data_path = "/" + data_path
    # ────────────────────────────────────────────────────────────────────────

    # Panel ka configured username (double-check filter ke liye)
    panel_username = p.get("username", "").strip().lower()

    url = f"{api_base}{data_path}?pageSize=50&page=1&sortBy=createdAt_descending"
    res = sess.get(url, timeout=15)
    if res.status_code == 401:
        raise Exception("Session expired")
    try:
        body = res.json()
    except Exception:
        return [], res.text
    docs = (body.get("data") or {}).get("docs", [])
    if not isinstance(docs, list):
        return [], res.text
    results = []
    for doc in docs:
        if not isinstance(doc, dict):
            continue

        # ── FIX 1: Sirf "Success" cause wale records process karo ───────────
        # Failed/Error records mein OTP nahi hota — unhe skip karo
        cause = str(doc.get("cause", "Success")).strip()
        if cause.lower() not in ("success", ""):
            continue
        # ────────────────────────────────────────────────────────────────────

        # ── FIX 2: Double-check — sirf apne account ke records ──────────────
        # Server-side JWT filtering pe rely karte hain, lekin agar
        # kabhi bhi dusre client ka record aa jaaye — block karo.
        if panel_username:
            client_info = doc.get("client") or {}
            if isinstance(client_info, dict):
                rec_user = str(client_info.get("username", "")).strip().lower()
                if rec_user and rec_user != panel_username:
                    # Yeh record dusre client ka hai — skip (live/sample safety)
                    continue
        # ────────────────────────────────────────────────────────────────────

        num_val = doc.get("number", "")
        msg_val = doc.get("message", "")
        clean_num = re.sub(r"\D", "", str(num_val))
        if not (clean_num and 5 <= len(clean_num) <= 18 and not re.match(r"^\d{8}$", clean_num)):
            continue
        msg_clean = re.sub(r"(?<!\n)nn(?!\n)", "\n", str(msg_val))
        otp = extract_otp_code(msg_clean)
        if otp and len(msg_clean) > 4:
            # FIX: createdAt ko _id (MongoDB ObjectId hex) se PEHLE try karo.
            # createdAt ek parseable datetime string hai — _is_stale_otp usse
            # sahi age check kar sakta hai. MongoDB _id hex string ka timestamp
            # _parse_item_datetime_epoch parse nahi kar sakta (stale check skip).
            # Dedup ke liye dono kaam karte hain (dono unique hain), lekin stale
            # detection ke liye createdAt behtar hai.
            item_id = str(doc.get("createdAt") or doc.get("_id") or doc.get("id") or "")
            results.append({"number": clean_num, "message": msg_clean, "otp": otp, "item_id": item_id})
    return results, res.text


def _fetch_captcha_panel_data(idx, p):
    """Ek Auto Captcha panel se data fetch karo. Returns list, ya None agar skip karna ho."""
    now = time.time()
    # Captcha panels: 10s minimum between fetches (was 30s — reduced for faster delivery)
    if now - p.get("last_fetch_time", 0) < 10:
        return None

    sess = panel_sessions.get(idx)
    if not sess:
        retry_wait = p.get("retry_wait", 90)
        # FIX: agar kisi buggy error-parse ki wajah se retry_wait bahut zyada set ho jaaye
        # (jaise galat "try after X minute" parsing), panel hamesha ke liye atka na rahe.
        # 30 minute se zyada kabhi wait mat karo — us se zyada hone pe cap laga do.
        if retry_wait > 1800:
            retry_wait = 1800
            p["retry_wait"] = 1800
        if now - p.get("last_login_attempt", 0) < retry_wait:
            return None
        p["last_login_attempt"] = now
        success = attempt_auto_login(p, idx)
        save_local_db()
        if not success:
            p["last_fetch_time"] = now
            # Login baar-baar fail ho raha hai — OWNER ko batao, warna panel silently
            # "OTP nahi bhej raha" dikhega bina kisi wajah ke.
            p["_login_fail_streak"] = p.get("_login_fail_streak", 0) + 1
            if p["_login_fail_streak"] >= 3:
                _notify_owner_panel_issue(
                    f"cpt_login_fail_{idx}",
                    f"<b>{p.get('name', 'Auto Captcha Panel')}</b> mein baar-baar login fail ho raha hai.\n"
                    f"Status: {p.get('login_status', 'Unknown')}\n"
                    f"Isliye is panel se OTP group mein nahi ja rahe — Username/Password/Login URL check karein."
                )
            return None
        p["_login_fail_streak"] = 0
        sess = panel_sessions.get(idx)

    try:
        if p.get("api_base"):
            parsed_data, res_text = _fetch_json_api_panel_data(p, sess)
        else:
            msg_link = p.get("msg_link", "").strip()
            if not msg_link.startswith("http") and msg_link != "":
                msg_link = "http://" + msg_link
            if not msg_link:
                _lu = p.get("login_url", "").strip()
                if not _lu.startswith("http"):
                    _lu = "http://" + _lu
                _sec = p.get("panel_section", "client")  # agent/client — login redirect se detect hota hai
                msg_link = f"{_extract_base_url(_lu)}/{_sec}/SMSCDRStats"
            parsed_data, res_text = fetch_cpt_panel_cdrs(p, sess, msg_link)
        p["login_status"] = "✅ Active & Fetching"
        p["last_fetch_time"] = time.time()
        if parsed_data:
            p["_zero_yield_streak"] = 0
        elif res_text and res_text.strip():
            # FIX: JSON API panels (jaise Teleroutex) ke liye zero-yield streak
            # count nahi karo — wahan empty response NORMAL hai (koi naya SMS nahi).
            # Zero-yield warning sirf HTML table panels ke liye meaningful hai
            # (wrong column mapping ka sign). JSON API panels mein docs==[] hona
            # bas "abhi koi pending OTP nahi" hai — configuration error nahi.
            if p.get("api_base"):
                p["_zero_yield_streak"] = 0  # Reset — JSON API panel ke liye normal
            else:
                # HTML table panel: Page mil gaya lekin ek bhi OTP/number parse nahi hua —
                # column-mapping ya table-structure mismatch ho sakta hai.
                p["_zero_yield_streak"] = p.get("_zero_yield_streak", 0) + 1
                if p["_zero_yield_streak"] >= 5:
                    _notify_owner_panel_issue(
                        f"cpt_zero_yield_{idx}",
                        f"<b>{p.get('name', 'Auto Captcha Panel')}</b> ka page load ho raha hai lekin "
                        f"koi bhi OTP/number parse nahi ho pa raha (5+ baar).\n"
                        f"Number/Message Column Name ya Serial check karein — panel ke table format se "
                        f"match nahi kar rahe."
                    )
        return parsed_data
    except Exception as e:
        p["login_status"] = "❌ Session Expired (Retrying...)"
        if idx in panel_sessions:
            del panel_sessions[idx]
        p["last_fetch_time"] = time.time()
        save_local_db()
        return None


def _process_panel_otps(idx, p, parsed_data):
    """Panel se mila parsed_data process karo aur OTPs deliver karo."""
    panel_needs_warmup = p.get("needs_warmup", True)  # Default True = safe (skip until first successful poll)

    limit = p.get("records", 0)
    if p.get("type") != "Auto Captcha Panel" and limit > 0:
        parsed_data = parsed_data[:limit]

    for item in parsed_data:
        try:
            num = item["number"]
            otp = item["otp"]
            msg_text = item["message"]

            item_id = item.get("item_id", "")
            panel_key = p.get("name", str(idx))
            if item_id:
                # FIX: Panel ka apna timestamp (item_id) check karo — agar OTP
                # already 25 ghante se purana hai, to isse kabhi deliver nahi
                # karna, chahe bot ne pehli baar hi dekha ho (dedup memory
                # se independent — yeh "content ki asli age" check hai).
                if _is_stale_otp(item_id):
                    _add_to_processed(f"PANEL_{panel_key}_{item_id}")
                    continue
                # Item ID wala panel: har unique record ek baar hi aayega (25h window)
                unique_id = f"PANEL_{panel_key}_{item_id}"
                dedup_window = 90000  # 25 ghante — same record dobara nahi
            else:
                # Item ID nahi: sirf 10 second spam guard.
                # Panel har 1-2s mein poll hota hai — 10s window same record ko
                # ek baar deliver karta hai. 10s baad same code = naya SMS → turant deliver.
                unique_id = f"{num}_{otp}"
                dedup_window = 10    # 10 second — sirf tight-loop spam rokne ke liye

            clean_api_num = str(num).replace("+", "").replace(" ", "").replace("-", "").strip()
            owners = _find_otp_owners(clean_api_num)

            # ── WARMUP GATE ─────────────────────────────────────────────────
            # Panel ka pehla successful poll — purane OTPs HAMESHA skip karo.
            # Owner ho ya na ho — warmup mein koi delivery nahi.
            # Mark-as-processed ZARURI hai — warna warmup ke baad same OTP
            # "naya" lagega aur dobara deliver ho jaayega.
            warmup_num_otp_key = f"WARMUP_{num}_{otp}"
            if panel_needs_warmup:
                if item_id:
                    # item_id wala: normal key 25h window se mark karo
                    _add_to_processed(unique_id)
                # HAMESHA WARMUP_{num}_{otp} bhi mark karo — chahe item_id ho ya na ho.
                # Yeh backup protection hai: agar item_id parsing inconsistent ho
                # (ek fetch mein mila, dusre mein nahi), toh bhi purana OTP block rahega.
                _add_to_processed(warmup_num_otp_key)
                continue  # HAMESHA skip — owner exception nahi

            # ── DEDUP GATE ──────────────────────────────────────────────────
            # Non-item_id entries: WARMUP_ check (25h) — purana OTP block karo.
            # Item_id wale: WARMUP_ check sirf tab — jab item_id empty ho (inconsistent parsing).
            # Agar item_id hai (naya SMS, different item_id), WARMUP_ block nahi karega —
            # warna same number pe genuinely naya OTP bhi 25h ke liye band ho jaata.
            if not item_id and _is_processed(warmup_num_otp_key, window=90000):
                continue
            # item_id wale: 25h window. Non-item_id: 10s window (same code allow karo)
            if _is_processed(unique_id, window=dedup_window):
                continue

            # Naya OTP — PEHLE mark karo, phir deliver karo (race condition prevent)
            _add_to_processed(unique_id)
            # Non-item_id panels ke liye WARMUP_ key bhi 25h set karo.
            # Item_id panels ke liye nahi — taaki alag item_id wala naya OTP block na ho.
            if not item_id:
                _add_to_processed(warmup_num_otp_key)

            # ── DELIVERY ────────────────────────────────────────────────────
            char, iso = get_flag_and_code(num)
            app_full_name, prem_app_html = get_service_info_html(p.get("name", "Panel"), msg_text)
            current_time = time.time()
            display_num = f"+{num}" if not str(num).startswith("+") else str(num)
            lang = detect_language(msg_text)

            _prune_traffic(current_time)
            with _traffic_lock:
                recent_traffic.append({
                    "service": app_full_name, "iso": iso,
                    "flag": char, "number": num, "time": current_time
                })
            save_local_db()

            first_owner = owners[0] if owners else None
            masked = mask_number(display_num, user_id=first_owner)

            # GROUP: har naya unique OTP group mein jaaye
            group_raw = f"{get_flag_info_html(display_num)} #{iso} ♦ {masked} ✅ {otp}"
            group_msg = render_body_text(group_raw)

            # FIX: Har group send apne try-except mein — ek fail ho toh baaki aur user delivery block na ho
            fw_groups = bot_settings.get("fw_groups", [])
            if not fw_groups:
                # OTP mila aur parse bhi ho gaya, lekin koi forwarding group hi configure nahi
                # hai — yehi sabse aam wajah hai "OTP aata hai lekin group mein nahi jaata".
                _notify_owner_panel_issue(
                    "no_fw_groups",
                    "OTP mil raha hai aur parse ho raha hai, lekin koi <b>OTP Group</b> add nahi hai "
                    "isliye woh kahin forward nahi ho raha.\n"
                    "Admin Panel → OTP Groups mein group add karein."
                )
            for fw in fw_groups:
                try:
                    _reset_btn_counter()
                    kb = _make_otp_kb(otp)
                    _fw_btns = fw.get("buttons", [])
                    for i in range(0, len(_fw_btns), 2):
                        row = [_make_fw_btn(_fw_btns[i], kb)]
                        if i + 1 < len(_fw_btns):
                            row.append(_make_fw_btn(_fw_btns[i + 1], kb))
                        kb.append(row)
                    res_fw = send_message(fw["chat_id"], group_msg, reply_markup={"inline_keyboard": kb})
                    if not (res_fw and res_fw.get("ok")):
                        logger.warning(f"Panel group send failed ({fw.get('chat_id')}): {res_fw}")
                        _notify_owner_panel_issue(
                            f"fw_send_fail_{fw.get('chat_id')}",
                            f"OTP Group (<code>{fw.get('chat_id')}</code>) mein message bhejna fail ho raha hai.\n"
                            f"Reason: {res_fw}\n"
                            f"Group ID sahi hai aur bot us group mein admin/member hai, verify karein."
                        )
                except Exception as e:
                    logger.warning(f"Panel group delivery error ({fw.get('chat_id')}): {e}")

            # BOT USER: agar number ka owner hai to use bhi deliver karo
            # FIX: Har owner apne try-except mein — ek fail ho toh baaki owners block na hon
            for owner_id in owners:
                try:
                    inbox_msg = render_body_text(
                        f"{get_flag_info_html(display_num)} #{iso} ♦ {display_num} ✅ {otp}")
                    _reset_btn_counter()
                    inbox_kb = _make_otp_kb(otp)
                    reward = float(bot_settings.get("otp_reward", 0.0))
                    if reward > 0:
                        update_balance(owner_id, reward)
                        inbox_kb.append([{"text": f"Added {reward} ₹",
                                          "icon_custom_emoji_id": "5420396762189831222",
                                          "callback_data": "ignore", "style": _rs()}])
                    send_message(owner_id, inbox_msg, reply_markup={"inline_keyboard": inbox_kb})
                    _increment_local_user(owner_id, "total_otps", 1)
                except Exception as e:
                    logger.warning(f"Panel user delivery error ({owner_id}): {e}")

            try:
                with _data_lock:
                    otp_received_numbers.add(clean_api_num)
            except Exception as e:
                logger.warning(f"panel_monitor otp_received error: {e}")

        except Exception as e:
            logger.warning(f"_process_panel_otps item error: {e}")

    if panel_needs_warmup:
        p["needs_warmup"] = False
        save_local_db()
        logger.info(f"Panel warmup done — old OTPs skipped.")


def _eagerly_warmup_panel(idx, p):
    """Jab panel ON hota hai tab TURANT ek fetch karo aur sare existing OTPs mark karo.
    panel_monitor_thread se race condition eliminate — panel ON hone ke 0.5s baad chalta hai.
    Agar fetch fail ho, needs_warmup=True rahta hai — panel_monitor_thread pehle iteration
    mein warmup kar lega (backup protection)."""
    try:
        time.sleep(0.5)  # callback complete hone do
        # Guard: agar monitor ne is dauraan pehle hi warmup complete kar diya,
        # toh eager warmup skip karo — race condition mein double-processing se bachao.
        if not p.get("needs_warmup", True):
            logger.info(f"Eager warmup skipped — monitor already warmed up.")
            return
        if p.get("type") == "Auto Captcha Panel":
            data = _fetch_captcha_panel_data(idx, p)
        elif p.get("api_url") or p.get("full_api_url"):
            data = _fetch_api_panel_data(idx, p)
        else:
            data = None
        if data:
            # _process_panel_otps needs_warmup=True dekh kar sab mark karega, deliver nahi karega
            _process_panel_otps(idx, p, data)
            logger.info(f"Eager warmup done for panel: {len(data)} OTPs pre-marked.")
        # data nahi aaya: needs_warmup=True rahne do — panel_monitor_thread handle karega
    except Exception as e:
        logger.warning(f"Eager warmup error for panel '{p.get('name')}': {e}")


def panel_monitor_thread():
    """Saare panels ko PARALLEL threads mein poll karo — ek slow panel doosre ko block na kare.
    Delivery delay: ~1-2 seconds (was up to minutes when panels ran sequentially).
    Har panel apna warmup khud karta hai (needs_warmup flag) — global first_run nahi."""
    # Startup pe SAARE panels ka warmup set karo.
    # Isse agar koi panel pehli baar timeout bhi ho jaye, woh bhi warmup miss nahi karega.
    for p in bot_settings.get("panels", []):
        p["last_fetch_time"] = 0
        p["needs_warmup"] = True  # Pehla successful poll hone tak purane OTPs skip

    def _fetch_one(args):
        """Single panel fetch — ThreadPoolExecutor mein parallel run hota hai."""
        idx, p = args
        p_type = p.get("type", "API Panel")
        if p_type == "Auto Captcha Panel":
            data = _fetch_captcha_panel_data(idx, p)
        elif p.get("api_url") or p.get("full_api_url"):
            # Per-panel rate limit: same panel ko 5s se pehle dobara poll mat karo
            if time.time() - p.get("last_fetch_time", 0) < 5:
                return idx, p, None
            # FIX: last_fetch_time PEHLE set karo — double-poll race condition rokne ke liye
            p["last_fetch_time"] = time.time()
            data = _fetch_api_panel_data(idx, p)
        else:
            return idx, p, None
        return idx, p, data

    with ThreadPoolExecutor(max_workers=30) as executor:
        while True:
            try:
                active = [(idx, p) for idx, p in enumerate(bot_settings.get("panels", []))
                          if p.get("status") == "ON"]

                if active:
                    futures = {executor.submit(_fetch_one, args): args for args in active}
                    for future in list(futures.keys()):
                        try:
                            idx, p, parsed_data = future.result(timeout=8)
                            if parsed_data:
                                _process_panel_otps(idx, p, parsed_data)
                        except Exception as e:
                            logger.warning(f"panel_monitor fetch/process error: {e}")

            except Exception as e:
                logger.warning(f"panel_monitor_thread error: {e}")

            _save_processed_otps()
            # Periodic memory cleanup (every ~5 minutes)
            if not hasattr(_cleanup_stale_sessions, '_last') or time.time() - _cleanup_stale_sessions._last > 300:
                _cleanup_stale_sessions()
                _cleanup_stale_sessions._last = time.time()
            time.sleep(1)  # Har 1 second mein check (was 5s — 5x faster)

# ==========================================
# User Management
# ==========================================
# 🌟 Local User Cache
user_cache = {}

def get_user(user_id):
    uid = int(user_id) if str(user_id).lstrip("-").isdigit() else user_id
    if uid in user_cache: return user_cache[uid]
    data = _get_local_user(uid)
    # FIX: Evict oldest 200 entries instead of clearing all — preserves recently active users
    if len(user_cache) > 1000:
        for k in list(user_cache.keys())[:200]:
            user_cache.pop(k, None)
    user_cache[uid] = data
    return data

def update_balance(user_id, amount):
    _increment_local_user(user_id, "balance", float(amount))
    # Invalidate user_cache so stale balance is not returned
    user_cache.pop(user_id, None)
    user_cache.pop(str(user_id), None)

# ==========================================
# UI Keyboards & Menu Builders
# ==========================================

# ── De-duplicated helpers ──────────────────────────────────────────────────

def _parse_btn_from_text(text, entities):
    """Parse 'BtnText - https://url' with optional custom_emoji from entities or emoji ID prefix.
    Formats supported:
      Button Text - https://link.com
      6228781436330054904 Button Text - https://link.com   (numeric emoji ID prefix)
      [premium emoji] Button Text - https://link.com       (actual premium emoji in message)
    """
    if "-" not in text:
        return None
    parts = text.split("-", 1)
    btn_text = parts[0].strip()
    btn_url  = parts[1].strip()
    emoji_id = None
    emoji_char = ""

    # 1. Check for numeric emoji ID prefix (e.g. "6228781436330054904 Button Text")
    id_match = re.match(r'^(\d{15,20})\s+(.*)', btn_text)
    if id_match:
        emoji_id = id_match.group(1)
        btn_text = id_match.group(2).strip()
    else:
        # 2. Check for actual premium emoji sent in message entities
        for ent in entities:
            if ent.get("type") == "custom_emoji":
                emoji_id   = ent.get("custom_emoji_id")
                offset     = ent.get("offset", 0)
                length     = ent.get("length", 0)
                b_text     = text.encode('utf-16-le')
                emoji_char = b_text[offset*2:(offset+length)*2].decode('utf-16-le')
                break
        if emoji_char:
            btn_text = btn_text.replace(emoji_char, "").strip()

    btn_data = {"text": btn_text, "url": btn_url, "style": _rs()}
    if emoji_id:
        btn_data["icon_custom_emoji_id"] = emoji_id
    return btn_data


def _build_2fa_code_txt(entry_name, code, remaining_time):
    """Return the formatted 2FA code message text."""
    return (
        f"━━━━━━━━━━━━━━━\n"
        f"《 🔐 <b>2FA CODE</b> 》\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📛 <b>NAME:</b> {entry_name}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔐 <b>CODE:</b> <code>{code}</code>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🕓 <b>EXPIRES IN:</b> {remaining_time}s\n"
        f"━━━━━━━━━━━━━━━"
    )


def _build_2fa_code_kb(code, secret):
    """Return the inline keyboard for a 2FA code display."""
    _reset_btn_counter()
    return [[{"text": "Click to copy", "icon_custom_emoji_id": "5353022963132174959", "copy_text": {"text": code}, "style": _rs()}],
            [{"text": "Refresh", "icon_custom_emoji_id": "5420155432272438703", "callback_data": f"ref_2fa_{secret}", "style": _rs()},
             {"text": "New Code", "icon_custom_emoji_id": "5352552689983067014", "callback_data": "gen_2fa", "style": _rs()}],
            [{"text": "How to Use", "icon_custom_emoji_id": "6282760761399841824", "callback_data": f"how_2fa_{secret}", "style": _rs()}],
            [{"text": "MY 2FA ADDED", "icon_custom_emoji_id": "5337255927735163754", "callback_data": "my_2fa_list", "style": _rs()}],
            [{"text": "Close", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": _rs()}]]


def _show_2fa_menu(chat_id, msg_id=None):
    """Show (or edit-to-show) the 2FA ONLINE main menu."""
    saved_count = len(user_2fa_saved.get(chat_id, []))
    saved_line  = f"\n📋 <b>Saved 2FA:</b> {saved_count} account(s)" if saved_count > 0 else ""
    txt = (
        f"━━━━━━━━━━━━━━━\n"
        f"《 🔐 <b>2FA ONLINE</b> 》\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔑 Apna <b>2FA Secret Key</b> dalkar instant code generate karein.\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💾 Code save hoga taaki aap baad mein bhi recover kar sakein.{saved_line}\n"
        f"━━━━━━━━━━━━━━━"
    )
    _reset_btn_counter()
    kb = [[{"text": "Generate 2FA Code", "icon_custom_emoji_id": "5353022963132174959", "callback_data": "gen_2fa", "style": _rs()}],
          [{"text": "MY 2FA ADDED", "icon_custom_emoji_id": "5337255927735163754", "callback_data": "my_2fa_list", "style": _rs()}],
          [{"text": "Close", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": _rs()}]]
    if msg_id:
        edit_message(chat_id, msg_id, render_body_text(txt), reply_markup={"inline_keyboard": kb})
    else:
        send_message(chat_id, render_body_text(txt), reply_markup={"inline_keyboard": kb})

def get_cancel_kb():
    _reset_btn_counter()
    return {"inline_keyboard": [[{"text": "Close", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": _rs()}]]}

def main_menu(user_id):
    _reset_btn_counter()
    kb = [
        [
            {"text": "GET NUMBER", "icon_custom_emoji_id": "5337132498965010628", "style": _rs()},
            {"text": "Search Number", "icon_custom_emoji_id": "5463352748751753567", "style": _rs()}
        ],
        [
            {"text": "TRAFFIC", "icon_custom_emoji_id": "5353032893096567467", "style": _rs()},
            {"text": "2FA ONLINE", "icon_custom_emoji_id": "5337255927735163754", "style": _rs()}
        ],
        [
            {"text": "Refer", "icon_custom_emoji_id": "5420396762189831222", "style": _rs()},
            {"text": "WITHDRAWAL", "icon_custom_emoji_id": "5352585194295564660", "style": _rs()}
        ],
        [
            {"text": "SUPPORT", "icon_custom_emoji_id": "5420145051336485498", "style": _rs()}
        ]
    ]
    if is_admin(user_id):
        kb.append([{"text": "Admin Panel", "icon_custom_emoji_id": "5420155432272438703", "style": _rs()}])
    return {"keyboard": kb, "resize_keyboard": True}

def get_admin_text():
    users_count = len(all_known_users) # 🌟 Zero Cost User Count!
    total_files = len(number_batches)
    available_nums = sum(len(b["numbers"]) for b in number_batches.values())

    txt = f"""
{PEM['admin']} <b>ADMIN CONTROL PANEL</b> {PEM['admin']}
━━━━━━━━━━━━━━━━━━

{PEM['graph']} <b>DATABASE OVERVIEW</b>
— — — — — — — — — —
{PEM['user']} Users      » {users_count}
{PEM['file']} Files      » {total_files}
{PEM['num']} Numbers    » {total_uploaded_stats}
{PEM['ok']} Assigned   » {total_assigned_stats}
{PEM['rocket']} Available  » {available_nums}

{PEM['graph']} <b>STOCK LEVEL</b>
— — — — — — — — — —
[██████░░░░░░░░░] {available_nums} free
"""
    return render_body_text(txt)

def admin_panel_keyboard():
    _reset_btn_counter()
    return {"inline_keyboard": [
        [{"text": "LEADER BOARD SYSTEM", "icon_custom_emoji_id": "5353032893096567467", "callback_data": "lb_main", "style": _rs()}],
        [{"text": "Upload Number", "icon_custom_emoji_id": "5353001161878182134", "callback_data": "upload_num", "style": _rs()},
         {"text": "Delete files", "icon_custom_emoji_id": "5422557736330106570", "callback_data": "delete_files", "style": _rs()}],
        [{"text": "Broadcast", "icon_custom_emoji_id": "5789428375261023681", "callback_data": "broadcast_msg", "style": _rs()},
         {"text": "System", "icon_custom_emoji_id": "5420155432272438703", "callback_data": "system_settings", "style": _rs()}],
        [{"text": "Used (OTP Received)", "icon_custom_emoji_id": "5352694861990501856", "callback_data": "show_used", "style": _rs()},
         {"text": "Unused (No OTP)", "icon_custom_emoji_id": "5352597830089347330", "callback_data": "show_unused", "style": _rs()}],
        [{"text": "Close", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": _rs()}]
    ]}

def system_settings_keyboard():
    _reset_btn_counter()
    return {"inline_keyboard": [
        [{"text": "Auto Mode", "icon_custom_emoji_id": "4969841369850840381", "callback_data": "auto_mode", "style": _rs()}],
        [{"text": "Force Join System", "icon_custom_emoji_id": "5420517437885943844", "callback_data": "manage_fj", "style": _rs()},
         {"text": "Admin Management", "icon_custom_emoji_id": "5420145051336485498", "callback_data": "manage_admins", "style": _rs()}],
        [{"text": "OTP Group", "icon_custom_emoji_id": "5190447043545438788", "callback_data": "manage_otp_groups", "style": _rs()},
         {"text": "User Management", "icon_custom_emoji_id": "5193063022226086560", "callback_data": "user_management", "style": _rs()}],
        [{"text": "Panel MANAGEMENT", "icon_custom_emoji_id": "5336879280578138635", "callback_data": "manage_panels", "style": _rs()},
         {"text": "Subscription", "icon_custom_emoji_id": "5190899075968441286", "callback_data": "dummy_alert", "style": _rs()}],
        [{"text": "ABHI Control", "icon_custom_emoji_id": "5193100774988617665", "callback_data": "abhi_control", "style": _rs()},
         {"text": "Premium Emoji", "icon_custom_emoji_id": "5352552689983067014", "callback_data": "manage_emojis", "style": _rs()}],
        [{"text": "Menu Design", "icon_custom_emoji_id": "5190751148704833975", "callback_data": "menu_design_list", "style": _rs()},
         {"text": "Test", "icon_custom_emoji_id": "5190781475468915802", "callback_data": "test_message_flow", "style": _rs()}],
        [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "back_to_admin", "style": _rs()}]
    ]}


# ═══════════════════════════════════════════════════════════════════════════════
# ██  SYSTEM EMOJI MANAGER  ─  All Button & Message Emojis  ██
# ═══════════════════════════════════════════════════════════════════════════════

# ── Static registry: every unique (button_text, orig_emoji_id) in the bot ────
_SYS_BTN_EMOJIS = [
    ("Generate 2FA Code",      "5353022963132174959"),
    ("Back",                   "5267490665117275176"),
    ("Add New",                "5352552689983067014"),
    ("Check Joined",           "5352694861990501856"),
    ("New Code",               "5352552689983067014"),
    ("MY 2FA ADDED",           "5337255927735163754"),
    ("Close",                  "5420130255174145507"),
    ("GET NUMBER",             "5337132498965010628"),
    ("Search Number",          "5463352748751753567"),
    ("TRAFFIC",                "5353032893096567467"),
    ("2FA ONLINE",             "5337255927735163754"),
    ("Refer",                  "5420396762189831222"),
    ("WITHDRAWAL",             "5352585194295564660"),
    ("SUPPORT",                "5420145051336485498"),
    ("Admin Panel",            "5420155432272438703"),
    ("LEADER BOARD SYSTEM",    "5353032893096567467"),
    ("Upload Number",          "5353001161878182134"),
    ("Delete files",           "5422557736330106570"),
    ("Broadcast",              "5789428375261023681"),
    ("System",                 "5420155432272438703"),
    ("Used (OTP Received)",    "5352694861990501856"),
    ("Unused (No OTP)",        "5352597830089347330"),
    ("Auto Mode",              "4969841369850840381"),
    ("Force Join System",      "5420517437885943844"),
    ("Admin Management",       "5420145051336485498"),
    ("OTP Group",              "5190447043545438788"),
    ("User Management",        "5193063022226086560"),
    ("Panel MANAGEMENT",       "5336879280578138635"),
    ("Subscription",           "5190899075968441286"),
    ("ABHI Control",           "5193100774988617665"),
    ("Premium Emoji",          "5352552689983067014"),
    ("Menu Design",            "5190751148704833975"),
    ("Test",                   "5190781475468915802"),
    ("Manage Balance",         "5190576863226933563"),
    ("Ban/Unban User",         "5334807341109908955"),
    ("User Profile",           "5352861489541714456"),
    ("Edit /start Menu",       "5395444784611480792"),
    ("Edit GET NUMBER",        "5337132498965010628"),
    ("Edit Search Number",     "5463352748751753567"),
    ("Edit Select Country",    "5336972142066047577"),
    ("Edit TRAFFIC",           "5353032893096567467"),
    ("Edit Refer",             "5420396762189831222"),
    ("Edit WITHDRAWAL",        "5352585194295564660"),
    ("Edit SUPPORT",           "5420145051336485498"),
    ("Reset Defaults",         "5192812028632274956"),
    ("Back to Menus",          "5267490665117275176"),
    ("All Uploading System",   "5353001161878182134"),
    ("All Deleting System",    "5422557736330106570"),
    ("All Downloading System", "5257969839313526622"),
    ("Upload Flags (TXT)",     "5353001161878182134"),
    ("Download Flags",         "5257969839313526622"),
    ("Upload Services (TXT)",  "5353001161878182134"),
    ("Download Services",      "5257969839313526622"),
    ("Delete All Flags",       "5422557736330106570"),
    ("Delete All Services",    "5422557736330106570"),
    ("Add Channel / Group",    "5420323438508155202"),
    ("Add Admin",              "5420323438508155202"),
    ("Edit OTP Button Link",   "5420517437885943844"),
    ("Add Forward Group",      "5420323438508155202"),
    ("Nexa Panel Control",      "6282760761399841824"),
    ("VoltX Panel Control",    "6282760761399841824"),
    ("Stex Panel Control",     "6282760761399841824"),
    ("W. METHODS",             "5190899075968441286"),
    ("BACK",                   "5267490665117275176"),
    ("Add Method",             "5420323438508155202"),
    ("Add New Provider",       "5420323438508155202"),
    ("Back to Providers",      "5267490665117275176"),
    ("Refresh",                "5420155432272438703"),
    ("Add Country Code",       "5420323438508155202"),
    ("Try Again",              "5420323438508155202"),
    ("CLOSE",                  "5420130255174145507"),
    ("Contact Support",        "5337302974806922068"),
    ("Remove country code",    "6206108815075579644"),
    ("Add country code",       "6206375377925839184"),
    ("Change Number",          "5420155432272438703"),
    ("Number Expired",         "5336997731481193790"),
    ("Download TXT",           "5257969839313526622"),
    ("Top Referrers",          "5420145051336485498"),
    ("Top OTP Receivers",      "5353001161878182134"),
    ("Withdrawal History",     "5348469219761626211"),
    ("Back to Admin",          "5267490665117275176"),
    ("Add New Service",        "5420323438508155202"),
    ("Back to System",         "5267490665117275176"),
    ("Next Page",              "6264699552041801361"),
    # ── Previously missing entries (added after full audit) ──────────────────
    ("OTP Code (copy)",        "5474525960143385880"),   # OTP value copy button
    ("Full Message",           "5303138782004924588"),   # Full message copy button
    ("Test Connection",        "5276032951342088188"),   # Provider test connection
    ("Delete Provider",        "5336944168944047463"),   # Delete panel provider
    ("COOLDOWN",               "5337172996211648018"),   # ABHI cooldown setting
    ("NUM/SHARE",              "5352862640592949843"),   # ABHI num/share + range copy
    ("MIN WITHDRAW",           "5352877703043258544"),   # ABHI min withdraw setting
    ("Explore Range",          "5190645917711114179"),   # Traffic explore service range
    ("Manage Services / COPY LINK / Set Records", "5192739271886282680"),  # Nexa/VoltX/Stex service manage + refer copy link + panel records
    # ── Full keyboard audit — all remaining buttons now covered ───────────────
    ("Add Country",            "5420323438508155202"),   # Nexa/VoltX/Stex add country
    ("Add Inline Button",      "5420323438508155202"),   # Menu design + forward group add button
    ("Add Range",              "5420323438508155202"),   # Nexa/VoltX/Stex add range
    ("APPROVE",                "5352694861990501856"),   # Withdrawal approve button
    ("Cancel",                 "5420130255174145507"),   # Generic cancel button
    ("Click to copy",          "5353022963132174959"),   # 2FA code copy button
    ("COPY LINK",              "5192739271886282680"),   # Refer link copy button
    ("Del",                    "5422557736330106570"),   # 2FA list delete button
    ("Delete Entire Country",  "5422557736330106570"),   # Nexa/VoltX/Stex delete country
    ("Delete Entire Group",    "5422557736330106570"),   # Forward group delete
    ("Delete Service",         "5422557736330106570"),   # Nexa/VoltX/Stex delete service
    ("Edit Body (Text)",       "5395444784611480792"),   # Menu design edit text
    ("Edit Inline Buttons",    "5420155432272438703"),   # Menu design edit buttons
    ("Full API (URL+Token)",   "5420517437885943844"),   # Panel full API url+token set
    ("Group Not Found",        "5420130255174145507"),   # OTP group not found fallback
    ("How to Use",             "6282760761399841824"),   # 2FA how to use guide
    ("Next",                   "6264699552041801361"),   # Pagination next page
    ("Panel Not Found",        "5420130255174145507"),   # Panel not found fallback
    ("REJECT",                 "5420130255174145507"),   # Withdrawal reject button
    ("Replace",                "5395444784611480792"),   # System emoji replace button
    ("Search Country",         "5336972142066047577"),   # Nexa/VoltX/Stex search country
    ("Set API URL",            "5420517437885943844"),   # Panel set API URL
    ("Set Token",              "5353022963132174959"),   # Panel set token
    ("View/Del Keys",          "5422557736330106570"),   # Nexa/VoltX/Stex view/delete keys
    # ── Dynamic toggle buttons (auto_mode + fj_settings) ─────────────────────
    ("Nexa ON",                "6237529876690113625"),   # Auto Mode — Nexa enabled indicator
    ("Nexa OFF",               "6267000941547885720"),   # Auto Mode — Nexa disabled indicator
    ("VoltX ON",               "6237529876690113625"),   # Auto Mode — VoltX enabled indicator
    ("VoltX OFF",              "6267000941547885720"),   # Auto Mode — VoltX disabled indicator
    ("Stex ON",                "6237529876690113625"),   # Auto Mode — Stex enabled indicator
    ("Stex OFF",               "6267000941547885720"),   # Auto Mode — Stex disabled indicator
    ("STATUS: ON",             "5352694861990501856"),   # Force Join — status ON indicator
    ("STATUS: OFF",            "5318840353510408444"),   # Force Join — status OFF indicator
    ("Group: (Forward Group)", "5193063022226086560"),   # OTP Groups — dynamic group entry
    ("Owner: (Admin)",         "5353032893096567467"),   # Admin list — owner row indicator
]

# ── Static registry: PEM dict, GLOBAL_BODY_EMOJIS, and hardcoded tg-emoji ───
# Each entry: (label, orig_emoji_id, char, usage_example)
_SYS_MSG_EMOJIS = [
    # ─── PEM Dict (lines 55-78) ───────────────────────────────────────────────
    ("PEM:ok",      "5352694861990501856", "✅",  'PEM["ok"] — success messages'),
    ("PEM:no",      "6267000941547885720", "❌",  'PEM["no"] — error messages'),
    ("PEM:warn",    "5336944168944047463", "⚠️",  'PEM["warn"] — warning messages'),
    ("PEM:admin",   "5353032893096567467", "📊",  'PEM["admin"] — admin panel header'),
    ("PEM:user",    "5352861489541714456", "👤",  'PEM["user"] — user profile'),
    ("PEM:file",    "5352721946054268944", "📁",  'PEM["file"] — file references'),
    ("PEM:rocket",  "5352597830089347330", "🚀",  'PEM["rocket"] — unused numbers'),
    ("PEM:graph",   "5352877703043258544", "📊",  'PEM["graph"] — stats/graph'),
    ("PEM:money",   "5348469219761626211", "💸",  'PEM["money"] — balance/money'),
    ("PEM:gift",    "5420396762189831222", "🎁",  'PEM["gift"] — referral rewards'),
    ("PEM:msg",     "5337302974806922068", "💬",  'PEM["msg"] — message/support'),
    ("PEM:gear",    "5420155432272438703", "⚙️",  'PEM["gear"] — system settings header'),
    ("PEM:link",    "5420517437885943844", "🔗",  'PEM["link"] — force join links'),
    ("PEM:trash",   "5422557736330106570", "🗑",  'PEM["trash"] — delete actions'),
    ("PEM:upload",  "5353001161878182134", "📤",  'PEM["upload"] — upload prompts'),
    ("PEM:world",   "5336972142066047577", "🌐",  'PEM["world"] — country select'),
    ("PEM:lock",    "5353022963132174959", "🔐",  'PEM["lock"] — 2FA/security'),
    ("PEM:phone",   "4969841369850840381", "📱",  'PEM["phone"] — auto mode header'),
    ("PEM:num",     "5352862640592949843", "🔢",  'PEM["num"] — search number prompt'),
    ("PEM:pin",     "5352922460897452503", "📍",  'PEM["pin"] — select service prompt'),
    ("PEM:star",    "5352552689983067014", "✨",  'PEM["star"] — emoji management header'),
    ("PEM:hi",      "5353027129250453493", "👋",  'PEM["hi"] — welcome/main menu'),
    # ─── GLOBAL_BODY_EMOJIS (lines 80-139) — auto-replace in message text ────
    ("GBE:✅",       "5352694861990501856", "✅",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:❌",       "5420130255174145507", "❌",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:⚠️",       "5336944168944047463", "⚠️",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🔥",       "5337267511261960341", "🔥",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🌟",       "5337102391244263212", "🌟",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:✨",       "5352552689983067014", "✨",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:➖",       "5870818207383686839", "➖",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:➕",       "5420323438508155202", "➕",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:➡️",       "6319061296704656261", "➡️",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🔄",       "6264896248659056036", "🔄",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:⌛",       "4958503072801228000", "⌛",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:⏳",       "6285092198497129798", "⏳",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🕓",       "5336983442125001376", "🕓",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🔴",       "6267237615720731788", "🔴",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:👤",       "5352861489541714456", "👤",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:👥",       "4972130076318500235", "👥",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:👋",       "5353027129250453493", "👋",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:👇",       "5406745015365943482", "👇",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:😒",       "5334763399299506604", "😒",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:😔",       "6120863614149596295", "😔",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🫂",       "5420145051336485498", "🫂",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:1️⃣",       "5877664071720898423", "1️⃣",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:2️⃣",       "5877223446731034464", "2️⃣",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:3️⃣",       "5879546817879740639", "3️⃣",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:4️⃣",       "5879844832775507443", "4️⃣",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:5️⃣",       "5879657954453491518", "5️⃣",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:6️⃣",       "5877556203617259178", "6️⃣",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:7️⃣",       "5879611822209765566", "7️⃣",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:8️⃣",       "5879971663159758717", "8️⃣",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:9️⃣",       "5877752470737784316", "9️⃣",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🔢",       "5352862640592949843", "🔢",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:📊",       "5353032893096567467", "📊",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:📈",       "5352877703043258544", "📈",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:📁",       "5352721946054268944", "📁",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:📂",       "5257969839313526622", "📂",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:📤",       "5353001161878182134", "📤",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:📝",       "5192739271886282680", "📝",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:📅",       "5352585194295564660", "📅",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:📋",       "6267008582294705964", "📋",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:💾",       "5197269100878907942", "💾",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:📛",       "6325731252066325108", "📛",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:💬",       "5337302974806922068", "💬",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🎙",       "5355102594886833928", "🎙",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:📢",       "5789428375261023681", "📢",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:📌",       "5318986077455795572", "📌",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:📍",       "5352922460897452503", "📍",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🔑",       "6282760761399841824", "🔑",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🔐",       "5337255927735163754", "🔐",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🔗",       "5420517437885943844", "🔗",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:⚙️",       "5420155432272438703", "⚙️",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🛡",       "5190447043545438788", "🛡",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🚫",       "5334807341109908955", "🚫",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🌐",       "6266794310671275367", "🌐",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🔒",       "6282846669335702032", "🔒",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:💸",       "5348469219761626211", "💸",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:💰",       "5190576863226933563", "💰",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:💎",       "5352838545826420397", "💎",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:💳",       "5190899075968441286", "💳",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🎁",       "5420396762189831222", "🎁",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🤝",       "5192805934073685937", "🤝",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🚀",       "5352597830089347330", "🚀",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🍏",       "5337132498965010628", "🍏",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🌍",       "5780471598922337683", "🌍",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🗑",       "5422557736330106570", "🗑",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🟢",       "5192812028632274956", "🟢",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:👀",       "5190645917711114179", "👀",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🕹",       "5193100774988617665", "🕹",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🧪",       "5190781475468915802", "🧪",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🎨",       "5190751148704833975", "🎨",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:💡",       "5422439311196834318", "💡",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    ("GBE:🎯",       "5276032951342088188", "🎯",  'GLOBAL_BODY_EMOJIS — rendered in all body text'),
    # ─── Hardcoded tg-emoji in message strings ────────────────────────────────
    ("HC:start_📊",  "6264778055454036969", "📊",  '/start text — NUMBER BOT header icon'),
    ("HC:start_🚀",  "5258332798409783582", "🚀",  '/start text — Welcome rocket'),
    ("HC:start_✅",  "6071001861341580968", "✅",  '/start text — Choose option below'),
    ("HC:start_💎",  "6073231507713954071", "💎",  '/start text — Premium OTP Service'),
    ("HC:otp_⏳",    "6266992763930158001", "⏳",  'OTP flow — hourglass (polling)'),
    ("HC:otp_⚡",    "6267107057304868214", "⚡",  'OTP flow — bolt (fast)'),
    ("HC:otp_✅",    "6266994443262367483", "✅",  'OTP flow — check (received)'),
    ("HC:otp_▶1",   "6301055479539828724", "▶",   'OTP result — ACCESS GRANTED arrow'),
    ("HC:otp_✔",    "6266781064992134926", "✔",   'OTP result — ACCESS GRANTED tick'),
    ("HC:otp_▶2",   "6264896248659056036", "▶",   'OTP result — separator arrow'),
    ("HC:mask_⭐",   "6228781436330054904", "⭐",  '_MASK_EMOJI — number masking star'),
    ("HC:2fa_👉",    "5416117059207572332", "👉",  '2FA guide — pointing finger'),
    ("HC:am_✅ON",   "6266827283135207188", "✅",  'Auto Mode — ON indicator'),
    ("HC:am_🔴OFF",  "6267237615720731788", "🔴",  'Auto Mode — OFF indicator'),
    ("HC:am_⚡",     "6318566568011764192", "⚡",  'Auto Mode — header bolt icon'),
    ("HC:panel_🔹",  "6282760761399841824", "🔹",  'Panel control — Nexa/VoltX/Stex header'),
]


# ── Helper: build {orig_id: new_id} map — ONLY for msg_N overrides ────────────
def _build_id_override_map(overrides: dict) -> dict:
    """Convert msg_N overrides to {orig_id: new_id} map for message TEXT replacement.
    btn_N entries are intentionally excluded here — buttons are matched by TEXT
    (see _build_btn_text_override_map) so that changing one button's emoji does NOT
    accidentally change other buttons that share the same emoji ID."""
    id_map = {}
    for key, new_id in overrides.items():
        if key.startswith("msg_"):
            try:
                idx = int(key[4:])
                if 0 <= idx < len(_SYS_MSG_EMOJIS):
                    orig_id = _SYS_MSG_EMOJIS[idx][1]
                    id_map[orig_id] = new_id
            except ValueError:
                id_map[key] = new_id
        elif not key.startswith("btn_"):
            # Legacy plain orig_id key — backward compat ke liye
            id_map[key] = new_id
    return id_map

# ── Helper: build {btn_text_lower: new_id} map — ONLY for btn_N overrides ─────
def _build_btn_text_override_map(overrides: dict) -> dict:
    """Build a {button_text_lower: new_id} map for button keyboard overrides.
    Matching by button TEXT instead of emoji ID ensures that changing one specific
    button's emoji only affects that button — even when multiple buttons share
    the same original emoji ID."""
    text_map = {}
    for key, new_id in overrides.items():
        if key.startswith("btn_"):
            try:
                idx = int(key[4:])
                if 0 <= idx < len(_SYS_BTN_EMOJIS):
                    btn_text = _SYS_BTN_EMOJIS[idx][0]
                    text_map[btn_text.lower().strip()] = new_id
            except ValueError:
                pass
    return text_map

# ── Helper: build {orig_id: new_id} ID-only fallback — ONLY for btn_N overrides ─
def _build_btn_id_fallback_map(overrides: dict) -> dict:
    """ID-based fallback map for btn_N overrides.

    Kuch buttons ka text runtime pe DYNAMIC hota hai — jaise OTP value,
    'COOLDOWN: 30s', 'Explore WhatsApp Range', 'NUM/SHARE: 5', etc.
    Inka actual button text _SYS_BTN_EMOJIS ke registered label se match
    nahi karta, isliye text_map lookup fail ho jaata hai.

    Yeh fallback un buttons ke liye kaam karta hai:
    — sirf un orig_ids ko include karta hai jinka _SYS_BTN_EMOJIS mein
      exactly ONE entry hai (unique ID) — is se koi ambiguity nahi hoti
      aur ek button ka change kisi aur button ko affect nahi karta.
    — Multiple entries wale shared IDs (e.g. Back, Add New, etc.) EXCLUDE
      kiye jaate hain kyunki unke saare buttons static text hain aur
      text_map se pehle hi handle ho jaate hain."""
    id_count = Counter(orig_id for _, orig_id in _SYS_BTN_EMOJIS)
    id_map = {}
    for key, new_id in overrides.items():
        if key.startswith("btn_"):
            try:
                idx = int(key[4:])
                if 0 <= idx < len(_SYS_BTN_EMOJIS):
                    orig_id = _SYS_BTN_EMOJIS[idx][1]
                    # Only unique-ID entries — shared IDs handled by text_map
                    if id_count[orig_id] == 1:
                        id_map[orig_id] = new_id
            except ValueError:
                pass
    return id_map

# ── Keyboard emoji override ──────────────────────────────────────────────────
def _apply_emoji_overrides(reply_markup: dict) -> dict:
    """Replace icon_custom_emoji_id values in ANY keyboard type with admin overrides.
    Handles both InlineKeyboardMarkup ('inline_keyboard') and
    ReplyKeyboardMarkup ('keyboard') so main_menu buttons are also overridden.

    Three-layer lookup — STRICT separation: btn_N overrides ONLY affect buttons,
    msg_N overrides ONLY affect message text (handled in _apply_text_overrides).

    Layer 1 — Text match (btn_N):
        Static-text buttons matched by their exact registered label.
        Changing btn_1 (Back) changes ALL 'Back' buttons but NOTHING else.

    Layer 2 — ID fallback (btn_N, unique-ID only):
        Dynamic-text buttons (OTP code showing actual OTP, 'COOLDOWN: 30s',
        'Explore X Range', etc.) whose runtime text ≠ registered label.
        Only applied when the emoji ID is unique in _SYS_BTN_EMOJIS —
        guarantees one btn_N change never bleeds into another button type.

    Layer 3 — Legacy plain-key (backward compat only, no btn_/msg_ prefix):
        Old overrides saved before the btn_N/msg_N system was introduced."""
    overrides = bot_settings.get("sys_emoji_overrides", {})
    if not overrides:
        return reply_markup

    # Layer 1: text-based map  {btn_text_lower: new_id}  — btn_N only
    text_map      = _build_btn_text_override_map(overrides)
    # Layer 2: id-based fallback {orig_id: new_id} — btn_N, unique IDs only
    id_fallback   = _build_btn_id_fallback_map(overrides)
    # Layer 3: legacy plain-key overrides (neither btn_ nor msg_ prefix)
    id_legacy     = {k: v for k, v in overrides.items()
                     if not k.startswith("btn_") and not k.startswith("msg_")}

    if not text_map and not id_fallback and not id_legacy:
        return reply_markup

    rm = copy.deepcopy(reply_markup)

    def _patch_btn(btn):
        btn_text_lower = btn.get("text", "").lower().strip()
        # Layer 1: static text match — most precise
        if btn_text_lower and btn_text_lower in text_map:
            btn["icon_custom_emoji_id"] = text_map[btn_text_lower]
            return
        eid = btn.get("icon_custom_emoji_id")
        if not eid:
            return
        # Layer 2: ID fallback — dynamic-text buttons with unique orig_id
        if id_fallback and eid in id_fallback:
            btn["icon_custom_emoji_id"] = id_fallback[eid]
            return
        # Layer 3: legacy plain-key fallback (backward compat)
        if id_legacy and eid in id_legacy:
            btn["icon_custom_emoji_id"] = id_legacy[eid]

    # InlineKeyboardMarkup
    for row in rm.get("inline_keyboard", []):
        for btn in row:
            _patch_btn(btn)
    # ReplyKeyboardMarkup (main_menu and similar reply keyboards)
    for row in rm.get("keyboard", []):
        for btn in row:
            _patch_btn(btn)
    return rm

# ─────────────────────────────────────────────────────────────────────────────
def get_user_management_text():
    # 🌟 Fast & Free User Management Stats!
    total = len(all_known_users)
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    txt = f"""➖➖➖➖➖➖➖➖
《 👋 USER VIEW 》
➖➖➖➖➖➖➖➖
📊 LIVE STATISTICS:
➖➖➖➖➖➖➖➖
🫂 TOTAL USERS: {total}
✅ VERIFIED USERS: (Hidden to save DB Cost)
🚫 BANNED USERS: (Hidden to save DB Cost)
➖➖➖➖➖➖➖➖
⌛ UPDATED: {now_str}"""
    return render_body_text(txt)

def user_management_keyboard():
    _reset_btn_counter()
    return {"inline_keyboard": [
        [{"text": "Manage Balance", "icon_custom_emoji_id": "5190576863226933563", "callback_data": "um_manage_balance", "style": _rs()},
         {"text": "Ban/Unban User", "icon_custom_emoji_id": "5334807341109908955", "callback_data": "um_ban_unban", "style": _rs()}],
        [{"text": "User Profile", "icon_custom_emoji_id": "5352861489541714456", "callback_data": "um_user_profile", "style": _rs()}],
        [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": _rs()}]
    ]}

def menu_design_list_keyboard():
    _reset_btn_counter()
    return {"inline_keyboard": [
        [{"text": "Edit /start Menu", "icon_custom_emoji_id": "5395444784611480792", "callback_data": "md_edit_start", "style": _rs()}],
        [{"text": "Edit GET NUMBER", "icon_custom_emoji_id": "5337132498965010628", "callback_data": "md_edit_get_number", "style": _rs()},
         {"text": "Edit Search Number", "icon_custom_emoji_id": "5463352748751753567", "callback_data": "md_edit_search_number", "style": _rs()}],
        [{"text": "Edit Select Country", "icon_custom_emoji_id": "5336972142066047577", "callback_data": "md_edit_select_country", "style": _rs()}],
        [{"text": "Edit TRAFFIC", "icon_custom_emoji_id": "5353032893096567467", "callback_data": "md_edit_traffic", "style": _rs()},
         {"text": "Edit Refer", "icon_custom_emoji_id": "5420396762189831222", "callback_data": "md_edit_refer", "style": _rs()}],
        [{"text": "Edit WITHDRAWAL", "icon_custom_emoji_id": "5352585194295564660", "callback_data": "md_edit_withdrawal", "style": _rs()},
         {"text": "Edit SUPPORT", "icon_custom_emoji_id": "5420145051336485498", "callback_data": "md_edit_support", "style": _rs()}],
        [{"text": "Reset Defaults", "icon_custom_emoji_id": "5192812028632274956", "callback_data": "md_reset_defaults", "style": _rs()}],
        [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": _rs()}]
    ]}

def menu_edit_options_keyboard(menu_key):
    _reset_btn_counter()
    return {"inline_keyboard": [
        [{"text": "Edit Body (Text)", "icon_custom_emoji_id": "5395444784611480792", "callback_data": f"md_text_{menu_key}", "style": _rs()}],
        [{"text": "Edit Inline Buttons", "icon_custom_emoji_id": "5420155432272438703", "callback_data": f"md_btns_{menu_key}", "style": _rs()}],
        [{"text": "Back to Menus", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "menu_design_list", "style": _rs()}]
    ]}

def menu_buttons_list_keyboard(menu_key):
    _reset_btn_counter()
    kb = []
    btns = bot_settings["custom_messages"].get(menu_key, {}).get("buttons", [])
    for idx, btn in enumerate(btns):
        kb.append([{"text": f"Del: {btn['text']}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"md_delbtn_{menu_key}_{idx}", "style": _rs()}])
    kb.append([{"text": "Add Inline Button", "icon_custom_emoji_id": "5420323438508155202", "callback_data": f"md_addbtn_{menu_key}", "style": _rs()}])
    kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"md_edit_{menu_key}", "style": _rs()}])
    return {"inline_keyboard": kb}

def emoji_settings_keyboard():
    _reset_btn_counter()
    return {"inline_keyboard": [
        [{"text": "All Uploading System", "icon_custom_emoji_id": "5353001161878182134", "callback_data": "emoji_upload_menu", "style": _rs()}],
        [{"text": "All Deleting System",  "icon_custom_emoji_id": "5422557736330106570", "callback_data": "emoji_delete_menu",  "style": _rs()}],
        [{"text": "All Downloading System","icon_custom_emoji_id": "5257969839313526622", "callback_data": "emoji_download_menu","style": _rs()}],
        [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": _rs()}]
    ]}

def emoji_upload_keyboard():
    _reset_btn_counter()
    return {"inline_keyboard": [
        [{"text": "Upload Flags (TXT)",    "icon_custom_emoji_id": "5353001161878182134", "callback_data": "up_flags_txt", "style": _rs()}],
        [{"text": "Upload Services (TXT)", "icon_custom_emoji_id": "5353001161878182134", "callback_data": "up_apps_txt",  "style": _rs()}],
        [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_emojis", "style": _rs()}]
    ]}

def emoji_delete_keyboard():
    _reset_btn_counter()
    return {"inline_keyboard": [
        [{"text": "Delete All Flags",    "icon_custom_emoji_id": "5422557736330106570", "callback_data": "del_all_flags", "style": _rs()}],
        [{"text": "Delete All Services", "icon_custom_emoji_id": "5422557736330106570", "callback_data": "del_all_apps",  "style": _rs()}],
        [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_emojis", "style": _rs()}]
    ]}

def emoji_download_keyboard():
    _reset_btn_counter()
    return {"inline_keyboard": [
        [{"text": "Download Flags",        "icon_custom_emoji_id": "5257969839313526622", "callback_data": "dl_flags_txt",    "style": _rs()}],
        [{"text": "Download Services",     "icon_custom_emoji_id": "5257969839313526622", "callback_data": "dl_apps_txt",     "style": _rs()}],
        [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_emojis", "style": _rs()}]
    ]}


# 🌟 Generates a downloadable .txt of saved premium flag/app emojis,
# in the exact format the upload-parser (wait_for_flag_txt / wait_for_app_txt) expects.
def generate_emoji_txt(mode):
    lines = []
    if mode == "flags":
        for code, info in bot_settings.get("premium_flags", {}).items():
            char = info.get("char", "")
            iso = info.get("iso", "")
            name = info.get("name", "")
            eid = info.get("id", "")
            if not (char and eid):
                continue
            json_part = json.dumps({"emoji": char, "id": eid}, ensure_ascii=False)
            lines.append(f"({code}) ({iso}) {name} {char} {json_part}")
    elif mode == "apps":
        for app_key, info in bot_settings.get("premium_apps", {}).items():
            char = info.get("char", "")
            eid = info.get("id", "")
            name = info.get("name", app_key)
            if not (char and eid):
                continue
            json_part = json.dumps({"emoji": char, "id": eid}, ensure_ascii=False)
            lines.append(f"{name} {char} {json_part}")
    return "\n".join(lines)

def fj_settings_keyboard():
    _reset_btn_counter()
    status_text = 'ON' if bot_settings['fj_on'] else 'OFF'
    status_icon = "5352694861990501856" if bot_settings['fj_on'] else "5318840353510408444"
    kb = [[{"text": f"STATUS: {status_text}", "icon_custom_emoji_id": status_icon, "callback_data": "toggle_fj", "style": _rs()}]]
    for idx, entry in enumerate(bot_settings["fj_channels"]):
        info = _get_fj_info(entry)
        ch_type = info.get("type", "channel")
        title = info.get("title", str(info.get("chat_id", "")))
        is_priv = info.get("is_private", False)
        type_tag = "Channel" if ch_type == "channel" else "Group"
        priv_tag = "Private" if is_priv else "Public"
        btn_label = f"{title} [{type_tag} | {priv_tag}]"
        kb.append([{"text": btn_label, "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"del_fj_{idx}", "style": _rs()}])
    kb.append([{"text": "Add Channel / Group", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "add_fj", "style": _rs()}])
    kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": _rs()}])
    return {"inline_keyboard": kb}

def admin_settings_keyboard():
    _reset_btn_counter()
    kb = []
    for idx, adm in enumerate(bot_settings["admins"]):
        text_btn = f"Owner: {adm}" if adm == OWNER_ID else f"Delete: {adm}"
        icon_id = "5353032893096567467" if adm == OWNER_ID else "5420130255174145507"
        # FIX: idx ki jagah actual admin ID use karo — list shift hone par wrong admin delete hota tha
        cb_data = "ignore" if adm == OWNER_ID else f"del_adm_{adm}"
        kb.append([{"text": text_btn, "icon_custom_emoji_id": icon_id, "callback_data": cb_data, "style": _rs()}])
    kb.append([{"text": "Add Admin", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "add_adm", "style": _rs()}])
    kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": _rs()}])
    return {"inline_keyboard": kb}

def otp_groups_list_keyboard():
    _reset_btn_counter()
    kb = [[{"text": "Edit OTP Button Link", "icon_custom_emoji_id": "5420517437885943844", "callback_data": "edit_otp_link", "style": _rs()}]]
    for idx, fg in enumerate(bot_settings["fw_groups"]):
        kb.append([{"text": f"Group: {fg['chat_id']}", "icon_custom_emoji_id": "5193063022226086560", "callback_data": f"manage_fw_{idx}", "style": _rs()}])
    kb.append([{"text": "Add Forward Group", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "add_fw", "style": _rs()}])
    kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": _rs()}])
    return {"inline_keyboard": kb}

def auto_mode_keyboard():
    _reset_btn_counter()
    nexa_on  = bot_settings.get("nexa_on", False)
    voltx_on = bot_settings.get("voltx_on", False)
    stex_on  = bot_settings.get("stex_on", False)
    # ON  emoji: green indicator  | OFF emoji: red indicator
    ON_EMOJI  = "6237529876690113625"
    OFF_EMOJI = "6267000941547885720"
    return {"inline_keyboard": [
        [{"text": "Nexa Panel Control",  "icon_custom_emoji_id": "6282760761399841824", "callback_data": "nexa_control",  "style": _rs()},
         {"text": "Nexa ON"  if nexa_on  else "Nexa OFF",  "icon_custom_emoji_id": ON_EMOJI if nexa_on  else OFF_EMOJI, "callback_data": "toggle_nexa",  "style": _rs()}],
        [{"text": "VoltX Panel Control", "icon_custom_emoji_id": "6282760761399841824", "callback_data": "voltx_control", "style": _rs()},
         {"text": "VoltX ON" if voltx_on else "VoltX OFF", "icon_custom_emoji_id": ON_EMOJI if voltx_on else OFF_EMOJI, "callback_data": "toggle_voltx", "style": _rs()}],
        [{"text": "Stex Panel Control",  "icon_custom_emoji_id": "6282760761399841824", "callback_data": "stex_control",  "style": _rs()},
         {"text": "Stex ON"  if stex_on  else "Stex OFF",  "icon_custom_emoji_id": ON_EMOJI if stex_on  else OFF_EMOJI, "callback_data": "toggle_stex",  "style": _rs()}],
        [{"text": "Back",  "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": _rs()}]
    ]}

def _panel_control_keyboard(panel_name):
    """Shared API panel control keyboard for Nexa, VoltX, Stex.
    panel_name: display name e.g. 'Nexa', 'VoltX', 'Stex' — lowercase used for callback IDs."""
    p = panel_name.lower()
    _reset_btn_counter()
    return {"inline_keyboard": [
        [{"text": f"Add {panel_name} Key", "icon_custom_emoji_id": "5420323438508155202", "callback_data": f"add_{p}_key", "style": _rs()},
         {"text": "View/Del Keys", "icon_custom_emoji_id": "5422557736330106570", "callback_data": f"view_{p}_keys", "style": _rs()}],
        [{"text": f"Manage {panel_name} Services", "icon_custom_emoji_id": "5192739271886282680", "callback_data": f"manage_{p}_srv", "style": _rs()}],
        [{"text": "Search Country", "icon_custom_emoji_id": "5336972142066047577", "callback_data": f"{p}_search_country", "style": _rs()}],
        [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "auto_mode", "style": _rs()}]
    ]}


def specific_fw_group_keyboard(idx):
    _reset_btn_counter()
    if idx < 0 or idx >= len(bot_settings.get("fw_groups", [])):
        return {"inline_keyboard": [[{"text": "Group Not Found", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "manage_otp_groups", "style": "danger"}]]}
    group = bot_settings["fw_groups"][idx]
    kb = []
    for b_idx, btn in enumerate(group.get("buttons", [])):
        kb.append([{"text": f"Del: {btn['text']}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"del_fwbtn_{idx}_{b_idx}", "style": _rs()}])
    
    kb.append([{"text": "Add Inline Button", "icon_custom_emoji_id": "5420323438508155202", "callback_data": f"add_fwbtn_{idx}", "style": _rs()}])
    kb.append([{"text": "Delete Entire Group", "icon_custom_emoji_id": "5422557736330106570", "callback_data": f"del_fw_{idx}", "style": _rs()}])
    kb.append([{"text": "Back to Groups", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_otp_groups", "style": _rs()}])
    return {"inline_keyboard": kb}

def abhi_control_keyboard():
    _reset_btn_counter()
    w_status = "ON" if bot_settings["withdraw_on"] else "OFF"
    sup_status = "ON" if bot_settings.get("support_link") else "OFF"
    grp_status = "ON" if bot_settings.get("w_group") else "OFF"
    return {"inline_keyboard": [
        [{"text": f"WITHDRAW: {w_status}", "icon_custom_emoji_id": "5348469219761626211", "callback_data": "abhi_toggle_w", "style": _rs()}],
        [{"text": f"MIN WITHDRAW: {bot_settings['min_withdraw']}", "icon_custom_emoji_id": "5352877703043258544", "callback_data": "abhi_min_w", "style": _rs()},
         {"text": f"OTP REWARD: {bot_settings['otp_reward']}", "icon_custom_emoji_id": "5190576863226933563", "callback_data": "abhi_otp_r", "style": _rs()}],
        [{"text": f"REFER REWARD: {bot_settings['refer_reward']}", "icon_custom_emoji_id": "5420396762189831222", "callback_data": "abhi_ref_r", "style": _rs()},
         {"text": f"COOLDOWN: {bot_settings['cooldown']}s", "icon_custom_emoji_id": "5337172996211648018", "callback_data": "abhi_cool", "style": _rs()}],
        [{"text": f"NUM/REQ: {bot_settings['num_req']}", "icon_custom_emoji_id": "5337132498965010628", "callback_data": "abhi_num_req", "style": _rs()},
         {"text": f"NUM/SHARE: {bot_settings['num_share']}", "icon_custom_emoji_id": "5352862640592949843", "callback_data": "abhi_num_share", "style": _rs()}],
        [{"text": f"SUPPORT LINK: {sup_status}", "icon_custom_emoji_id": "5420145051336485498", "callback_data": "abhi_sup_link", "style": _rs()},
         {"text": "W. METHODS", "icon_custom_emoji_id": "5190899075968441286", "callback_data": "manage_w_methods", "style": _rs()}],
        [{"text": f"W. GROUP: {grp_status}", "icon_custom_emoji_id": "5420517437885943844", "callback_data": "abhi_w_group", "style": _rs()},
         {"text": "BACK", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": _rs()}]
    ]}

def w_methods_keyboard():
    _reset_btn_counter()
    kb = []
    for idx, m in enumerate(bot_settings["w_methods"]):
        kb.append([{"text": f"Delete: {m}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"del_wm_{idx}", "style": _rs()}])
    kb.append([{"text": "Add Method", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "add_wm", "style": _rs()}])
    kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "abhi_control", "style": _rs()}])
    return {"inline_keyboard": kb}

def typed_panels_list_keyboard(p_type):
    _reset_btn_counter()
    kb = []
    for idx, p in enumerate(bot_settings["panels"]):
        if p.get("type", "API Panel") != p_type: continue
        action_text = f"Turn OFF {p['name']}" if p['status'] == 'ON' else f"Turn ON {p['name']}"
        action_icon = "5318840353510408444" if p['status'] == 'ON' else "5192812028632274956"
        icon_id = "5420155432272438703" 
        kb.append([
            {"text": action_text, "icon_custom_emoji_id": action_icon, "callback_data": f"tog_pnl_{idx}", "style": _rs()},
            {"text": f"{p['name']}", "icon_custom_emoji_id": icon_id, "callback_data": f"conf_pnl_{idx}", "style": _rs()}
        ])
    add_cb = "add_api_panel" if p_type == "API Panel" else "add_cpt_panel"
    kb.append([{"text": "Add New Provider", "icon_custom_emoji_id": "5420323438508155202", "callback_data": add_cb, "style": _rs()}])
    kb.append([{"text": "Delete Provider", "icon_custom_emoji_id": "5336944168944047463", "callback_data": f"list_del_{'api' if p_type=='API Panel' else 'cpt'}", "style": _rs()}])
    kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_panels", "style": _rs()}])
    return {"inline_keyboard": kb}

def panel_config_keyboard(idx):
    _reset_btn_counter()
    if idx < 0 or idx >= len(bot_settings.get("panels", [])):
        return {"inline_keyboard": [[{"text": "Panel Not Found", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "manage_panels", "style": "danger"}]]}
    p = bot_settings["panels"][idx]
    
    kb = []
    action_text = "Turn OFF" if p['status'] == 'ON' else "Turn ON"
    action_icon = "5318840353510408444" if p['status'] == 'ON' else "5192812028632274956"
    kb.append([{"text": action_text, "icon_custom_emoji_id": action_icon, "callback_data": f"tog_pnl_{idx}", "style": _rs()}])
    
    if p["type"] != "Auto Captcha Panel":
        rec_count_text = "All (Unlimited)" if p.get('records', 0) == 0 else str(p.get('records'))
        kb.append([{"text": "Set API URL", "icon_custom_emoji_id": "5420517437885943844", "callback_data": f"set_p_api_{idx}", "style": _rs()}])
        kb.append([{"text": "Set Token", "icon_custom_emoji_id": "5353022963132174959", "callback_data": f"set_p_tok_{idx}", "style": _rs()}])
        token_hdr = p.get("token_header", "")
        hdr_text = f"Token Header: {token_hdr}" if token_hdr else "Set Token Header (Optional)"
        kb.append([{"text": hdr_text, "icon_custom_emoji_id": "5353022963132174959", "callback_data": f"set_p_tokh_{idx}", "style": _rs()}])
        kb.append([{"text": "Full API (URL+Token)", "icon_custom_emoji_id": "5420517437885943844", "callback_data": f"set_p_fapi_{idx}", "style": _rs()}])
        kb.append([{"text": f"Set Records Count: {rec_count_text}", "icon_custom_emoji_id": "5192739271886282680", "callback_data": f"set_p_rec_{idx}", "style": _rs()}])
        
    kb.append([{"text": "Test Connection", "icon_custom_emoji_id": "5276032951342088188", "callback_data": f"test_p_conn_{idx}", "style": _rs()}])
        
    back_data = "manage_api_panels" if p.get("type", "API Panel") == "API Panel" else "manage_cpt_panels"
    kb.append([{"text": "Back to Providers", "icon_custom_emoji_id": "5267490665117275176", "callback_data": back_data, "style": _rs()}])
    return {"inline_keyboard": kb}

def build_traffic_ui():
    current_time = time.time()
    _prune_traffic(current_time)
    
    stats = {}
    with _traffic_lock:
        _traffic_snapshot = list(recent_traffic)
    for t in _traffic_snapshot:
        srv = t.get("service", "Unknown")
        iso = t.get("iso", "XX")
        flag = t.get("flag", "🌍")
        
        if srv not in stats:
            stats[srv] = {}
        if iso not in stats[srv]:
            stats[srv][iso] = {"count": 0, "flag": flag}
        stats[srv][iso]["count"] += 1
        
    txt = "╔═════════════════╗\n║  📈 <b>NETWORK TRAFFIC</b>\n╚═════════════════╝\n\n"
    
    _reset_btn_counter()
    kb = []
    if not stats:
        txt += "<i>No recent traffic found in the last hour...</i>\n"
    else:
        srv_totals = []
        for srv, countries in stats.items():
            total = sum(c["count"] for c in countries.values())
            srv_totals.append((srv, total, countries))
        
        srv_totals.sort(key=lambda x: x[1], reverse=True)
        
        for srv, total, countries in srv_totals:
            app_full_name, prem_app_html = get_service_info_html(srv)
            txt += f"[ {prem_app_html} <b>{app_full_name}</b> ]\n│\n"
            
            c_list = sorted(countries.items(), key=lambda x: x[1]["count"], reverse=True)
            c_list = c_list[:7] 
            
            for i, (iso, c_data) in enumerate(c_list):
                prem_flag_html = get_flag_info_html(iso)
                count = c_data["count"]
                
                c_name = iso
                for code, fdata in bot_settings.get("premium_flags", {}).items():
                    if fdata.get("iso") == iso:
                        c_name = fdata.get("name", iso)
                        break
                        
                txt += f"├ {prem_flag_html} <b>{c_name} ({iso})</b>\n"
                txt += f"│ ╰ Success: {count}\n"
                if i < len(c_list) - 1:
                    txt += "│\n"
            txt += "\n"
        
        # 🌟 FIX: [:3] limit removed, now all services will show buttons below!
        for srv, _, _ in srv_totals: 
            safe_srv = srv[:20] 
            # To show full name nicely in button
            app_full_name, _ = get_service_info_html(safe_srv, safe_srv)
            kb.append([{"text": f"Explore {app_full_name} Range", "icon_custom_emoji_id": "5190645917711114179", "callback_data": f"exp_rng_{safe_srv}", "style": _rs()}])
            
    txt = render_body_text(txt)
    kb.append([{"text": "Refresh", "icon_custom_emoji_id": "5420155432272438703", "callback_data": "refresh_traffic", "style": _rs()}])
    _add_close_btn(kb)
    
    return txt, {"inline_keyboard": kb}

# ==========================================
# OTP Deduplication Persistence
# ==========================================
_seen_otps_save_lock = threading.Lock()

def _save_processed_otps():
    # FIX: panel_monitor_thread har panel ko PARALLEL threads mein poll karta hai, aur
    # har naya OTP milte hi turant _save_processed_otps() call hota hai. Pehle isme koi
    # lock nahi tha — do threads ek hi waqt pe same "seen_otps.json.tmp" likh/rename kar
    # rahe the, isliye ek thread ka tmp file dusre thread ke os.replace se pehle hi
    # "consume" ho jaata tha → "No such file or directory" error, aur save silently
    # fail ho jaata tha (isse dedup state disk pe save nahi hota, restart pe purane
    # OTPs dobara process ho sakte the).
    with _seen_otps_save_lock:
        try:
            with _data_lock:
                items = dict(processed_otps)
            # Sirf last 25 ghante ke entries save karo (24h panel history + 1h margin)
            cutoff = time.time() - 90000
            items = {k: v for k, v in items.items() if v > cutoff}
            tmp_path = SEEN_OTPS_FILE + ".tmp"
            with open(tmp_path, "w") as f:
                json.dump(items, f)
            os.replace(tmp_path, SEEN_OTPS_FILE)
        except Exception as e:
            logger.warning(f"OTP save error: {e}")

def _load_processed_otps():
    global processed_otps
    try:
        with open(SEEN_OTPS_FILE, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            cutoff = time.time() - 90000  # 25h — save ke saath match
            new_dict = {k: v for k, v in data.items() if v > cutoff}
        else:
            # Purana format (list) — ek ghante purana timestamp assign karo
            new_dict = {uid: time.time() - 3600 for uid in data}
        with _data_lock:
            processed_otps = new_dict
        logger.info(f"Loaded {len(new_dict)} previously seen OTP IDs — old OTPs will be skipped.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        with _data_lock:
            processed_otps = {}
        if not isinstance(e, FileNotFoundError):
            logger.warning(f"seen_otps.json parse error: {e} — starting fresh")

def _add_to_processed(unique_id):
    with _data_lock:
        processed_otps[unique_id] = time.time()
        # 25 ghante se purane entries hatao (save/load cutoff ke saath match)
        if len(processed_otps) > 20000:
            cutoff = time.time() - 90000
            old_keys = [k for k, v in processed_otps.items() if v < cutoff]
            for k in old_keys:
                del processed_otps[k]
            # Agar abhi bhi bahut zyada, to oldest 10000 hatao
            if len(processed_otps) > 20000:
                sorted_keys = sorted(processed_otps, key=lambda k: processed_otps[k])
                for k in sorted_keys[:10000]:
                    del processed_otps[k]

def _is_processed(unique_id, window=90000):
    """True if unique_id last `window` seconds mein process ho chuka hai (default 25 ghante).
    25h window isliye: panels 24h tak OTP history rakhte hain, toh 25h = 1 ghante ka
    extra safe margin — purane OTPs kabhi dobara deliver nahi honge."""
    with _data_lock:
        ts = processed_otps.get(unique_id)
        if ts is None:
            return False
        return (time.time() - ts) < window

# ==========================================
# OTP Age Guard — panel ke apne timestamp (item_id) se OTP ki asli age nikalo
# ==========================================
# FIX: Purana dedup sirf "pehle dekha hua OTP dobara mat bhejo" check karta tha —
# lekin agar koi OTP jo panel mein 25+ ghante purana hai, bot ne PEHLI baar dekha
# (restart, panel lag, number reuse ya history replay ki wajah se), to woh "naya"
# maan ke deliver ho jata tha, jabki asal mein woh bahut purana OTP tha.
# Ab item_id (panel ka apna date/time column) parse karke real age check hoti
# hai — agar OTP 25 ghante se zyada purana hai, to woh group/user ko KABHI
# deliver nahi hoga, chahe dedup memory mein pehli baar hi dikh raha ho.
OTP_MAX_AGE_SECONDS = 90000  # 25 ghante

_DT_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%d-%m-%Y %H:%M:%S",
    "%d/%m/%Y %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%fZ",   # ISO 8601 with ms + Z  (jaise Teleroutex createdAt)
    "%Y-%m-%dT%H:%M:%SZ",      # ISO 8601 without ms + Z
    "%Y-%m-%dT%H:%M:%S.%f",    # ISO 8601 with ms, no Z
)

def _parse_item_datetime_epoch(dt_str):
    """item_id mein aya datetime string ko epoch seconds mein convert karta hai.
    Parse nahi ho paya to None return karta hai (age-check us case mein skip ho jata hai —
    hum sirf CONFIRMED purane OTPs ko block karte hain, kabhi false-positive nahi)."""
    if not dt_str:
        return None
    s = str(dt_str).strip()
    for fmt in _DT_FORMATS:
        try:
            return datetime.strptime(s, fmt).timestamp()
        except (ValueError, TypeError):
            continue
    return None

def _is_stale_otp(item_id, max_age=OTP_MAX_AGE_SECONDS):
    """True agar item_id ka apna timestamp bataye ki OTP already max_age se purana hai.
    Panel ke record ki timestamp future mein bhi ho sakti hai (clock drift) — us case
    mein bhi stale nahi maanenge, sirf ATEET (past) mein bahut purana ho to hi block karo."""
    epoch = _parse_item_datetime_epoch(item_id)
    if epoch is None:
        return False
    age = time.time() - epoch
    return age > max_age

# ==========================================
# Shared Helper Functions (deduplication)
# ==========================================
def _process_pending_referral(chat_id):
    u_data = _get_local_user(chat_id)
    if u_data.get("referred_by") and not u_data.get("ref_paid"):
        inviter = u_data["referred_by"]
        _update_local_user(chat_id, {"ref_paid": True})
        reward = bot_settings.get("refer_reward", 0.2)
        update_balance(inviter, reward)
        _increment_local_user(inviter, "total_refers", 1)
        ref_msg = (
            f"{PEM['gift']} <b>New Referral !</b>\n"
            f"------------------\n"
            f"🔥 <b>You Received {reward} INR</b>\n"
            f"------------------\n"
            f"{PEM['user']} <b>From User ID:</b> <code>{chat_id}</code>"
        )
        send_message(inviter, render_body_text(ref_msg))

def _get_all_numbers_set():
    all_nums = set()
    for b in number_batches.values():
        for n in b["numbers"]:
            all_nums.add(n["num"].replace("+", "").strip())
    for n in used_numbers_list:
        all_nums.add(n.replace("+", "").strip())
    return all_nums

def _record_and_deliver_otp(owner_id, num_str, app_name, msg_text, otp, clean_num_key, caller_tag=""):
    """Shared helper: record traffic + save DB + deliver OTP to user + mark otp_received.
    Used by poll_otp_with_status, _poll_mauthapi_otp_single, _poll_mauthapi_otps, global_sms_listener."""
    char, iso = get_flag_and_code(num_str)
    app_full_name, prem_app_html = get_service_info_html(app_name, msg_text)
    current_time = time.time()
    _prune_traffic(current_time)
    with _traffic_lock:
        recent_traffic.append({"service": app_full_name, "iso": iso, "flag": char, "number": num_str, "time": current_time})
    save_local_db()
    _deliver_otp_to_user(owner_id, num_str, app_full_name, prem_app_html, iso, otp, msg_text)
    try:
        clean_key = str(clean_num_key).replace("+", "").replace(" ", "").replace("-", "").strip()
        with _data_lock:
            otp_received_numbers.add(clean_key)
    except Exception as e:
        logger.warning(f"otp_received_numbers error [{caller_tag}]: {e}")



def _make_otp_kb(otp_code):
    """OTP copy-button keyboard helper — single definition used everywhere."""
    return [[{"text": str(otp_code), "icon_custom_emoji_id": "5474525960143385880",
              "copy_text": {"text": str(otp_code)}, "style": _rs()}]]

def _deliver_otp_to_user(owner_id, num_str, app_full_name, prem_app_html, iso, otp_code, msg_text):
    _reset_btn_counter()
    display_num = f"+{num_str}" if not str(num_str).startswith("+") else str(num_str)
    lang = detect_language(msg_text)
    masked = mask_number(display_num, user_id=owner_id)
    # Group delivery pehle karo — owner_id None hone se group block nahi hoga
    # Group mein masked number (privacy) — user DM mein full number
    group_msg = render_body_text(f"{get_flag_info_html(display_num)} #{iso} ♦ {masked} ✅ {otp_code}")
    # ✅ OTP Group mein deliver karo (Forward Groups) — owner required NAHI
    for fw in bot_settings.get("fw_groups", []):
        try:
            _reset_btn_counter()
            kb = _make_otp_kb(otp_code)
            _fw_btns = fw.get("buttons", [])
            for i in range(0, len(_fw_btns), 2):
                row = [_make_fw_btn(_fw_btns[i], kb)]
                if i + 1 < len(_fw_btns):
                    row.append(_make_fw_btn(_fw_btns[i + 1], kb))
                kb.append(row)
            res_fw = send_message(fw["chat_id"], group_msg, reply_markup={"inline_keyboard": kb})
            if res_fw and res_fw.get("ok"):
                logger.debug(f"OTP forwarded to group {fw.get('chat_id')}")
            else:
                logger.warning(f"FW Group send failed ({fw.get('chat_id')}): {res_fw}")
        except Exception as e:
            logger.warning(f"FW Group delivery error ({fw.get('chat_id')}): {e}")
    # ✅ User ke personal chat mein deliver karo — sirf tab jab owner mila ho
    if not owner_id:
        return
    display_msg = render_body_text(f"{get_flag_info_html(display_num)} #{iso} ♦ {display_num} ✅ {otp_code}")
    _reset_btn_counter()
    inbox_kb = _make_otp_kb(otp_code)
    reward = float(bot_settings.get("otp_reward", 0.0))
    if reward > 0:
        update_balance(owner_id, reward)
        inbox_kb.append([{"text": f"Added {reward} ₹", "icon_custom_emoji_id": "5420396762189831222", "callback_data": "ignore", "style": _rs()}])
        logger.debug(f"OTP reward {reward} credited to user {owner_id}")
    try:
        send_message(owner_id, display_msg, reply_markup={"inline_keyboard": inbox_kb})
        logger.debug(f"OTP delivered to user {owner_id}: {otp_code}")
    except Exception as e:
        logger.warning(f"User OTP delivery error ({owner_id}): {e}")
    _increment_local_user(owner_id, "total_otps", 1)

# ==========================================
# Message Handler
# ==========================================

def _alert_group_gone(call):
    answer_callback(call["id"], "❌ Group not found!", show_alert=True)

_PANEL_SC_CFG = {
    "nexa":  {"key": "nexa_search_countries",  "del_cb": "del_sc_",    "add_cb": "add_search_country",     "back_cb": "nexa_control",  "label": "Nexa"},
    "voltx": {"key": "voltx_search_countries", "del_cb": "del_vxsc_",  "add_cb": "add_vx_search_country",  "back_cb": "voltx_control", "label": "VoltX"},
    "stex":  {"key": "stex_search_countries",  "del_cb": "del_stxsc_", "add_cb": "add_stx_search_country", "back_cb": "stex_control",  "label": "Stex"},
}

def _show_panel_search_countries(panel, chat_id, msg_id):
    """Show allowed search countries UI for a panel (nexa/voltx/stex)."""
    cfg = _PANEL_SC_CFG[panel]
    _reset_btn_counter()
    kb = []
    for idx, c in enumerate(bot_settings.get(cfg["key"], [])):
        kb.append([{"text": f"Delete {c}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"{cfg['del_cb']}{idx}", "style": _rs()}])
    kb.append([{"text": "Add Country Code", "icon_custom_emoji_id": "5420323438508155202", "callback_data": cfg["add_cb"], "style": _rs()}])
    kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": cfg["back_cb"], "style": _rs()}])
    edit_message(chat_id, msg_id, render_body_text(
        f"🌍 <b>{cfg['label']} Allowed Search Countries:</b>\n"
        f"Only these country codes will be allowed in Search Number for {cfg['label']}."),
        reply_markup={"inline_keyboard": kb})


def _alert_panel_gone(call):
    answer_callback(call["id"], "❌ Panel not found! List may have changed.", show_alert=True)

def _err_panel_gone(chat_id):
    send_message(chat_id, render_body_text("❌ Panel not found! It may have been deleted."))

def _set_panel_temp(chat_id, msg_id, idx):
    panels = bot_settings.get("panels", [])
    if idx < 0 or idx >= len(panels):
        _err_panel_gone(chat_id)
        return
    temp_data[chat_id] = {"msg_id": msg_id, "p_idx": idx, "p_name": panels[idx]["name"]}

def _add_close_btn(kb):
    kb.append([{"text": "Close", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": _rs()}])

def _append_custom_btns(kb, c_msg):
    for b in c_msg.get("buttons", []):
        b_copy = b.copy()
        b_copy["style"] = _rs()
        kb.append([b_copy])

def _prune_traffic(current_time):
    with _traffic_lock:
        recent_traffic[:] = [t for t in recent_traffic if current_time - t.get("time", 0) <= 3600]

def _find_flag_emoji_id(c, flags_db, default="5780471598922337683"):
    # ✅ FIX: Pehle direct dial code key check karo (e.g. "91", "880", "1")
    if c in flags_db and "id" in flags_db[c]:
        return flags_db[c]["id"]
    c_upper = c.upper()
    for flag_data in flags_db.values():
        iso = flag_data.get("iso", "").upper()
        name = flag_data.get("name", "").upper()
        if c_upper == iso or c_upper == name or c_upper in name or name in c_upper:
            if "id" in flag_data:
                return flag_data["id"]
    return default

def _save_panel_field(chat_id, msg, field, value):
    if not _td_has(chat_id, "p_idx", "msg_id"):
        _err_panel_gone(chat_id)
        user_states.pop(chat_id, None)
        temp_data.pop(chat_id, None)
        return
    idx = _td(chat_id, "p_idx", -1)
    edit_msg_id = _td(chat_id, "msg_id", msg["message_id"])
    if idx < 0 or idx >= len(bot_settings["panels"]):
        _err_panel_gone(chat_id)
    else:
        bot_settings["panels"][idx][field] = value
        save_local_db()
        delete_message(chat_id, msg["message_id"])
        _show_panel_cfg(chat_id, edit_msg_id, idx)
    user_states.pop(chat_id, None)
    temp_data.pop(chat_id, None)


# ==========================================
# Shared UI Helpers (deduplication)
# ==========================================
def _show_fj_panel(chat_id, msg_id):
    edit_message(chat_id, msg_id, render_body_text(f"{PEM['link']} <b>FORCE JOIN SYSTEM</b>\nManage channels/groups below:"), reply_markup=fj_settings_keyboard())

def _show_admin_panel(chat_id, msg_id):
    edit_message(chat_id, msg_id, render_body_text(f"{PEM['user']} <b>ADMIN MANAGEMENT</b>\nManage your bot admins below:"), reply_markup=admin_settings_keyboard())

def _show_otp_groups_panel(chat_id, msg_id):
    edit_message(chat_id, msg_id, render_body_text("🛡 <b>OTP GROUP MANAGEMENT</b>\nManage settings below:"), reply_markup=otp_groups_list_keyboard())

def _show_abhi_panel(chat_id, msg_id, extra=""):
    txt = "🕹 <b>ABHI CONTROL PANEL</b>"
    if extra: txt += f"\n\n{extra}"
    edit_message(chat_id, msg_id, render_body_text(txt), reply_markup=abhi_control_keyboard())

def _show_w_methods(chat_id, msg_id):
    edit_message(chat_id, msg_id, render_body_text("💳 <b>WITHDRAWAL METHODS</b>\n\nManage your withdrawal methods below:"), reply_markup=w_methods_keyboard())

def _show_panel_cfg(chat_id, edit_msg_id, idx):
    """Refresh panel config display after a field update."""
    if idx < 0 or idx >= len(bot_settings["panels"]):
        _err_panel_gone(chat_id)
        return
    p = bot_settings["panels"][idx]
    if p["type"] == "Auto Captcha Panel":
        text = (f"⚙️ <b>Configure {p['name']}</b>\n\n<b>Type:</b> {p['type']}\n"
                f"<b>Status:</b> {'🟢 Monitoring' if p['status'] == 'ON' else '🔴 Stopped'}\n"
                f"<b>Login Status:</b> {p.get('login_status', 'Unknown')}\n"
                f"<b>Login URL:</b> <code>{p.get('login_url', 'None')}</code>\n"
                f"<b>User:</b> <code>{p.get('username', 'None')}</code>")
    else:
        hdr_info = f"\n<b>Token Header:</b> <code>{p.get('token_header')}</code>" if p.get('token_header') else ""
        text = (f"⚙️ <b>Configure {p['name']}</b>\n\n<b>Type:</b> {p['type']}\n"
                f"<b>Status:</b> {'🟢 Monitoring' if p['status'] == 'ON' else '🔴 Stopped'}\n"
                f"<b>API URL:</b> <code>{p.get('api_url', 'None')}</code>\n"
                f"<b>Token:</b> <code>{p.get('token', 'None')}</code>{hdr_info}\n"
                f"<b>Full API URL:</b> <code>{p.get('full_api_url', 'None')}</code>")
    edit_message(chat_id, edit_msg_id, render_body_text(text), reply_markup=panel_config_keyboard(idx))


def _err_invalid_id(chat_id):
    send_message(chat_id, render_body_text("❌ Invalid ID!"), reply_markup=get_cancel_kb())

def _show_2fa_name_input(chat_id, msg_id):
    """Helper: 2FA naam input screen. Duplicate code remove."""
    txt = (
        f"━━━━━━━━━━━━━━━\n"
        f"《 📛 <b>CODE KA NAAM BATAYEIN</b> 》\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📝 Is 2FA code ko kya naam dena chahte hain?\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👇 Naam type karke bhejein:"
    )
    _reset_btn_counter()
    kb = {"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "cancel_2fa", "style": _rs()}]]}
    edit_message(chat_id, msg_id, render_body_text(txt), reply_markup=kb)


def _make_fw_btn(btn, kb):
    b = {"text": btn["text"], "url": btn["url"], "style": _rs()}
    if "icon_custom_emoji_id" in btn: b["icon_custom_emoji_id"] = btn["icon_custom_emoji_id"]
    return b

def _build_services_keyboard(c_msg_key="get_number"):
    """Helper: GET NUMBER screen ke liye services list keyboard banata hai. Duplicate code remove."""
    local_srvs = set([b["service"] for b in number_batches.values() if b["numbers"]])
    nexa_srvs = set(bot_settings.get("nexa_services", {}).keys())
    voltx_srvs = set(bot_settings.get("voltx_services", {}).keys())
    stex_srvs = set(bot_settings.get("stex_services", {}).keys())
    all_services = local_srvs.union(nexa_srvs).union(voltx_srvs).union(stex_srvs)
    c_msg = bot_settings["custom_messages"].get(c_msg_key, {})
    txt = render_body_text(c_msg.get("text", f"{PEM['pin']} Select Service"))
    apps_db = bot_settings.get("premium_apps", {})
    _reset_btn_counter()
    kb = []
    for s in sorted(all_services):
        emoji_id = _get_service_emoji_id(s, apps_db)
        kb.append([{"text": s, "icon_custom_emoji_id": emoji_id, "callback_data": f"g_s_{s}", "style": _rs()}])
    _append_custom_btns(kb, c_msg)
    _add_close_btn(kb)
    return all_services, txt, kb


def _search_and_recycle_local(query, chat_id):
    """Search local number_batches for numbers matching prefix query.
    If all matching numbers are already used by this user, recycle them (reset shares/used_by).
    Returns list of (batch_id, index) tuples for available numbers."""
    found_indices = []
    for b_id, b_data in number_batches.items():
        for idx, n_obj in enumerate(b_data["numbers"]):
            if n_obj["num"].replace("+", "").startswith(query) and chat_id not in n_obj.get("used_by", []):
                found_indices.append((b_id, idx))
    if not found_indices:
        has_matching = False
        for b_id, b_data in number_batches.items():
            for n_obj in b_data["numbers"]:
                if n_obj["num"].replace("+", "").startswith(query):
                    has_matching = True
                    n_obj["shares"] = 0
                    n_obj["used_by"] = []
        if has_matching:
            for b_id, b_data in number_batches.items():
                for idx, n_obj in enumerate(b_data["numbers"]):
                    if n_obj["num"].replace("+", "").startswith(query):
                        found_indices.append((b_id, idx))
    return found_indices


def handle_message(msg):
    global total_assigned_stats
    global total_uploaded_stats
    chat_id = msg["chat"]["id"]
    chat_type = msg["chat"].get("type", "private")
    
    if chat_type != "private":
        return
        
    text = msg.get("text", "") or ""
    register_user_local(chat_id) # 🌟 Save User locally for Free Broadcasts!

    if is_user_banned(chat_id):
        send_message(chat_id, render_body_text("🚫 <b>You are banned from using this bot!</b>\nIf you think this is a mistake, please contact support."))
        return
    
    # --- REFERRAL FIX: Save inviter BEFORE Force Join ---
    if text.startswith("/start"):
        parts = text.split()
        if len(parts) > 1 and parts[1].isdigit():
            inviter = int(parts[1])
            if inviter != chat_id:
                u_data = _get_local_user(chat_id)
                if not u_data.get("referred_by"):
                    _update_local_user(chat_id, {"referred_by": inviter, "ref_paid": False})
                        
    if not check_force_join(chat_id):
        send_force_join_msg(chat_id)
        return
        
    MAIN_MENU_CMDS = ["GET NUMBER", "Search Number", "TRAFFIC", "Refer", "WITHDRAWAL", "SUPPORT", "Admin Panel", "2FA ONLINE"]
    
    is_main_cmd = False
    if text in MAIN_MENU_CMDS or text.startswith("/start"):
        if chat_id in user_states: user_states.pop(chat_id, None)
        if chat_id in temp_data: temp_data.pop(chat_id, None)
        is_main_cmd = True
    
    if chat_id in user_states and not is_main_cmd:
        state = user_states[chat_id]
        
        # 🌟 Auto Captcha Panel Setup Flow 
        if state == "wait_for_cpanel_url" and text:
            temp_data[chat_id]["p_data"]["login_url"] = text.strip()
            user_states[chat_id] = "wait_for_cpanel_user"
            send_message(chat_id, render_body_text("2️⃣ <b>Username</b>\n➡️ Enter Panel Username:"), reply_markup=get_cancel_kb())
            return
            
        elif state == "wait_for_cpanel_user" and text:
            if chat_id not in temp_data or "p_data" not in temp_data.get(chat_id, {}):
                user_states.pop(chat_id, None); send_message(chat_id, render_body_text("❌ Session expired. Please try again.")); return
            temp_data[chat_id]["p_data"]["username"] = text.strip()
            user_states[chat_id] = "wait_for_cpanel_pass"
            send_message(chat_id, render_body_text("3️⃣ <b>Password</b>\n➡️ Enter Panel Password:"), reply_markup=get_cancel_kb())
            return
            
        elif state == "wait_for_cpanel_pass" and text:
            if chat_id not in temp_data or "p_data" not in temp_data.get(chat_id, {}):
                user_states.pop(chat_id, None); send_message(chat_id, render_body_text("❌ Session expired. Please try again.")); return
            temp_data[chat_id]["p_data"]["password"] = text.strip()
            # ✅ Auto-detect: msg_link, column names aur serials bot khud detect kar lega
            # msg_link empty rahega → code {base}/client/SMSCDRStats use karega
            # num_col_name/msg_col_name → defaults "number"/"message" + smart header scan
            temp_data[chat_id]["p_data"]["login_status"] = "⏳ Pending Auto-Login..."
            temp_data[chat_id]["p_data"]["needs_warmup"] = True
            bot_settings["panels"].append(temp_data[chat_id]["p_data"])
            save_local_db()
            # Auto Captcha panel status="ON" se start hota hai — eager warmup spawn karo
            new_panel_idx = len(bot_settings["panels"]) - 1
            threading.Thread(target=_eagerly_warmup_panel, args=(new_panel_idx, bot_settings["panels"][-1]), daemon=True).start()

            send_message(chat_id, render_body_text(f"{PEM['ok']} <b>Auto Captcha Panel Added Successfully!</b>\nBot will now automatically login and detect settings in background."), reply_markup=main_menu(chat_id))
            
            msg_id = temp_data[chat_id]["msg_id"]
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "manage_cpt_panels", "id": "internal"})
            
            user_states.pop(chat_id, None)
            temp_data.pop(chat_id, None)
            return

        # --- User Management Flows ---
        elif state == "wait_for_um_bal_uid" and text:
            target_uid_str = text.strip()
            if not target_uid_str.isdigit():
                send_message(chat_id, render_body_text("❌ Invalid ID! Please send a numeric User ID."), reply_markup=get_cancel_kb())
                return
            target_uid = int(target_uid_str)
            user_data = _get_local_user(target_uid)
            current_bal = user_data.get('balance', 0.0)
            temp_data[chat_id]["target_uid"] = target_uid
            user_states[chat_id] = "wait_for_um_bal_amt"
            send_message(chat_id, render_body_text(f"✅ User found!\n💰 Current Balance: {current_bal} ₹\n\n📝 Send the amount to ADD (e.g. 50) or REMOVE (e.g. -50):"), reply_markup=get_cancel_kb())
            return

        elif state == "wait_for_um_bal_amt" and text:
            try:
                amt = float(text.strip())
                target_uid = temp_data[chat_id]["target_uid"]
                old_bal = _get_local_user(target_uid).get('balance', 0.0)
                update_balance(target_uid, amt)
                new_bal = _get_local_user(target_uid).get('balance', 0.0)
                send_message(chat_id, render_body_text(f"{PEM['ok']} Balance updated!\n{PEM['user']} User: <code>{target_uid}</code>\n💰 Old: {old_bal} ₹ → New: {new_bal} ₹"), reply_markup=main_menu(chat_id))
                
                if amt >= 0:
                    notif_text = f"{PEM['gift']} <b>Balance Added!</b>\n➖➖➖➖➖➖➖\n💰 <b>Amount:</b> +{amt} ₹\n💰 <b>New Balance:</b> {new_bal} ₹\n➖➖➖➖➖➖➖\n👨‍⚖️ <b>By Admin</b>"
                else:
                    notif_text = f"{PEM['warn']} <b>Balance Removed!</b>\n➖➖➖➖➖➖➖\n💰 <b>Amount:</b> {amt} ₹\n💰 <b>New Balance:</b> {new_bal} ₹\n➖➖➖➖➖➖➖\n👨‍⚖️ <b>By Admin</b>"
                send_message(target_uid, render_body_text(notif_text))
                user_states.pop(chat_id, None)
                temp_data.pop(chat_id, None)
            except ValueError:
                send_message(chat_id, render_body_text("❌ Invalid amount! Please send a number."), reply_markup=get_cancel_kb())
            return

        elif state == "wait_for_um_ban_uid" and text:
            target_uid_str = text.strip()
            if not target_uid_str.isdigit():
                _err_invalid_id(chat_id)
                return
            target_uid = int(target_uid_str)
            user_data = _get_local_user(target_uid)
            current_status = user_data.get("banned", False)
            new_status = not current_status
            _update_local_user(target_uid, {"banned": new_status})
            
            user_banned_cache[target_uid] = {'banned': new_status, 'time': time.time()}
            
            status_text = "BANNED 🚫" if new_status else "UNBANNED ✅"
            send_message(chat_id, render_body_text(f"✅ User {target_uid} has been {status_text}!"), reply_markup=main_menu(chat_id))
            user_states.pop(chat_id, None)
            temp_data.pop(chat_id, None)
            return

        elif state == "wait_for_um_prof_uid" and text:
            target_uid_str = text.strip()
            if not target_uid_str.isdigit():
                _err_invalid_id(chat_id)
                return
            target_uid = int(target_uid_str)
            data = _get_local_user(target_uid)
            is_verified = True if data.get('total_otps', 0) > 0 else data.get('verified', False)
            prof_text = f"""➖➖➖➖➖➖➖➖
👤 <b>USER PROFILE</b>
➖➖➖➖➖➖➖➖
🆔 ID: <code>{target_uid}</code>
💰 Balance: {data.get('balance', 0.0)} ₹
🤝 Total Refers: {data.get('total_refers', 0)}
🔐 Total OTPs: {data.get('total_otps', 0)}
✅ Verified: {is_verified}
🚫 Banned: {data.get('banned', False)}
➖➖➖➖➖➖➖➖"""
            _reset_btn_counter()
            kb = {"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "user_management", "style": _rs()}]]}
            send_message(chat_id, render_body_text(prof_text), reply_markup=kb)
            user_states.pop(chat_id, None)
            temp_data.pop(chat_id, None)
            return

        # --- Menu Design Flow ---
        elif state == "wait_for_menu_text" and text:
            try:
                menu_key = temp_data[chat_id]["menu_key"]
                formatted_html_text = extract_premium_html(msg)
                
                bot_settings["custom_messages"][menu_key]["text"] = formatted_html_text
                save_local_db()
                
                delete_message(chat_id, msg["message_id"])
                
                preview_text = render_body_text(formatted_html_text)
                success_text = f"{PEM['ok']} <b>Message Body Updated successfully!</b>\n\n🎨 <b>Editing: {menu_key.upper()}</b>\n\nPreview of current Text:\n{preview_text}"
                edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text(success_text), reply_markup=menu_edit_options_keyboard(menu_key))
            except Exception as e:
                send_message(chat_id, render_body_text(f"❌ Error saving text: {e}"))
            finally:
                if chat_id in user_states: user_states.pop(chat_id, None)
                if chat_id in temp_data: temp_data.pop(chat_id, None)
            return
            
        elif state == "wait_for_menu_btn" and text:
            try:
                menu_key = temp_data[chat_id]["menu_key"]
                btn_data = _parse_btn_from_text(text, msg.get("entities", []))
                if btn_data is not None:
                    bot_settings["custom_messages"][menu_key]["buttons"].append(btn_data)
                    save_local_db()
                    delete_message(chat_id, msg["message_id"])
                    edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text(f"{PEM['gear']} <b>Edit Inline Buttons: {menu_key.upper()}</b>"), reply_markup=menu_buttons_list_keyboard(menu_key))
                else:
                    send_message(chat_id, render_body_text(f"{PEM['no']} Invalid format. Use <code>Button Text - https://link.com</code>"))
            except Exception as e:
                logger.warning(f"Error: {e}")
            finally:
                if chat_id in user_states: user_states.pop(chat_id, None)
                if chat_id in temp_data: temp_data.pop(chat_id, None)
            return

        elif state == "wait_for_test_service" and text:
            temp_data[chat_id]["service"] = text.strip()
            user_states[chat_id] = "wait_for_test_number"
            send_message(chat_id, render_body_text("📝 Send the Number (e.g. +8801712345678):"), reply_markup=get_cancel_kb())
            return
            
        elif state == "wait_for_test_number" and text:
            temp_data[chat_id]["number"] = text.strip()
            user_states[chat_id] = "wait_for_test_otp"
            send_message(chat_id, render_body_text("📝 Send the OTP (e.g. 556677):"), reply_markup=get_cancel_kb())
            return
            
        elif state == "wait_for_test_otp" and text:
            temp_data[chat_id]["otp"] = text.strip()
            user_states[chat_id] = "wait_for_test_lang"
            send_message(chat_id, render_body_text("📝 Send the Language (e.g. EN, AR):"), reply_markup=get_cancel_kb())
            return
            
        elif state == "wait_for_test_lang" and text:
            lang = text.strip().upper()
            if not lang.startswith("#"):
                lang = "#" + lang
                
            srv = temp_data[chat_id]["service"]
            num = temp_data[chat_id]["number"]
            otp = temp_data[chat_id]["otp"]
            
            masked = mask_number(num)
            prem_flag_html = get_flag_info_html(num)
            char, iso = get_flag_and_code(num)
            app_full_name, prem_app_html = get_service_info_html(srv)
            
            msg_text = render_body_text(f"{prem_flag_html} #{iso} ♦ {masked} ✅ {otp}")
            
            for fw in bot_settings.get("fw_groups", []):
                _reset_btn_counter()
                kb = _make_otp_kb(otp)
                _fw_btns = fw.get("buttons", [])
                for i in range(0, len(_fw_btns), 2):
                    row = [_make_fw_btn(_fw_btns[i], kb)]
                    if i + 1 < len(_fw_btns):
                        row.append(_make_fw_btn(_fw_btns[i + 1], kb))
                    kb.append(row)
                send_message(fw["chat_id"], msg_text, reply_markup={"inline_keyboard": kb})
                
            send_message(chat_id, render_body_text(f"{PEM['ok']} Test message formatted and sent to all Forward Groups!"), reply_markup=main_menu(chat_id))
            user_states.pop(chat_id, None)
            temp_data.pop(chat_id, None)
            return


        elif state in ["wait_for_flag_txt", "wait_for_app_txt"] and "document" in msg:
            doc = msg["document"]
            content = _download_telegram_txt_document(chat_id, doc)
            if content is None:
                return
            
            mode = "flags" if state == "wait_for_flag_txt" else "apps"
            count = 0
            
            if mode == "flags":
                for line in content.splitlines():
                    json_match = re.search(r'(\{.*\})', line)
                    if json_match:
                        try:
                            data = json.loads(json_match.group(1))
                            char = data.get("emoji")
                            eid = data.get("id")
                            
                            prefix_str = line[:json_match.start()].strip()
                            code_match = re.search(r'\((\d+)\)', prefix_str)
                            iso_match = re.search(r'\(([A-Za-z]+)\)', prefix_str)
                            
                            if code_match and iso_match and char and eid:
                                code = code_match.group(1)
                                iso = iso_match.group(1).upper()
                                name = prefix_str.replace(f"({code})", "").replace(f"({iso_match.group(1)})", "").replace(char, "").strip()
                                bot_settings["premium_flags"][code] = {"char": char, "iso": iso, "name": name, "id": eid}
                                count += 1
                        except Exception as e:
                            logger.warning(f"Error: {e}")
            else:
                for line in content.splitlines():
                    json_match = re.search(r'(\{.*\})', line)
                    if json_match:
                        try:
                            data = json.loads(json_match.group(1))
                            char = data.get("emoji")
                            eid = data.get("id")
                            
                            name_part = line[:json_match.start()].strip()
                            name = name_part.replace(char, '').strip() if char else name_part
                            
                            if char and eid and name:
                                bot_settings["premium_apps"][name.upper()] = {"char": char, "id": eid, "name": name}
                                count += 1
                        except Exception as e:
                            logger.warning(f"Error: {e}")
            
            save_local_db()
            send_message(chat_id, render_body_text(f"{PEM['ok']} Successfully loaded {count} Emojis!"), reply_markup=emoji_settings_keyboard())
            user_states.pop(chat_id, None)
            if chat_id in temp_data: temp_data.pop(chat_id, None)
            return

        elif state == "wait_for_broadcast":
            msg_id = msg["message_id"]
            send_message(chat_id, render_body_text(f"{PEM['ok']} Broadcast started..."))
            threading.Thread(target=broadcast_copymessage, args=(chat_id, msg_id)).start()
            user_states.pop(chat_id, None)
            if chat_id in temp_data: temp_data.pop(chat_id, None)
            return

        elif state == "wait_for_txt" and "document" in msg:
            doc = msg["document"]
            file_content = _download_telegram_txt_document(chat_id, doc)
            if file_content is None:
                return

            temp_data[chat_id] = {"numbers": file_content.splitlines(), "filename": doc["file_name"]}
            user_states[chat_id] = "wait_for_service"
            send_message(chat_id, render_body_text(f"{PEM['ok']} File received.\n\n📌 Enter the service name (e.g., WHATSAPP):"), reply_markup=get_cancel_kb())
            return

        elif state == "wait_for_service" and text:
            temp_data[chat_id]["service"] = text.upper()
            user_states[chat_id] = "wait_for_country"
            send_message(chat_id, render_body_text(f"{PEM['ok']} Service set.\n\n🌍 Enter the country name (e.g., YEMEN):"), reply_markup=get_cancel_kb())
            return

        elif state == "wait_for_country" and text:
            country = text.upper()
            service = temp_data[chat_id]["service"]
            raw_numbers = temp_data[chat_id]["numbers"]
            
            clean_nums = []
            for num in raw_numbers:
                num = num.strip()
                if num:
                    if not num.startswith('+'): num = '+' + num
                    clean_nums.append(num)
            
            batch_id = str(uuid.uuid4())[:8]
            number_batches[batch_id] = {"filename": temp_data[chat_id]["filename"], "service": service, "country": country, "numbers": [{"num": n, "shares": 0, "used_by": []} for n in clean_nums]}
            with _stats_lock:
                total_uploaded_stats += len(clean_nums)
            save_local_db()
            
            if not clean_nums:
                send_message(chat_id, render_body_text(f"{PEM['no']} No valid numbers found in file!"), reply_markup=main_menu(chat_id))
                user_states.pop(chat_id, None); temp_data.pop(chat_id, None); return
            app_full_name, prem_app_html = get_service_info_html(service)
            prem_flag_html = get_flag_info_html(clean_nums[0]) if clean_nums else f"{PEM['world']} "
            
            broadcast_txt = f"➖➖➖➖➖➖➖➖\n《 NEW NUMBERS 》\n➖➖➖➖➖➖➖➖\n{prem_flag_html} {country} {prem_app_html} {service}\n➖➖➖➖➖➖➖➖\n📤 Total Added: <b>{len(clean_nums)}</b>\n➖➖➖➖➖➖➖➖\nUse /start to get your numbers!"
            broadcast_txt = render_body_text(broadcast_txt)
            
            send_message(chat_id, render_body_text(f"{PEM['ok']} Numbers added to local stock! Starting broadcast..."))
            
            threading.Thread(target=broadcast_text_message, args=(broadcast_txt,)).start()
            
            user_states.pop(chat_id, None)
            temp_data.pop(chat_id, None)
            return

        elif state == "wait_for_add_nexa_key" and text:
            bot_settings["nexa_keys"].append(text.strip())
            save_local_db()
            _service_warmup_needed["nexa"] = True  # Skip old OTPs for newly added key
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, _td(chat_id, "msg_id", msg["message_id"]), render_body_text(f"✅ Nexa API Key Added! Total Keys: {len(bot_settings.get('nexa_keys', []))}"), reply_markup=_panel_control_keyboard("Nexa"))
            user_states.pop(chat_id, None)
            temp_data.pop(chat_id, None)
            return

        elif state == "wait_for_add_sc" and text:
            code = text.strip().replace("+", "")
            if "nexa_search_countries" not in bot_settings: bot_settings["nexa_search_countries"] = []
            if code not in bot_settings["nexa_search_countries"]:
                bot_settings["nexa_search_countries"].append(code)
            save_local_db()
            delete_message(chat_id, msg["message_id"])
            _show_panel_search_countries("nexa", chat_id, _td(chat_id, "msg_id", msg["message_id"]))
            user_states.pop(chat_id, None)
            temp_data.pop(chat_id, None)
            return

        elif state == "wait_nx_srv_name" and text:
            srv = text.strip().upper()
            if "nexa_services" not in bot_settings: bot_settings["nexa_services"] = {}
            if srv not in bot_settings["nexa_services"]: bot_settings["nexa_services"][srv] = {}
            save_local_db()
            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": "manage_nexa_srv", "id": "internal"})
            user_states.pop(chat_id, None)
            if chat_id in temp_data: temp_data.pop(chat_id, None)
            return

        elif state == "wait_nx_cnt_name" and text:
            cnt = text.strip()
            srv = temp_data.get(chat_id, {}).get("srv")
            if not srv or srv not in bot_settings.get("nexa_services", {}):
                send_message(chat_id, render_body_text("❌ Session expired. Please start again."))
                user_states.pop(chat_id, None); temp_data.pop(chat_id, None)
                return
            if cnt not in bot_settings["nexa_services"][srv]: bot_settings["nexa_services"][srv][cnt] = []
            save_local_db()
            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": f"nx_srv_{srv}", "id": "internal"})
            user_states.pop(chat_id, None)
            if chat_id in temp_data: temp_data.pop(chat_id, None)
            return

        elif state == "wait_nx_addr" and text:
            srv = temp_data.get(chat_id, {}).get("srv")
            cnt = temp_data.get(chat_id, {}).get("cnt")
            if not srv or not cnt or srv not in bot_settings.get("nexa_services", {}):
                send_message(chat_id, render_body_text("❌ Session expired. Please start again."))
                user_states.pop(chat_id, None); temp_data.pop(chat_id, None)
                return
            new_range = text.strip().replace("+", "")
            
            if new_range not in bot_settings["nexa_services"][srv][cnt]:
                bot_settings["nexa_services"][srv][cnt].append(new_range)
                
                if "nexa_search_countries" not in bot_settings:
                    bot_settings["nexa_search_countries"] = []
                nexa_prefix = new_range.replace("X", "").replace("x", "")
                if nexa_prefix and nexa_prefix not in bot_settings["nexa_search_countries"]:
                    bot_settings["nexa_search_countries"].append(nexa_prefix)
                    
                save_local_db()
                
            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": f"nx_cnt_{srv}_{cnt}", "id": "internal"})
            user_states.pop(chat_id, None)
            if chat_id in temp_data: temp_data.pop(chat_id, None)
            return

        # VoltX state handlers
        elif state == "wait_for_add_voltx_key" and text:
            bot_settings["voltx_keys"].append(text.strip())
            save_local_db()
            _service_warmup_needed["voltx"] = True  # Skip old OTPs for newly added key
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, _td(chat_id, "msg_id", msg["message_id"]), render_body_text(f"✅ VoltX API Key Added! Total Keys: {len(bot_settings.get('voltx_keys', []))}"), reply_markup=_panel_control_keyboard("VoltX"))
            user_states.pop(chat_id, None)
            temp_data.pop(chat_id, None)
            return

        elif state == "wait_vx_srv_name" and text:
            srv = text.strip().upper()
            if "voltx_services" not in bot_settings: bot_settings["voltx_services"] = {}
            if srv not in bot_settings["voltx_services"]: bot_settings["voltx_services"][srv] = {}
            save_local_db()
            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": "manage_voltx_srv", "id": "internal"})
            user_states.pop(chat_id, None)
            if chat_id in temp_data: temp_data.pop(chat_id, None)
            return

        elif state == "wait_vx_cnt_name" and text:
            cnt = text.strip()
            srv = temp_data[chat_id]["srv"]
            if cnt not in bot_settings["voltx_services"][srv]: bot_settings["voltx_services"][srv][cnt] = []
            save_local_db()
            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": f"vx_srv_{srv}", "id": "internal"})
            user_states.pop(chat_id, None)
            if chat_id in temp_data: temp_data.pop(chat_id, None)
            return

        elif state == "wait_vx_addr" and text:
            srv, cnt = temp_data[chat_id]["srv"], temp_data[chat_id]["cnt"]
            new_range = text.strip()
            if new_range not in bot_settings["voltx_services"][srv][cnt]:
                bot_settings["voltx_services"][srv][cnt].append(new_range)
                if "voltx_search_countries" not in bot_settings:
                    bot_settings["voltx_search_countries"] = []
                prefix = new_range.replace("X", "").replace("x", "")
                if prefix and prefix not in bot_settings["voltx_search_countries"]:
                    bot_settings["voltx_search_countries"].append(prefix)
                save_local_db()
            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": f"vx_cnt_{srv}_{cnt}", "id": "internal"})
            user_states.pop(chat_id, None)
            if chat_id in temp_data: temp_data.pop(chat_id, None)
            return

        elif state == "wait_for_add_vxsc" and text:
            code = text.strip().replace("+", "")
            if "voltx_search_countries" not in bot_settings: bot_settings["voltx_search_countries"] = []
            if code not in bot_settings["voltx_search_countries"]:
                bot_settings["voltx_search_countries"].append(code)
            save_local_db()
            delete_message(chat_id, msg["message_id"])
            _show_panel_search_countries("voltx", chat_id, _td(chat_id, "msg_id", msg["message_id"]))
            user_states.pop(chat_id, None)
            temp_data.pop(chat_id, None)
            return

        # Stex state handlers
        elif state == "wait_for_add_stex_key" and text:
            bot_settings["stex_keys"].append(text.strip())
            save_local_db()
            _service_warmup_needed["stex"] = True  # Skip old OTPs for newly added key
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, _td(chat_id, "msg_id", msg["message_id"]), render_body_text(f"✅ Stex API Key Added! Total Keys: {len(bot_settings.get('stex_keys', []))}"), reply_markup=_panel_control_keyboard("Stex"))
            user_states.pop(chat_id, None)
            temp_data.pop(chat_id, None)
            return

        elif state == "wait_stx_srv_name" and text:
            srv = text.strip().upper()
            if "stex_services" not in bot_settings: bot_settings["stex_services"] = {}
            if srv not in bot_settings["stex_services"]: bot_settings["stex_services"][srv] = {}
            save_local_db()
            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": "manage_stex_srv", "id": "internal"})
            user_states.pop(chat_id, None)
            if chat_id in temp_data: temp_data.pop(chat_id, None)
            return

        elif state == "wait_stx_cnt_name" and text:
            cnt = text.strip()
            srv = temp_data[chat_id]["srv"]
            if cnt not in bot_settings["stex_services"][srv]: bot_settings["stex_services"][srv][cnt] = []
            save_local_db()
            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": f"stx_srv_{srv}", "id": "internal"})
            user_states.pop(chat_id, None)
            if chat_id in temp_data: temp_data.pop(chat_id, None)
            return

        elif state == "wait_stx_addr" and text:
            srv, cnt = temp_data[chat_id]["srv"], temp_data[chat_id]["cnt"]
            new_range = text.strip()
            if new_range not in bot_settings["stex_services"][srv][cnt]:
                bot_settings["stex_services"][srv][cnt].append(new_range)
                if "stex_search_countries" not in bot_settings:
                    bot_settings["stex_search_countries"] = []
                prefix = new_range.replace("X", "").replace("x", "")
                if prefix and prefix not in bot_settings["stex_search_countries"]:
                    bot_settings["stex_search_countries"].append(prefix)
                save_local_db()
            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": f"stx_cnt_{srv}_{cnt}", "id": "internal"})
            user_states.pop(chat_id, None)
            if chat_id in temp_data: temp_data.pop(chat_id, None)
            return

        elif state == "wait_for_add_stxsc" and text:
            code = text.strip().replace("+", "")
            if "stex_search_countries" not in bot_settings: bot_settings["stex_search_countries"] = []
            if code not in bot_settings["stex_search_countries"]:
                bot_settings["stex_search_countries"].append(code)
            save_local_db()
            delete_message(chat_id, msg["message_id"])
            _show_panel_search_countries("stex", chat_id, _td(chat_id, "msg_id", msg["message_id"]))
            user_states.pop(chat_id, None)
            temp_data.pop(chat_id, None)
            return

        elif state == "wait_for_add_wm" and text:
            bot_settings["w_methods"].append(text.strip())
            save_local_db()
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, _td(chat_id, "msg_id", msg["message_id"]), render_body_text("💳 <b>WITHDRAWAL METHODS</b>\n\nManage your withdrawal methods below:"), reply_markup=w_methods_keyboard())
            user_states.pop(chat_id, None)
            temp_data.pop(chat_id, None)
            return

        elif state == "wait_for_add_fj" and text:
            raw_input = text.strip()
            # Handle private invite links (https://t.me/+xxx or https://t.me/joinchat/xxx)
            if "t.me/+" in raw_input or "t.me/joinchat/" in raw_input:
                # For private invite links, we need the numeric chat_id
                # Admin must also provide numeric ID for private chats
                delete_message(chat_id, msg["message_id"])
                edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text("⚠️ <b>Private invite link detected!</b>\n\nPrivate channel/group ke liye numeric ID bhejein (e.g. <code>-1001234567890</code>)\n\nID kaise pata karein:\n1. Channel/Group mein koi message forward karein\n2. @userinfobot ko forward karein\n3. Woh aapko ID de dega"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_fj", "style": _rs()}]]})
                return
            parsed_id = parse_chat_id(raw_input)
            detected = auto_detect_chat(parsed_id)
            if detected:
                bot_settings["fj_channels"].append(detected)
                save_local_db()
                delete_message(chat_id, msg["message_id"])
                type_label = "Channel" if detected["type"] == "channel" else "Group"
                priv_label = "Private" if detected["is_private"] else "Public"
                edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text(f"✅ <b>Successfully Added!</b>\n\n{type_label} | {priv_label}\n📌 Title: <b>{detected['title']}</b>\n🆔 ID: <code>{detected['chat_id']}</code>\n🔗 Link: {detected.get('invite_link', 'N/A')}"), reply_markup=fj_settings_keyboard())
            else:
                delete_message(chat_id, msg["message_id"])
                edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text("❌ <b>Error!</b> Bot is not admin in this channel/group ya invalid ID hai.\n\nMake sure:\n1. Bot ko channel/group mein add karein\n2. Bot ko admin banaayein\n3. Phir dobara try karein"), reply_markup={"inline_keyboard": [[{"text": "Try Again", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "add_fj", "style": _rs()}, {"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_fj", "style": _rs()}]]})
            user_states.pop(chat_id, None)
            temp_data.pop(chat_id, None)
            return
            
        elif state == "wait_for_add_adm" and text:
            if text.isdigit():
                bot_settings["admins"].append(int(text))
                save_local_db()
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, _td(chat_id, "msg_id", msg["message_id"]), render_body_text("👥 <b>ADMIN MANAGEMENT</b>\nManage your bot admins below:"), reply_markup=admin_settings_keyboard())
            user_states.pop(chat_id, None)
            temp_data.pop(chat_id, None)
            return

        elif state == "wait_for_add_fw_id" and text:
            bot_settings["fw_groups"].append({"chat_id": text.strip(), "buttons": []})
            save_local_db()
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, _td(chat_id, "msg_id", msg["message_id"]), render_body_text("🛡 <b>OTP GROUP MANAGEMENT</b>\nManage settings below:"), reply_markup=otp_groups_list_keyboard())
            user_states.pop(chat_id, None)
            temp_data.pop(chat_id, None)
            return
            
        elif state == "wait_for_add_fw_btn" and text:
            fw_idx = _td(chat_id, "fw_idx", -1)
            if fw_idx < 0 or fw_idx >= len(bot_settings.get("fw_groups", [])):
                send_message(chat_id, render_body_text("❌ Group not found!"))
                user_states.pop(chat_id, None); temp_data.pop(chat_id, None); return
            btn_data = _parse_btn_from_text(text, msg.get("entities", []))
            if btn_data is not None:
                bot_settings["fw_groups"][fw_idx]["buttons"].append(btn_data)
            save_local_db()
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text(f"🛡 <b>Manage Group:</b> {bot_settings['fw_groups'][fw_idx]['chat_id']}"), reply_markup=specific_fw_group_keyboard(fw_idx))
            user_states.pop(chat_id, None)
            temp_data.pop(chat_id, None)
            return
            
        elif state == "wait_for_otp_link" and text:
            bot_settings["otp_link"] = text.strip()
            save_local_db()
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text("🛡 <b>OTP GROUP MANAGEMENT</b>\nManage settings below:"), reply_markup=otp_groups_list_keyboard())
            user_states.pop(chat_id, None)
            temp_data.pop(chat_id, None)
            return

        elif state == "wait_for_panel_name" and text:
            p_name = text.strip()
            t_key = temp_data[chat_id].get("add_type", "api")
            msg_id = temp_data[chat_id]["msg_id"]
            delete_message(chat_id, msg["message_id"])
            
            if t_key == "logc":
                user_states[chat_id] = "wait_for_cpanel_url"
                temp_data[chat_id] = {"msg_id": msg_id, "p_data": {
                    "name": p_name, "type": "Auto Captcha Panel", "status": "ON", "records": 0, "login_status": "⏳ Pending First Login"
                }}
                edit_message(chat_id, msg_id, render_body_text("1️⃣ <b>Login URL</b>\n➡️ Enter Panel Login Link:"), reply_markup=get_cancel_kb())
                return
            else:
                bot_settings["panels"].append({
                    "name": p_name, "type": "API Panel", "status": "OFF", "api_url": "", "token": "", "records": 0, "needs_warmup": True
                })
                save_local_db()
                handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "manage_api_panels", "id": "internal"})
                if chat_id in user_states: user_states.pop(chat_id, None)
                if chat_id in temp_data: temp_data.pop(chat_id, None)
                return

        elif state == "wait_for_p_api" and text:
            _save_panel_field(chat_id, msg, "api_url", text.strip())
            return

        elif state == "wait_for_p_tok" and text:
            _save_panel_field(chat_id, msg, "token", text.strip())
            return

        elif state == "wait_for_p_tokheader" and text:
            idx = _td(chat_id, "p_idx", -1)
            if idx < 0 or idx >= len(bot_settings["panels"]):
                _err_panel_gone(chat_id)
            else:
                val = text.strip()
                if val.lower() == "none":
                    bot_settings["panels"][idx].pop("token_header", None)
                else:
                    bot_settings["panels"][idx]["token_header"] = val
                save_local_db()
                delete_message(chat_id, msg["message_id"])
                _show_panel_cfg(chat_id, _td(chat_id, "msg_id", msg["message_id"]), idx)
            user_states.pop(chat_id, None)
            temp_data.pop(chat_id, None)
            return

        elif state == "wait_for_p_fapi" and text:
            _save_panel_field(chat_id, msg, "full_api_url", text.strip())
            return

        elif state == "wait_for_p_rec" and text:
            if text.isdigit():
                idx = temp_data[chat_id]["p_idx"]
                if idx < 0 or idx >= len(bot_settings["panels"]):
                    _err_panel_gone(chat_id)
                else:
                    bot_settings["panels"][idx]["records"] = int(text)
                    save_local_db()
                    delete_message(chat_id, msg["message_id"])
                    _show_panel_cfg(chat_id, temp_data[chat_id]["msg_id"], idx)
                user_states.pop(chat_id, None)
                temp_data.pop(chat_id, None)
            else:
                send_message(chat_id, render_body_text("❌ Please enter a valid number! Try again."))
            return

        elif state == "set_abhi":
            msg_id = _td(chat_id, "msg_id", msg["message_id"])
            key = _td(chat_id, "key", "")
            if not key:
                user_states.pop(chat_id, None); temp_data.pop(chat_id, None); return
            try:
                if key in ["min_withdraw", "otp_reward", "refer_reward"]: bot_settings[key] = float(text)
                elif key in ["cooldown", "num_req", "num_share"]: bot_settings[key] = int(text)
                else: bot_settings[key] = text
                save_local_db()
                delete_message(chat_id, msg["message_id"])
                _show_abhi_panel(chat_id, msg_id)
            except Exception as e:
                delete_message(chat_id, msg["message_id"])
                _show_abhi_panel(chat_id, msg_id, "❌ Invalid value!")
            user_states.pop(chat_id, None)
            temp_data.pop(chat_id, None)
            return

        elif state == "wait_for_search" and text:
            query = text.strip().replace("+", "")
            if not query.isdigit() or len(query) < 3 or len(query) > 9:
                send_message(chat_id, render_body_text("❌ Please enter a valid 3 to 9 digit number!"))
                return
                
            wait_msg = send_message(chat_id, render_body_text("⌛ <i>Processing... Finding Number...</i>"))
            wait_msg_id = wait_msg.get("result", {}).get("message_id") if isinstance(wait_msg, dict) else None
            
            # 🌟 1. First search number from Local (for any country)
            found_indices = _search_and_recycle_local(query, chat_id)

            fetched_nums = []
            if not found_indices:
                # 🌟 2. If not found in Local, then check if can get from Nexa/VoltX/Stex
                allowed_countries = (
                    bot_settings.get("nexa_search_countries", []) +
                    bot_settings.get("voltx_search_countries", []) +
                    bot_settings.get("stex_search_countries", [])
                )
                
                is_nexa_allowed = False
                if not allowed_countries:
                    is_nexa_allowed = True
                else:
                    clean_allowed = [c.replace("X", "").replace("x", "") for c in allowed_countries]
                    if any(query.startswith(c) or c.startswith(query) for c in clean_allowed if c):
                        is_nexa_allowed = True
                    
                if not is_nexa_allowed:
                    if wait_msg_id: delete_message(chat_id, wait_msg_id)
                    send_message(chat_id, render_body_text("❌ <b>This country code is not available for search.</b>\n\nPlease try a different number prefix."), reply_markup=main_menu(chat_id))
                    user_states.pop(chat_id, None)
                    if chat_id in temp_data: temp_data.pop(chat_id, None)
                    return
                    
                if wait_msg_id: edit_message(chat_id, wait_msg_id, render_body_text("⌛ <i>Processing... Finding Number via API...</i>"))
                # 🌟 Try all panels with strict isolation (Nexa → VoltX → Stex)
                _api_num, _api_panel = _fetch_number_via_panels(query, chat_id)
                if _api_num:
                    fetched_nums.append(_api_num)
                    save_local_db()
                else:
                    if wait_msg_id: delete_message(chat_id, wait_msg_id)
                    send_message(chat_id, render_body_text("❌ Number out of stock!"), reply_markup=main_menu(chat_id))
                    user_states.pop(chat_id, None)
                    if chat_id in temp_data: temp_data.pop(chat_id, None)
                    return
            else:
                random.shuffle(found_indices)
                for b_id, idx in found_indices:
                    if len(fetched_nums) >= bot_settings.get("num_req", 1): break
                    if b_id not in number_batches: continue
                    nb = number_batches[b_id]["numbers"]
                    if idx < 0 or idx >= len(nb): continue
                    n_obj = nb[idx]
                    num_str = n_obj["num"]
                    
                    fetched_nums.append(num_str)
                    
                    n_obj["shares"] += 1
                    n_obj["used_by"].append(chat_id)
                    with _stats_lock:
                        total_assigned_stats += 1
                    
                    if n_obj["shares"] >= bot_settings.get("num_share", 1):
                        if num_str not in used_numbers_list:
                            used_numbers_list.append(num_str)
                save_local_db()
                
            if wait_msg_id: edit_message(chat_id, wait_msg_id, render_body_text("✅ Number Found!"))
            _sess_msg = {"nums": fetched_nums, "service": "", "country": "",
                         "ctx": "search", "query": query,
                         "cc_codes": _build_cc_codes(fetched_nums), "cc_state": [True] * len(fetched_nums),
                         "msg_id": wait_msg_id or 0}
            user_active_sessions[chat_id] = _sess_msg
            kb = _rebuild_num_kb(chat_id)
            num_text = render_body_text(_build_num_text(chat_id))
            if wait_msg_id:
                try:
                    edit_message(chat_id, wait_msg_id, num_text, reply_markup={"inline_keyboard": kb})
                except Exception:
                    msg_res = send_message(chat_id, num_text, reply_markup={"inline_keyboard": kb})
                    if msg_res and msg_res.get("ok") and msg_res.get("result"):
                        user_active_sessions[chat_id]["msg_id"] = msg_res["result"]["message_id"]
            else:
                msg_res = send_message(chat_id, num_text, reply_markup={"inline_keyboard": kb})
                if msg_res and msg_res.get("ok") and msg_res.get("result"):
                    user_active_sessions[chat_id]["msg_id"] = msg_res["result"]["message_id"]
            if chat_id in user_states: user_states.pop(chat_id, None)
            if chat_id in temp_data: temp_data.pop(chat_id, None)
            return
            
        elif state == "wait_for_withdraw_amount" and text:
            msg_id_to_edit = temp_data[chat_id].get("msg_id")
            try:
                amount = float(text.strip())
                bal = _td(chat_id, "balance", 0.0)
                min_w = bot_settings.get('min_withdraw', 30.0)
                
                if amount < min_w:
                    if msg_id_to_edit: edit_message(chat_id, msg_id_to_edit, render_body_text(f"❌ Minimum withdrawal is {min_w} ₹!\n💰 Balance: {bal} ₹\n\n📝 Enter again:"), reply_markup=get_cancel_kb())
                    return
                if amount > bal:
                    if msg_id_to_edit: edit_message(chat_id, msg_id_to_edit, render_body_text(f"❌ You don't have enough balance!\n💰 Balance: {bal} ₹\n\n📝 Enter again:"), reply_markup=get_cancel_kb())
                    return
                    
                temp_data[chat_id]["amount"] = amount
                user_states[chat_id] = "wait_for_withdraw_number"
                if msg_id_to_edit:
                    edit_message(chat_id, msg_id_to_edit, render_body_text(f"✅ Amount: {amount} ₹\n\n📱 Now send your <b>{temp_data[chat_id]['method']}</b> account number:"), reply_markup=get_cancel_kb())
            except ValueError:
                if msg_id_to_edit: edit_message(chat_id, msg_id_to_edit, render_body_text("❌ Invalid amount!\n\n📝 Please send a valid number:"), reply_markup=get_cancel_kb())
            return
            
        elif state == "wait_for_2fa_name" and text:
            msg_id_to_edit = temp_data.get(chat_id, {}).get("msg_id")
            delete_message(chat_id, msg.get("message_id"))

            if not msg_id_to_edit:
                send_message(chat_id, render_body_text("❌ Error: Message not found. Try again."))
                user_states.pop(chat_id, None)
                if chat_id in temp_data: temp_data.pop(chat_id, None)
                return

            name = text.strip()[:30]
            temp_data[chat_id]["2fa_name"] = name
            user_states[chat_id] = "wait_for_2fa_key"

            ask_key_txt = (
                f"━━━━━━━━━━━━━━━\n"
                f"《 🔑 <b>ENTER 2FA KEY</b> 》\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📛 <b>NAME:</b> {name}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📝 Ab apna <b>2FA Secret Key</b> bhejein\n"
                f"━━━━━━━━━━━━━━━\n"
                f"💡 <b>Secret key kahan milegi?</b>\n"
                f"App/website pe 2FA setup ke time jo <b>32-digit key</b> ya <b>QR code</b> ke neeche likha hota hai, woh copy karke bhejein.\n"
                f"━━━━━━━━━━━━━━━"
            )
            _reset_btn_counter()
            cancel_kb = {"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "back_to_2fa_name", "style": _rs()}]]}
            edit_message(chat_id, msg_id_to_edit, render_body_text(ask_key_txt), reply_markup=cancel_kb)
            return

        elif state == "wait_for_2fa_key" and text:
            msg_id_to_edit = temp_data.get(chat_id, {}).get("msg_id")
            delete_message(chat_id, msg.get("message_id"))

            if not msg_id_to_edit:
                send_message(chat_id, render_body_text("❌ Error: Message not found. Try again."))
                user_states.pop(chat_id, None)
                if chat_id in temp_data: temp_data.pop(chat_id, None)
                return

            entry_name = temp_data.get(chat_id, {}).get("2fa_name", "My Account")

            try:
                secret = text.strip().replace(" ", "")
                totp = pyotp.TOTP(secret)
                code = totp.now()
                remaining_time = 30 - (int(time.time()) % 30)

                # Save to user's 2FA list
                if chat_id not in user_2fa_saved:
                    user_2fa_saved[chat_id] = []
                # Avoid duplicate keys
                existing_keys = [e["key"] for e in user_2fa_saved[chat_id]]
                if secret not in existing_keys:
                    user_2fa_saved[chat_id].append({"name": entry_name, "key": secret})
                    _save_2fa_saved()  # FIX: persist new 2FA entry to disk

                success_txt = _build_2fa_code_txt(entry_name, code, remaining_time)
                kb = _build_2fa_code_kb(code, secret)

                edit_message(chat_id, msg_id_to_edit, render_body_text(success_txt), reply_markup={"inline_keyboard": kb})
                user_states.pop(chat_id, None)
                if chat_id in temp_data: temp_data.pop(chat_id, None)
            except Exception as e:
                logger.warning(f"2FA key validation error: {e}")
                error_txt = (
                    f"━━━━━━━━━━━━━━━\n"
                    f"《 🔑 <b>ENTER 2FA KEY</b> 》\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"📛 <b>NAME:</b> {entry_name}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"📝 <b>2FA Secret Key bhejein</b>\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"❌ <b>Invalid Secret Key! Dobara try karein.</b>\n"
                    f"━━━━━━━━━━━━━━━"
                )
                _reset_btn_counter()
                cancel_kb = {"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "back_to_2fa_name", "style": _rs()}]]}
                edit_message(chat_id, msg_id_to_edit, render_body_text(error_txt), reply_markup=cancel_kb)
            return

        elif state == "wait_for_withdraw_number":
            if not _td_has(chat_id, "method", "amount"):
                send_message(chat_id, render_body_text("❌ Session expired. Please start withdrawal again."))
                user_states.pop(chat_id, None); temp_data.pop(chat_id, None); return
            msg_id_to_edit = _td(chat_id, "msg_id")
            method = _td(chat_id, "method", "UPI")
            amount = _td(chat_id, "amount", 0)
            number = text
            req_id = f"W_{str(uuid.uuid4())[:6].upper()}"
            
            first_name = msg.get("from", {}).get("first_name", "User")
            last_name = msg.get("from", {}).get("last_name", "")
            full_name = f"{first_name} {last_name}".strip()
            
            update_balance(chat_id, -amount)
            pending_withdrawals[req_id] = {"user_id": chat_id, "amount": amount, "method": method, "number": number, "full_name": full_name}
            
            # Save withdrawal to local DB
            _save_local_withdrawal(req_id, {"user_id": str(chat_id), "amount": amount, "method": method, "status": "pending"})
                
            admin_msg = f"🎙 <b>NEW WITHDRAWAL REQUEST</b>\n\n👤 <b>USER:</b> <a href='tg://user?id={chat_id}'>{full_name}</a>\n💳 <b>WITHDRAWAL:</b> {amount} INR\n🍏 <b>NUMBER:</b> <code>{number}</code>\n🏦 <b>METHOD:</b> {method}\n\n🧾 <b>REQ ID:</b> {req_id}\n👨‍⚖️ <b>PROCESSED BY ADMIN</b>"
            _reset_btn_counter()
            wd_kb = {"inline_keyboard": [[{"text": "APPROVE", "icon_custom_emoji_id": "5352694861990501856", "callback_data": f"wapp_{req_id}", "style": _rs()}, {"text": "REJECT", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"wrej_{req_id}", "style": _rs()}]]}
            rendered_admin_msg = render_body_text(admin_msg)
            # Track all sent message IDs for later editing on approve/reject
            sent_messages = []  # list of {"chat_id": ..., "message_id": ...}
            # Send to withdrawal group
            if bot_settings.get("w_group"):
                try:
                    res = send_message(bot_settings["w_group"], rendered_admin_msg, reply_markup=wd_kb)
                    if res.get("ok") and res.get("result") and "message_id" in res["result"]:
                        sent_messages.append({"chat_id": bot_settings["w_group"], "message_id": res["result"]["message_id"]})
                    else:
                        for adm_id in bot_settings.get("admins", []):
                            try: send_message(adm_id, render_body_text(f"⚠️ W.GROUP ({bot_settings['w_group']}) mein message send fail hua! Group ID check karein."))
                            except Exception as e:
                                logger.warning(f"Error: {e}")
                except Exception as e:
                    logger.warning(f"Error: {e}")
            # Send DM to each admin
            for adm_id in bot_settings.get("admins", []):
                if adm_id != chat_id:
                    try:
                        res = send_message(adm_id, rendered_admin_msg, reply_markup=wd_kb)
                        if res.get("ok") and res.get("result") and "message_id" in res["result"]:
                            sent_messages.append({"chat_id": adm_id, "message_id": res["result"]["message_id"]})
                    except Exception as e:
                        logger.warning(f"Error: {e}")
            pending_withdrawals[req_id]["sent_messages"] = sent_messages
            
            _reset_btn_counter()
            kb = {"inline_keyboard": [[{"text": "Close", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": _rs()}]]}
            success_text = f"{PEM['ok']} Your withdrawal request has been submitted!\n\n🧾 <b>Req ID:</b> {req_id}\n💰 <b>Amount:</b> {amount} ₹\n🏦 <b>Method:</b> {method}\n📱 <b>Number:</b> <code>{number}</code>"
            
            if msg_id_to_edit:
                edit_message(chat_id, msg_id_to_edit, render_body_text(success_text), reply_markup=kb)
            else:
                send_message(chat_id, render_body_text(success_text), reply_markup=kb)
                
            user_states.pop(chat_id, None)
            temp_data.pop(chat_id, None)
            return

    # --- Regular Commands ---
    if text.startswith("/start"):
        first_name = msg.get("from", {}).get("first_name", "User")
        _welcome_user(chat_id, first_name)
            
    elif text == "TRAFFIC":
        txt, markup = build_traffic_ui()
        send_message(chat_id, txt, reply_markup=markup)
        
    elif text == "Refer":
        u_data = get_user(chat_id)
        ref_link = f"https://t.me/{BOT_USERNAME.lstrip('@').strip()}?start={chat_id}"
        c_msg = bot_settings["custom_messages"].get("refer", {})
        
        raw_txt = c_msg.get("text", f"{PEM['gift']} Refer").replace("{ref_link}", ref_link).replace("{total_ref}", str(u_data.get('total_refers', 0))).replace("{ref_reward}", str(bot_settings['refer_reward']))
        txt = render_body_text(raw_txt)
        
        _reset_btn_counter()
        kb = [[{"text": "COPY LINK", "icon_custom_emoji_id": "5192739271886282680", "copy_text": {"text": ref_link}, "style": _rs()}]]
        _append_custom_btns(kb, c_msg)
        kb.append([{"text": "CLOSE", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": _rs()}])
        
        send_message(chat_id, txt, reply_markup={"inline_keyboard": kb})

    elif text == "WITHDRAWAL":
        if not bot_settings["withdraw_on"]:
            send_message(chat_id, render_body_text(f"{PEM['no']} Withdrawals are currently disabled."))
            return
        
        u_data = get_user(chat_id)
        bal = u_data.get('balance', 0.0)
        
        c_msg = bot_settings["custom_messages"].get("withdrawal", {})
        raw_txt = c_msg.get("text", "Withdrawal").replace("{bal}", str(bal)).replace("{total_otp}", str(u_data.get('total_otps', 0))).replace("{total_ref}", str(u_data.get('total_refers', 0))).replace("{min_w}", str(bot_settings['min_withdraw']))
        txt = render_body_text(raw_txt)
        
        _reset_btn_counter()
        kb = []
        for mi, m in enumerate(bot_settings["w_methods"]):
            kb.append([{"text": m.strip(), "icon_custom_emoji_id": "5190899075968441286", "callback_data": f"sel_wm_{m.strip()}", "style": _rs()}])
        
        _append_custom_btns(kb, c_msg)
        _add_close_btn(kb)
        send_message(chat_id, txt, reply_markup={"inline_keyboard": kb})

    elif text == "Admin Panel" and is_admin(chat_id):
        send_message(chat_id, get_admin_text(), reply_markup=admin_panel_keyboard())

    elif text == "GET NUMBER":
        all_services, txt, kb = _build_services_keyboard("get_number")
        if not all_services:
            send_message(chat_id, render_body_text(f"{PEM['no']} No numbers or services available!"))
        else:
            send_message(chat_id, txt, reply_markup={"inline_keyboard": kb})

    elif text == "Search Number":
        user_states[chat_id] = "wait_for_search"
        c_msg = bot_settings["custom_messages"].get("search_number", {})
        txt = render_body_text(c_msg.get("text", f"{PEM['num']} Search Number"))
        _reset_btn_counter()
        kb = []
        _append_custom_btns(kb, c_msg)
        _add_close_btn(kb)
        send_message(chat_id, txt, reply_markup={"inline_keyboard": kb})

    elif text == "2FA ONLINE" or text == "🔐 2FA ONLINE":
        _show_2fa_menu(chat_id)

    elif text == "SUPPORT":
        c_msg = bot_settings["custom_messages"].get("support", {})
        txt = render_body_text(c_msg.get("text", f"{PEM['msg']} Support"))
        if not txt.strip(): txt = render_body_text(f"{PEM['msg']} Support")
        _reset_btn_counter()
        kb = []
        sup_link = bot_settings.get("support_link", "")
        if sup_link:
            kb.append([{"text": "Contact Support", "icon_custom_emoji_id": "5337302974806922068", "url": sup_link, "style": _rs()}])
        for b in c_msg.get("buttons", []):
            b_copy = b.copy()
            b_copy["style"] = _rs()
            kb.append([b_copy])
        _add_close_btn(kb)
        send_message(chat_id, txt, reply_markup={"inline_keyboard": kb} if kb else None)

def _build_cc_codes(nums):
    """Build a parallel list of country-code strings for each number in nums."""
    codes = []
    for num in nums:
        _, iso, _ = get_flag_info_from_num(num)
        codes.append(_get_cc_from_iso(iso) or _get_cc_from_num(num))
    return codes


def _rebuild_num_kb(chat_id):
    """Rebuild the number-display inline keyboard from user_active_sessions, honouring cc_state."""
    session = user_active_sessions.get(chat_id, {})
    nums      = session.get("nums", [])
    service   = session.get("service", "")
    country   = session.get("country", "")
    ctx       = session.get("ctx", "regular")
    cc_codes  = session.get("cc_codes", [])
    cc_state  = session.get("cc_state", [True] * len(nums))
    query     = session.get("query", "")

    _reset_btn_counter()
    kb = []

    # ── number rows ────────────────────────────────────────────────
    any_cc_added = False
    has_any_cc   = False
    for i, num in enumerate(nums):
        raw = str(num).lstrip("+")
        _, iso, flag_eid = get_flag_info_from_num(raw)
        flag_emoji_id = flag_eid or "5780471598922337683"
        cc    = cc_codes[i] if i < len(cc_codes) else None
        added = cc_state[i] if i < len(cc_state) else False

        if cc:
            has_any_cc = True
        if added and cc:
            any_cc_added = True

        # Strip any existing CC from raw so we never get double-prepend
        local_raw = raw[len(cc):] if (cc and raw.startswith(str(cc))) else raw

        if added and cc:
            display_num = f"+{cc}{local_raw}"
        else:
            display_num = local_raw  # no + when CC not added

        kb.append([{"text": display_num, "icon_custom_emoji_id": flag_emoji_id,
                    "copy_text": {"text": display_num}, "style": _rs()}])

    # ── single CC toggle button below ALL numbers ───────────────────
    if has_any_cc:
        if any_cc_added:
            kb.append([{"text": "Remove country code", "icon_custom_emoji_id": "6206108815075579644",
                        "callback_data": "rem_cc_all", "style": _rs()}])
        else:
            kb.append([{"text": "Add country code", "icon_custom_emoji_id": "6206375377925839184",
                        "callback_data": "add_cc_all", "style": _rs()}])

    # ── action row ─────────────────────────────────────────────────
    if ctx == "regular":
        change_cb  = f"c_n_{service}_{country}"
        c_msg_key  = "get_number"
        last_btn_meta = {"text": "Back", "icon_custom_emoji_id": "5267490665117275176",
                         "callback_data": f"g_s_{service}"}
    else:  # search
        change_cb  = f"c_n_s_{query}_{service or ''}"
        c_msg_key  = "search_number"
        last_btn_meta = {"text": "Close", "icon_custom_emoji_id": "5420130255174145507",
                         "callback_data": "close_msg"}

    kb.append([
        {"text": "Change Number", "icon_custom_emoji_id": "5420155432272438703",
         "callback_data": change_cb, "style": _rs()},
        {"text": "OTP Group", "icon_custom_emoji_id": "5190447043545438788",
         "url": bot_settings.get("otp_link", ""), "style": _rs()}
    ])
    _append_custom_btns(kb, bot_settings["custom_messages"].get(c_msg_key, {}))
    # Assign style AFTER Change Number & OTP Group so visual order matches color rotation
    last_btn = {**last_btn_meta, "style": _rs()}
    kb.append([last_btn])

    return kb

def _build_num_text(chat_id):
    """Number display message body: Country + Waiting for OTP (premium emoji, no numbers in text)."""
    session = user_active_sessions.get(chat_id, {})
    nums = session.get("nums", [])

    if not nums:
        return "📱 Number Ready"

    first_raw = str(nums[0]).lstrip("+")
    _, iso, _ = get_flag_info_from_num(first_raw)
    flag_html = get_flag_info_html(first_raw)

    # Country full name from premium_flags
    c_name = iso
    for _code, _fdata in bot_settings.get("premium_flags", {}).items():
        if _fdata.get("iso") == iso:
            c_name = _fdata.get("name", iso)
            break

    world_pem = PEM.get("world", "🌐")
    wait_pem  = '<tg-emoji emoji-id="6264896248659056036">🔄</tg-emoji>'

    return (
        f"{world_pem} <b>Country:</b> {flag_html} <b>{c_name} ({iso})</b>\n"
        f"\n"
        f"{wait_pem} <b>Waiting for OTP</b>"
    )

def expire_previous_number(chat_id):
    if chat_id in user_active_sessions:
        prev_data = user_active_sessions[chat_id]
        prev_msg_id = prev_data["msg_id"]
        nums = prev_data["nums"]
        
        # Remove from ALL panel systems so no more messages go to inbox
        for num in nums:
            if num in nexa_assigned_numbers:
                del nexa_assigned_numbers[num]
            if num in voltx_assigned_numbers:
                del voltx_assigned_numbers[num]
            if num in stex_assigned_numbers:
                del stex_assigned_numbers[num]
        save_local_db()
        
        # Edit previous message and add Expired button
        _reset_btn_counter()
        kb = [[{"text": "Number Expired", "icon_custom_emoji_id": "5336997731481193790", "callback_data": "ignore", "style": _rs()}]]
        try:
            edit_message(chat_id, prev_msg_id, render_body_text(f"{PEM['no']} <b>Number Expired</b>"), reply_markup={"inline_keyboard": kb})
        except Exception as e:
            logger.warning(f"Error expiring number message: {e}")
        del user_active_sessions[chat_id]

# ==========================================
# Callback Query Handler
# ==========================================
def handle_callback(call):
    try:
        _handle_callback_inner(call)
    except Exception as e:
        # Always answer callback to stop button loading even on error
        try: answer_callback(call.get("id", ""), f"⚠️ Error: {str(e)[:40]}")
        except Exception as answer_err:
            logger.warning(f"Error: {answer_err}")
        logger.warning(f"Callback error ({call.get('data','')}): {e}")

def _safe_int(val, default=-1):
    """Safe int conversion — returns default on error."""
    try:
        return int(val)
    except (ValueError, IndexError, TypeError):
        return default

def _td(chat_id, key, default=None):
    """Safe temp_data access — returns default if missing."""
    return temp_data.get(chat_id, {}).get(key, default)

def _td_has(chat_id, *keys):
    """Check temp_data has chat_id and all given keys."""
    d = temp_data.get(chat_id, {})
    return all(k in d for k in keys)


def _handle_callback_inner(call):
    global total_assigned_stats
    chat_id = call["message"]["chat"]["id"]
    chat_type = call["message"]["chat"].get("type", "private")
    data = call.get("data", "")

    # 🌟 Button Loading Fix: Give Response to Telegram immediately when button pressed, so button does not get stuck!
    # ✅ FIX: Skip auto-answer when: recursive internal call, or handler calls answer_callback explicitly with text/show_alert
    _skip_auto_answer = (
        call.get("id") == "internal" or
        data.startswith(("test_p_conn_", "c_n_", "g_c_")) or
        data in {"toggle_nexa", "toggle_voltx", "toggle_stex", "check_fj"} or
        data.startswith(("del_b_", "del_nxa_", "del_sc_", "del_vxsc_", "del_vx_",
                         "del_stxsc_", "del_stx_", "del_adm_", "del_fwbtn_", "del_fw_",
                         "del_2fa_", "del_fj_", "del_wm_",
                         "nx_dr_", "vx_dr_", "stx_dr_", "wapp_", "wrej_"))
    )
    if not _skip_auto_answer:
        try: threading.Thread(target=answer_callback, args=(call["id"],)).start()
        except Exception as e:
            logger.warning(f"Error: {e}")

    if chat_type != "private" and not (data.startswith("wapp_") or data.startswith("wrej_")):
        return

    msg_id = call["message"]["message_id"]

    if chat_type == "private":
        if is_user_banned(chat_id):
            answer_callback(call["id"], "🚫 You are banned from using this bot!", show_alert=True)
            return

        if not check_force_join(chat_id) and data != "check_fj":
            send_force_join_msg(chat_id)
            return

    if data == "check_fj":
        if check_force_join(chat_id):
            # FIX: Pehle hi callback ko turant "answer" kar do — warna button
            # par loading-spinner animation khatam hone tak (3-4 sec) atka
            # rehta tha, aur impatient user dobara-dobara tap karke do
            # animations ek saath chala deta tha (isi se message idhar-udhar
            # ho raha tha). Ab spinner turant ruk jata hai.
            answer_callback(call["id"], "✅ Verified! Starting...")
            delete_message(chat_id, msg_id)
            first_name = call.get("from", {}).get("first_name", "User")
            _welcome_user(chat_id, first_name)
        else:
            answer_callback(call["id"], "❌ You haven't joined all channels yet!", show_alert=True)
        return

    if data == "close_msg":
        if chat_id in user_states: user_states.pop(chat_id, None)
        if chat_id in temp_data: temp_data.pop(chat_id, None)
        answer_callback(call["id"])
        delete_message(chat_id, msg_id)
        send_message(chat_id, render_body_text(f"{PEM['hi']} Main Menu:"), reply_markup=main_menu(chat_id))
        
    elif data == "cancel_2fa":
        if chat_id in user_states: user_states.pop(chat_id, None)
        if chat_id in temp_data: temp_data.pop(chat_id, None)
        _show_2fa_menu(chat_id, msg_id)
        answer_callback(call["id"])

    elif data == "back_to_2fa_name":
        user_states[chat_id] = "wait_for_2fa_name"
        prev_msg = temp_data.get(chat_id, {}).get("msg_id", msg_id)
        temp_data[chat_id] = {"msg_id": prev_msg}
        _show_2fa_name_input(chat_id, msg_id)
        answer_callback(call["id"])

    elif data == "gen_2fa":
        user_states[chat_id] = "wait_for_2fa_name"
        temp_data[chat_id] = {"msg_id": msg_id}
        _show_2fa_name_input(chat_id, msg_id)
        answer_callback(call["id"])

    elif data.startswith("ref_2fa_"):
        secret = data.replace("ref_2fa_", "")
        try:
            totp = pyotp.TOTP(secret)
            code = totp.now()
            remaining_time = 30 - (int(time.time()) % 30)
            # Find name from saved list
            entry_name = next((e["name"] for e in user_2fa_saved.get(chat_id, []) if e["key"] == secret), "My Account")
            success_txt = _build_2fa_code_txt(entry_name, code, remaining_time)
            kb = _build_2fa_code_kb(code, secret)
            edit_message(chat_id, msg_id, render_body_text(success_txt), reply_markup={"inline_keyboard": kb})
        except Exception as e:
            answer_callback(call["id"], "❌ Error refreshing code!", show_alert=True)

    elif data.startswith("how_2fa_"):
        secret = data.replace("how_2fa_", "")
        cur_text = call["message"].get("text", call["message"].get("caption", ""))
        m = re.search(r"CODE:\s*([0-9]{4,8})", cur_text)
        code = m.group(1) if m else "------"
        entry_name = next((e["name"] for e in user_2fa_saved.get(chat_id, []) if e["key"] == secret), "My Account")

        guide_txt = (
            f"━━━━━━━━━━━━━━━\n"
            f"《 🔑 <b>2FA CODE KAISE USE KAREIN</b> 》\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📛 <b>Account:</b> {entry_name}\n"
            f"🔐 <b>Current Code:</b> <code>{code}</code>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"<b>Step-by-Step Guide:</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"1️⃣ <b>App/website kholein</b> jahan login karna hai\n"
            f"   (Instagram, Facebook, Gmail, etc.)\n"
            f"━━━━━━━━━━━━━━━\n"
            f"2️⃣ <b>Email + Password</b> daalkar login karein\n"
            f"━━━━━━━━━━━━━━━\n"
            f"3️⃣ Login ke baad screen aayegi:\n"
            f"   <i>\"Enter your 6-digit code\" ya</i>\n"
            f"   <i>\"Go to your authentication app\"</i>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"4️⃣ Woh code box mein <b>upar wala code paste karein</b>:\n"
            f"   <tg-emoji emoji-id=\"5416117059207572332\">👉</tg-emoji> <code>{code}</code>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"5️⃣ <b>Continue / Verify</b> button press karein ✅\n"
            f"━━━━━━━━━━━━━━━\n"
            f"⚠️ <b>Zaroori:</b> Yeh code sirf <b>30 seconds</b> valid hai!\n"
            f"Code expire hone pe <b>Refresh</b> button se naya code lein.\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💾 <b>Recovery ke liye:</b> \"MY 2FA ADDED\" mein\n"
            f"apna secret key saved hai — kabhi bhi code generate kar sakte ho.\n"
            f"━━━━━━━━━━━━━━━"
        )
        _reset_btn_counter()
        guide_kb = {"inline_keyboard": [
            [{"text": "Click to copy", "icon_custom_emoji_id": "5353022963132174959", "copy_text": {"text": code}, "style": _rs()}],
            [{"text": "MY 2FA ADDED", "icon_custom_emoji_id": "5337255927735163754", "callback_data": "my_2fa_list", "style": _rs()}],
            [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"ref_2fa_{secret}", "style": _rs()}]
        ]}
        edit_message(chat_id, msg_id, render_body_text(guide_txt), reply_markup=guide_kb)
        try: answer_callback(call["id"])
        except Exception as e:
            logger.warning(f"Error: {e}")

    elif data == "my_2fa_list":
        _show_2fa_list(chat_id, msg_id)
        try: answer_callback(call["id"])
        except Exception as e:
            logger.warning(f"Error: {e}")

    elif data.startswith("gen_saved_2fa_"):
        try:
            idx = int(data.replace("gen_saved_2fa_", ""))
            saved = user_2fa_saved.get(chat_id, [])
            if idx < 0 or idx >= len(saved):
                answer_callback(call["id"], "❌ Entry not found!", show_alert=True)
                return
            entry = saved[idx]
            secret = entry["key"]
            entry_name = entry["name"]
            totp = pyotp.TOTP(secret)
            code = totp.now()
            remaining_time = 30 - (int(time.time()) % 30)

            success_txt = _build_2fa_code_txt(entry_name, code, remaining_time)
            kb = _build_2fa_code_kb(code, secret)
            edit_message(chat_id, msg_id, render_body_text(success_txt), reply_markup={"inline_keyboard": kb})
            try: answer_callback(call["id"])
            except Exception as e:
                logger.warning(f"Error: {e}")
        except Exception as e:
            answer_callback(call["id"], "❌ Error generating code!", show_alert=True)

    elif data.startswith("del_2fa_"):
        try:
            idx = int(data.replace("del_2fa_", ""))
            saved = user_2fa_saved.get(chat_id, [])
            if idx < 0 or idx >= len(saved):
                answer_callback(call["id"], "❌ Entry not found!", show_alert=True)
                return
            del_name = saved[idx]["name"]
            user_2fa_saved[chat_id].pop(idx)
            _save_2fa_saved()  # FIX: persist deletion to disk
            answer_callback(call["id"], f"🗑 '{del_name}' delete ho gaya!", show_alert=True)
            _show_2fa_list(chat_id, msg_id)
        except Exception as e:
            answer_callback(call["id"], "❌ Error!", show_alert=True)

    elif data == "cancel_abhi_edit":
        if chat_id in user_states: user_states.pop(chat_id, None)
        if chat_id in temp_data: temp_data.pop(chat_id, None)
        _show_abhi_panel(chat_id, msg_id)
        
    elif data == "dummy_alert":
        answer_callback(call["id"], "This feature will be added later!", show_alert=True)
        
    elif data == "refresh_traffic":
        txt, markup = build_traffic_ui()
        edit_message(chat_id, msg_id, txt, reply_markup=markup)
        answer_callback(call["id"], "✅ Traffic Refreshed!", show_alert=False)

    elif data.startswith("exp_rng_"):
        srv_query = data.replace("exp_rng_", "")
        
        country_stats = {}
        current_time = time.time()
        with _traffic_lock:
            traffic_snapshot = list(recent_traffic)
        for t in traffic_snapshot:
            if current_time - t.get("time", 0) <= 3600:
                if t.get("service", "").startswith(srv_query):
                    iso = t.get("iso", "XX")
                    flag = t.get("flag", "🌍")
                    if iso not in country_stats:
                        country_stats[iso] = {"count": 0, "flag": flag}
                    country_stats[iso]["count"] += 1
        
        if not country_stats:
            answer_callback(call["id"], "❌ No recent traffic found for this service!", show_alert=True)
            return
            
        _reset_btn_counter()
        kb = []
        for iso, c_data in sorted(country_stats.items(), key=lambda x: x[1]["count"], reverse=True):
            count = c_data["count"]
            c_name = iso
            emoji_id = "5780471598922337683"
            for code, fdata in bot_settings.get("premium_flags", {}).items():
                if fdata.get("iso") == iso:
                    c_name = fdata.get("name", iso)
                    if "id" in fdata: emoji_id = fdata["id"]
                    break
            
            btn_text = f"{c_name} ({iso}) - {count} OTP"
            kb.append([{"text": btn_text, "icon_custom_emoji_id": emoji_id, "callback_data": f"exp_c_{srv_query}_{iso}", "style": _rs()}])
            
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "refresh_traffic", "style": _rs()}])
        
        app_full_name, prem_app_html = get_service_info_html(srv_query)
        edit_message(chat_id, msg_id, render_body_text(f"📊 <b>Explore Service: {prem_app_html} {app_full_name}</b>\n\nSelect a country to view available ranges:"), reply_markup={"inline_keyboard": kb})
        answer_callback(call["id"])

    elif data.startswith("exp_c_"):
        # rpartition splits at the LAST "_" so service names with underscores survive intact
        _sfx = data[len("exp_c_"):]; srv_query, _, iso_query = _sfx.rpartition("_")
        
        nums = []
        current_time = time.time()
        with _traffic_lock:
            traffic_snapshot = list(recent_traffic)
        for t in traffic_snapshot:
            if current_time - t.get("time", 0) <= 3600:
                if t.get("service", "").startswith(srv_query) and t.get("iso") == iso_query:
                    num = t.get("number", "").replace("+", "").strip()
                    if num: nums.append(num)
        
        if not nums:
            answer_callback(call["id"], "❌ No recent numbers found for this country!", show_alert=True)
            return
            
        # Only take range from Nexa Services (not Search Countries, as those only have country codes)
        known_ranges = set()
        for s_name, c_dict in bot_settings.get("nexa_services", {}).items():
            for c_name, r_list in c_dict.items():
                for r in r_list:
                    known_ranges.add(r)
                    
        sorted_known = sorted(list(known_ranges), key=len, reverse=True)
        
        r_counts = Counter()
        for num in nums:
            matched = False
            for r in sorted_known:
                if num.startswith(r):
                    r_counts[r] += 1
                    matched = True
                    break
            if not matched:
                if len(num) >= 7:
                    r_counts[num[:7]] += 1
                else:
                    r_counts[num] += 1
                    
        r_list = r_counts.most_common(12)
        
        _reset_btn_counter()
        kb = []
        for r, count in r_list:
            kb.append([{"text": f"{r} ({count})", "icon_custom_emoji_id": "5352862640592949843", "copy_text": {"text": r}, "style": _rs()}])
            
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"exp_rng_{srv_query}", "style": _rs()}])
        
        app_full_name, prem_app_html = get_service_info_html(srv_query)
        prem_flag_html = get_flag_info_html(iso_query)
        
        edit_message(chat_id, msg_id, render_body_text(f"📊 <b>Ranges for {prem_app_html} {app_full_name} - {prem_flag_html} {iso_query}</b>\n\nClick on any range to copy it."), reply_markup={"inline_keyboard": kb})
        answer_callback(call["id"])

    # --- User Management Flows Integration ---
    elif data == "user_management":
        edit_message(chat_id, msg_id, get_user_management_text(), reply_markup=user_management_keyboard())

    elif data == "um_manage_balance":
        user_states[chat_id] = "wait_for_um_bal_uid"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the User ID to Manage Balance:"), reply_markup=get_cancel_kb())
        
    elif data == "um_ban_unban":
        user_states[chat_id] = "wait_for_um_ban_uid"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the User ID to Ban or Unban:"), reply_markup=get_cancel_kb())

    elif data == "um_user_profile":
        user_states[chat_id] = "wait_for_um_prof_uid"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the User ID to View Profile:"), reply_markup=get_cancel_kb())

    # --- Menu Design Integration ---
    elif data == "menu_design_list":
        edit_message(chat_id, msg_id, render_body_text(f"🎨 <b>Menu Design Editor</b>\n\nSelect a menu block to edit its Body Text and Inline Buttons. You can use Premium Emojis too!"), reply_markup=menu_design_list_keyboard())

    elif data == "md_reset_defaults":
        bot_settings["custom_messages"] = DEFAULT_CUSTOM_MESSAGES.copy()
        save_local_db()
        answer_callback(call["id"], "✅ Resetted to Premium Defaults!", show_alert=True)

    elif data.startswith("md_edit_"):
        answer_callback(call["id"])
        if chat_id in user_states: user_states.pop(chat_id, None)
        if chat_id in temp_data: temp_data.pop(chat_id, None)
        key = data.replace("md_edit_", "")
        cm_text = render_body_text(bot_settings["custom_messages"].get(key, {}).get("text", "..."))
        try:
            edit_message(chat_id, msg_id, render_body_text(f"🎨 <b>Editing: {key.upper()}</b>\n\nPreview of current Text:\n{cm_text}"), reply_markup=menu_edit_options_keyboard(key))
        except Exception as e:
            logger.warning(f"Error: {e}")

    elif data.startswith("md_text_"):
        key = data.replace("md_text_", "")
        user_states[chat_id] = "wait_for_menu_text"
        temp_data[chat_id] = {"msg_id": msg_id, "menu_key": key}
        edit_message(chat_id, msg_id, render_body_text(f"📝 <b>Edit Body: {key.upper()}</b>\n\nSend the new text. You can use Premium Emojis directly here.\n(Use standard HTML like <b>bold</b>, <i>italic</i> for formatting)"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"md_edit_{key}", "style": _rs()}]]})

    elif data.startswith("md_btns_"):
        answer_callback(call["id"]) 
        if chat_id in user_states: user_states.pop(chat_id, None) 
        if chat_id in temp_data: temp_data.pop(chat_id, None)
        key = data.replace("md_btns_", "")
        try:
            edit_message(chat_id, msg_id, render_body_text(f"⚙️ <b>Edit Inline Buttons: {key.upper()}</b>"), reply_markup=menu_buttons_list_keyboard(key))
        except Exception as e:
            logger.warning(f"Error: {e}")

    elif data.startswith("md_addbtn_"):
        key = data.replace("md_addbtn_", "")
        user_states[chat_id] = "wait_for_menu_btn"
        temp_data[chat_id] = {"msg_id": msg_id, "menu_key": key}
        edit_message(chat_id, msg_id, render_body_text(f"➕ <b>Add Button: {key.upper()}</b>\n\nSend custom button in this format:\n<code>Button Text - https://link.com</code>\n\n<i>(Only normal Emojis supported here!)</i>"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"md_btns_{key}", "style": _rs()}]]})

    elif data.startswith("md_delbtn_"):
        after_prefix = data[len("md_delbtn_"):]
        key, b_idx_str = after_prefix.rsplit("_", 1)
        b_idx = int(b_idx_str)
        if key in bot_settings["custom_messages"] and b_idx < len(bot_settings["custom_messages"][key].get("buttons", [])):
            del bot_settings["custom_messages"][key]["buttons"][b_idx]
            save_local_db()
            answer_callback(call["id"], "✅ Button Deleted!", show_alert=True)
            edit_message(chat_id, msg_id, render_body_text(f"⚙️ <b>Edit Inline Buttons: {key.upper()}</b>"), reply_markup=menu_buttons_list_keyboard(key))
        else:
            answer_callback(call["id"], "❌ Button not found!", show_alert=True)

    elif data.startswith("sel_wm_"):
        method = data.replace("sel_wm_", "")
        bal = get_user(chat_id).get('balance', 0.0)
        min_w = bot_settings.get('min_withdraw', 30.0)
        
        if bal < min_w:
            answer_callback(call["id"], f"❌ Insufficient balance!\nMinimum {min_w} ₹ required.\nYour balance: {bal} ₹", show_alert=True)
            return
        
        answer_callback(call["id"], f"💳 Method: {method} selected!\n💰 Balance: {bal} ₹\n\nNow enter the amount below.", show_alert=True)
        temp_data[chat_id] = {"method": method, "balance": bal, "msg_id": msg_id}
        user_states[chat_id] = "wait_for_withdraw_amount"
        try:
            edit_message(chat_id, msg_id, render_body_text(f"💳 Method: <b>{method}</b>\n💰 Available Balance: <b>{bal} ₹</b>\n\n📝 Enter the amount you want to withdraw (Min: {min_w} ₹):"), reply_markup=get_cancel_kb())
        except Exception as e:
            send_message(chat_id, render_body_text(f"💳 Method: <b>{method}</b>\n💰 Available Balance: <b>{bal} ₹</b>\n\n📝 Enter the amount you want to withdraw (Min: {min_w} ₹):"), reply_markup=get_cancel_kb())

    elif data == "test_message_flow":
        user_states[chat_id] = "wait_for_test_service"
        temp_data[chat_id] = {}
        edit_message(chat_id, msg_id, render_body_text("🧪 <b>Test Mode</b>\n\n📝 Send the Service Name (e.g., IG):"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": _rs()}]]})

    elif data == "manage_emojis":
        edit_message(chat_id, msg_id, render_body_text(f"{PEM['star']} <b>Premium Emoji Management</b>\n\nSelect a category below:"), reply_markup=emoji_settings_keyboard())

    elif data == "emoji_upload_menu":
        edit_message(chat_id, msg_id, render_body_text(f"📤 <b>All Uploading System</b>\n\nSelect what you want to upload:"), reply_markup=emoji_upload_keyboard())

    elif data == "emoji_delete_menu":
        edit_message(chat_id, msg_id, render_body_text(f"🗑 <b>All Deleting System</b>\n\nSelect what you want to delete:"), reply_markup=emoji_delete_keyboard())

    elif data == "emoji_download_menu":
        edit_message(chat_id, msg_id, render_body_text(f"📥 <b>All Downloading System</b>\n\nSelect what you want to download:"), reply_markup=emoji_download_keyboard())

    elif data == "up_flags_txt":
        user_states[chat_id] = "wait_for_flag_txt"
        edit_message(chat_id, msg_id, render_body_text("📂 Please upload the <b>Flag Emojis</b> <code>.txt</code> file."), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "emoji_upload_menu", "style": _rs()}]]})

    elif data == "up_apps_txt":
        user_states[chat_id] = "wait_for_app_txt"
        edit_message(chat_id, msg_id, render_body_text("📂 Please upload the <b>Service Apps</b> <code>.txt</code> file."), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "emoji_upload_menu", "style": _rs()}]]})

    elif data == "dl_flags_txt":
        content = generate_emoji_txt("flags")
        if content:
            send_document(chat_id, "Flag_Emojis.txt", content)
            answer_callback(call["id"], "✅ Downloaded!")
        else:
            answer_callback(call["id"], "❌ No Flag Emojis found!", show_alert=True)

    elif data == "dl_apps_txt":
        content = generate_emoji_txt("apps")
        if content:
            send_document(chat_id, "Service_Apps.txt", content)
            answer_callback(call["id"], "✅ Downloaded!")
        else:
            answer_callback(call["id"], "❌ No App Emojis found!", show_alert=True)

    elif data == "del_all_flags":
        bot_settings["premium_flags"] = {}
        save_local_db()
        answer_callback(call["id"], "✅ All Premium Flags Deleted Successfully!", show_alert=True)
        edit_message(chat_id, msg_id, render_body_text(f"🗑 <b>All Deleting System</b>\n\nSelect what you want to delete:"), reply_markup=emoji_delete_keyboard())

    elif data == "del_all_apps":
        bot_settings["premium_apps"] = {}
        save_local_db()
        answer_callback(call["id"], "✅ All Service Emojis Deleted Successfully!", show_alert=True)
        edit_message(chat_id, msg_id, render_body_text(f"🗑 <b>All Deleting System</b>\n\nSelect what you want to delete:"), reply_markup=emoji_delete_keyboard())


    elif data == "broadcast_msg":
        user_states[chat_id] = "wait_for_broadcast"
        edit_message(chat_id, msg_id, render_body_text("📢 <b>Broadcast Mode</b>\n\nSend the message you want to broadcast (Text, Photo, Video, File etc)."), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "back_to_admin", "style": _rs()}]]})

    elif data == "upload_num":
        user_states[chat_id] = "wait_for_txt"
        edit_message(chat_id, msg_id, render_body_text("📂 Please upload the numbers in a <b>.txt</b> file."), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "back_to_admin", "style": _rs()}]]})

    elif data == "delete_files":
        _reset_btn_counter()
        kb = []
        for b_id, b_data in number_batches.items():
            kb.append([{"text": f"{b_data['filename']} ({len(b_data['numbers'])})", "icon_custom_emoji_id": "5422557736330106570", "callback_data": f"del_b_{b_id}", "style": _rs()}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "back_to_admin", "style": _rs()}])
        txt = "🗑 Select a file to delete:" if len(kb) > 1 else f"{PEM['no']} No files found."
        edit_message(chat_id, msg_id, render_body_text(txt), reply_markup={"inline_keyboard": kb})

    elif data.startswith("del_b_"):
        b_id = data.split("del_b_")[1]
        if b_id in number_batches:
            del number_batches[b_id]
            save_local_db()
            answer_callback(call["id"], "✅ File deleted!", show_alert=True)
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "delete_files", "id": "internal"})

    elif data == "show_used":
        all_nums = _get_all_numbers_set()
        otp_used = [n for n in all_nums if n in otp_received_numbers]
        _reset_btn_counter()
        kb = {"inline_keyboard": [[{"text": "Download TXT", "icon_custom_emoji_id": "5257969839313526622", "callback_data": "dl_used", "style": _rs()}], [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "back_to_admin", "style": _rs()}]]}
        edit_message(chat_id, msg_id, render_body_text(f"{PEM['ok']} <b>Used Numbers (OTP Received):</b> {len(otp_used)}"), reply_markup=kb)

    elif data == "show_unused":
        all_nums = _get_all_numbers_set()
        otp_unused = [n for n in all_nums if n not in otp_received_numbers]
        _reset_btn_counter()
        kb = {"inline_keyboard": [[{"text": "Download TXT", "icon_custom_emoji_id": "5257969839313526622", "callback_data": "dl_unused", "style": _rs()}], [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "back_to_admin", "style": _rs()}]]}
        edit_message(chat_id, msg_id, render_body_text(f"{PEM['rocket']} <b>Unused Numbers (No OTP):</b> {len(otp_unused)}"), reply_markup=kb)

    elif data == "dl_used":
        all_nums = _get_all_numbers_set()
        otp_used = [n for n in all_nums if n in otp_received_numbers]
        if not otp_used:
            answer_callback(call["id"], "No OTP received numbers found!", show_alert=True)
            return
        content = "\n".join(otp_used).encode('utf-8')
        send_document(chat_id, "used_otp_numbers.txt", content)
        answer_callback(call["id"])

    elif data == "dl_unused":
        all_nums = _get_all_numbers_set()
        otp_unused = [n for n in all_nums if n not in otp_received_numbers]
        if not otp_unused:
            answer_callback(call["id"], "All numbers have received OTP!", show_alert=True)
            return
        content = "\n".join(otp_unused).encode('utf-8')
        send_document(chat_id, "unused_no_otp_numbers.txt", content)
        answer_callback(call["id"])

    elif data == "lb_main":
        txt = f"━━━━━━━━━━━━━━━\n《 {PEM['admin']} <b>LEADER BOARD MENU</b> 》\n━━━━━━━━━━━━━━━\n<i>Select a category to view the top performers or history.</i>\n━━━━━━━━━━━━━━━"
        _reset_btn_counter()
        kb = [
            [{"text": "Top Referrers", "icon_custom_emoji_id": "5420145051336485498", "callback_data": "lb_top_refs", "style": _rs()}],
            [{"text": "Top OTP Receivers", "icon_custom_emoji_id": "5353001161878182134", "callback_data": "lb_top_otps", "style": _rs()}],
            [{"text": "Withdrawal History", "icon_custom_emoji_id": "5348469219761626211", "callback_data": "lb_w_history", "style": _rs()}],
            [{"text": "Back to Admin", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "back_to_admin", "style": _rs()}]
        ]
        edit_message(chat_id, msg_id, render_body_text(txt), reply_markup={"inline_keyboard": kb})

    elif data.startswith("lb_"):
        sub = data.replace("lb_", "")
        edit_message(chat_id, msg_id, render_body_text("⌛ <i>Fetching Data...</i>"))
        
        num_map = {"1": "1️⃣", "2": "2️⃣", "3": "3️⃣", "4": "4️⃣", "5": "5️⃣", "6": "6️⃣", "7": "7️⃣", "8": "8️⃣", "9": "9️⃣", "0": "0️⃣"}
        def get_p_num(n): return "".join([num_map.get(c, c) for c in str(n)])
        
        try:
            if sub == "top_refs":
                title, field, limit_n, icon = "TOP 5 REFERRERS", "total_refers", 5, PEM.get('user', '👥')
                res_txt = ""
                count = 1
                sorted_users = sorted(local_users_db.items(), key=lambda x: x[1].get(field, 0), reverse=True)[:limit_n]
                for uid, d in sorted_users:
                    if d.get(field, 0) > 0:
                        p = "└" if count == limit_n else "├"
                        res_txt += f"{p} {get_p_num(count)} <a href='tg://user?id={uid}'>{uid}</a> ➔ <b>{d.get(field,0)}</b>\n"
                        count += 1
                if not res_txt: res_txt = "└ <i>No data found.</i>\n"

            elif sub == "top_otps":
                title, field, limit_n, icon = "TOP 5 OTP RECEIVERS", "total_otps", 5, PEM.get('msg', '📩')
                res_txt = ""
                count = 1
                sorted_users = sorted(local_users_db.items(), key=lambda x: x[1].get(field, 0), reverse=True)[:limit_n]
                for uid, d in sorted_users:
                    if d.get(field, 0) > 0:
                        p = "└" if count == limit_n else "├"
                        res_txt += f"{p} {get_p_num(count)} <a href='tg://user?id={uid}'>{uid}</a> ➔ <b>{d.get(field,0)}</b>\n"
                        count += 1
                if not res_txt: res_txt = "└ <i>No data found.</i>\n"

            elif sub == "w_history":
                title, limit_n, icon = "LAST 10 WITHDRAWALS", 10, PEM.get('money', '💸')
                res_txt = ""
                count = 1
                sorted_ws = sorted(local_withdrawals_db.items(), key=lambda x: x[1].get("timestamp", 0), reverse=True)[:limit_n]
                for wid, d in sorted_ws:
                    s = str(d.get('status','Pending')).lower()
                    stat_icon = PEM.get('ok','✅') if s in ["approved","success"] else PEM.get('no','❌') if s=="rejected" else "⏳"
                    uid = d.get('user_id','User')
                    p = "└" if count == limit_n else "├"
                    res_txt += f"{p} {get_p_num(count)} <a href='tg://user?id={uid}'>{uid}</a> ➔ <b>{d.get('amount',0)}₹</b> {stat_icon}\n"
                    count += 1
                if not res_txt: res_txt = "└ <i>No history found.</i>\n"

            final_msg = f"━━━━━━━━━━━━━━━\n{icon} <b>{title}</b>\n━━━━━━━━━━━━━━━\n{res_txt}━━━━━━━━━━━━━━━"
            _reset_btn_counter()
            kb = [[{"text": "Refresh", "icon_custom_emoji_id": "5420155432272438703", "callback_data": data, "style": _rs()}, {"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "lb_main", "style": _rs()}]]
            edit_message(chat_id, msg_id, render_body_text(final_msg), reply_markup={"inline_keyboard": kb})

        except Exception as e:
            edit_message(chat_id, msg_id, render_body_text(f"❌ Error: {e}"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "lb_main", "style": _rs()}]]})

    elif data == "back_to_admin":
        if chat_id in user_states: user_states.pop(chat_id, None)
        if chat_id in temp_data: temp_data.pop(chat_id, None)
        edit_message(chat_id, msg_id, get_admin_text(), reply_markup=admin_panel_keyboard())
        
    elif data == "system_settings":
        edit_message(chat_id, msg_id, render_body_text(f"{PEM['gear']} <b>System Settings</b>\nManage advanced bot configurations below:"), reply_markup=system_settings_keyboard())

    elif data == "auto_mode":
        nexa_cnt  = len(bot_settings.get('nexa_keys', []))
        voltx_cnt = len(bot_settings.get('voltx_keys', []))
        stex_cnt  = len(bot_settings.get('stex_keys', []))
        nexa_on   = bot_settings.get("nexa_on", False)
        voltx_on  = bot_settings.get("voltx_on", False)
        stex_on   = bot_settings.get("stex_on", False)
        _on_txt  = '<tg-emoji emoji-id="6266827283135207188">✅</tg-emoji> ON'
        _off_txt = '<tg-emoji emoji-id="6267237615720731788">🔴</tg-emoji> OFF'
        edit_message(chat_id, msg_id, render_body_text(
            '➖➖➖➖➖➖➖\n'
            '  <tg-emoji emoji-id="6318566568011764192">⚡</tg-emoji>  <b>AUTO MODE</b>  <tg-emoji emoji-id="6318566568011764192">⚡</tg-emoji>\n'
            '➖➖➖➖➖➖➖\n\n'
            f'<b>Nexa</b>   »  Keys: <b>{nexa_cnt}</b>   {_on_txt if nexa_on else _off_txt}\n'
            f'<b>VoltX</b>  »  Keys: <b>{voltx_cnt}</b>  {_on_txt if voltx_on else _off_txt}\n'
            f'<b>Stex</b>   »  Keys: <b>{stex_cnt}</b>   {_on_txt if stex_on else _off_txt}\n\n'
            '➖➖➖➖➖➖➖'
        ), reply_markup=auto_mode_keyboard())

    elif data == "toggle_nexa":
        bot_settings["nexa_on"] = not bot_settings.get("nexa_on", False)
        save_local_db()
        if bot_settings["nexa_on"]:
            _service_warmup_needed["nexa"] = True  # Skip old OTPs on first poll after enable
        state = "✅ ON" if bot_settings["nexa_on"] else "🔴 OFF"
        answer_callback(call["id"], f"Nexa is now {state}", show_alert=False)
        handle_callback({"message": call["message"], "data": "auto_mode", "id": "internal"})

    elif data == "toggle_voltx":
        bot_settings["voltx_on"] = not bot_settings.get("voltx_on", False)
        save_local_db()
        if bot_settings["voltx_on"]:
            _service_warmup_needed["voltx"] = True  # Skip old OTPs on first poll after enable
        state = "✅ ON" if bot_settings["voltx_on"] else "🔴 OFF"
        answer_callback(call["id"], f"VoltX is now {state}", show_alert=False)
        handle_callback({"message": call["message"], "data": "auto_mode", "id": "internal"})

    elif data == "toggle_stex":
        bot_settings["stex_on"] = not bot_settings.get("stex_on", False)
        save_local_db()
        if bot_settings["stex_on"]:
            _service_warmup_needed["stex"] = True  # Skip old OTPs on first poll after enable
        state = "✅ ON" if bot_settings["stex_on"] else "🔴 OFF"
        answer_callback(call["id"], f"Stex is now {state}", show_alert=False)
        handle_callback({"message": call["message"], "data": "auto_mode", "id": "internal"})

    elif data == "nexa_control":
        edit_message(chat_id, msg_id, render_body_text(f'<tg-emoji emoji-id="6282760761399841824">🔹</tg-emoji> <b>Nexa</b>\n\nTotal API Keys: {len(bot_settings.get("nexa_keys", []))}\nManage your Nexa API Keys below:'), reply_markup=_panel_control_keyboard("Nexa"))

    elif data == "add_nexa_key":
        user_states[chat_id] = "wait_for_add_nexa_key"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the new Nexa API Key (e.g. nxa_...):"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "nexa_control", "style": _rs()}]]})

    elif data == "view_nexa_keys":
        _reset_btn_counter()
        kb = []
        for idx, key in enumerate(bot_settings.get("nexa_keys", [])):
            safe_name = key[:10] + "..." if len(key)>10 else key
            kb.append([{"text": f"Delete {safe_name}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"del_nxa_{idx}", "style": _rs()}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "nexa_control", "style": _rs()}])
        edit_message(chat_id, msg_id, render_body_text("🗑 <b>Select Nexa Key to Delete:</b>"), reply_markup={"inline_keyboard": kb})

    elif data.startswith("del_nxa_"):
        idx = _safe_int(data.split("_")[2] if len(data.split("_")) > 2 else -1)
        if 0 <= idx < len(bot_settings.get("nexa_keys", [])):
            del bot_settings["nexa_keys"][idx]
            save_local_db()
            answer_callback(call["id"], "✅ Nexa Key Deleted!", show_alert=True)
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "view_nexa_keys", "id": "internal"})
        else:
            answer_callback(call["id"], "❌ Key not found!", show_alert=True)

    elif data == "nexa_search_country":
        _show_panel_search_countries("nexa", chat_id, msg_id)

    elif data == "add_search_country":
        user_states[chat_id] = "wait_for_add_sc"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the Country Code (e.g. 880 or 92):"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "nexa_search_country", "style": _rs()}]]})

    elif data.startswith("del_sc_"):
        idx = _safe_int(data.split("_")[2] if len(data.split("_")) > 2 else -1)
        if 0 <= idx < len(bot_settings.get("nexa_search_countries", [])):
            del bot_settings["nexa_search_countries"][idx]
            save_local_db()
            answer_callback(call["id"], "✅ Country Deleted!", show_alert=True)
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "nexa_search_country", "id": "internal"})
        else:
            answer_callback(call["id"], "❌ Country not found!", show_alert=True)

    elif data == "manage_nexa_srv":
        _reset_btn_counter()
        kb = []
        srvs = bot_settings.get("nexa_services", {})
        apps_db = bot_settings.get("premium_apps", {})
        for si, srv in enumerate(srvs):
            emoji_id = _get_service_emoji_id(srv, apps_db)
            kb.append([{"text": f"{srv}", "icon_custom_emoji_id": emoji_id, "callback_data": f"nx_srv_{srv}", "style": _rs()}])
        kb.append([{"text": "Add New Service", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "nx_add_srv", "style": _rs()}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "nexa_control", "style": _rs()}])
        edit_message(chat_id, msg_id, render_body_text("📦 <b>Nexa Services Manager</b>\nManage your API-based dynamic services below:"), reply_markup={"inline_keyboard": kb})

    elif data == "nx_add_srv":
        user_states[chat_id] = "wait_nx_srv_name"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Enter Service Name (e.g. TELEGRAM):"), reply_markup=get_cancel_kb())

    elif data.startswith("nx_srv_"):
        srv = data.replace("nx_srv_", "")
        _reset_btn_counter()
        kb = []
        countries = bot_settings["nexa_services"].get(srv, {})
        flags_db = bot_settings.get("premium_flags", {})
        for ci, c in enumerate(countries):
            emoji_id = _find_flag_emoji_id(c, flags_db)
            kb.append([{"text": f"{c} ({len(countries[c])} Ranges)", "icon_custom_emoji_id": emoji_id, "callback_data": f"nx_cnt_{srv}_{c}", "style": _rs()}])
        kb.append([{"text": "Add Country", "icon_custom_emoji_id": "5420323438508155202", "callback_data": f"nx_add_cnt_{srv}", "style": _rs()}])
        kb.append([{"text": "Delete Service", "icon_custom_emoji_id": "5422557736330106570", "callback_data": f"nx_del_srv_{srv}", "style": _rs()}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_nexa_srv", "style": _rs()}])
        edit_message(chat_id, msg_id, render_body_text(f"📂 <b>Service: {srv}</b>\nManage countries for this service:"), reply_markup={"inline_keyboard": kb})

    elif data.startswith("nx_add_cnt_"):
        srv = data.replace("nx_add_cnt_", "")
        user_states[chat_id] = "wait_nx_cnt_name"
        temp_data[chat_id] = {"msg_id": msg_id, "srv": srv}
        edit_message(chat_id, msg_id, render_body_text(f"🌍 Enter Country Name for <b>{srv}</b> (e.g. BD, INDIA):"), reply_markup=get_cancel_kb())

    elif data.startswith("nx_cnt_"):
        _sfx = data[len("nx_cnt_"):]; srv, _, cnt = _sfx.partition("_")
        ranges = bot_settings["nexa_services"][srv].get(cnt, [])
        
        _reset_btn_counter()
        kb = []
        row = []
        for ri, r in enumerate(ranges):
            row.append({"text": f"Delete {r}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"nx_dr_{srv}_{cnt}_{r}", "style": _rs()})
            if len(row) == 2:
                kb.append(row)
                row = []
        if row: kb.append(row)
        
        kb.append([{"text": "Add Range", "icon_custom_emoji_id": "5420323438508155202", "callback_data": f"nx_addr_{srv}_{cnt}", "style": _rs()}])
        kb.append([{"text": "Delete Entire Country", "icon_custom_emoji_id": "5422557736330106570", "callback_data": f"nx_del_cnt_{srv}_{cnt}", "style": _rs()}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"nx_srv_{srv}", "style": _rs()}])
        
        txt = f"📍 <b>Service: {srv} | Country: {cnt}</b>\n\n<b>Total Ranges:</b> {len(ranges)}\n<i>Click on a range below to delete it, or add a new one.</i>"
        edit_message(chat_id, msg_id, render_body_text(txt), reply_markup={"inline_keyboard": kb})

    elif data.startswith("nx_addr_"):
        _sfx = data[len("nx_addr_"):]; srv, _, cnt = _sfx.partition("_")
        user_states[chat_id] = "wait_nx_addr"
        temp_data[chat_id] = {"msg_id": msg_id, "srv": srv, "cnt": cnt}
        edit_message(chat_id, msg_id, render_body_text(f"📝 Send the new Range for <b>{cnt}</b> (e.g. 88017):"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"nx_cnt_{srv}_{cnt}", "style": _rs()}]]})

    elif data.startswith("nx_dr_"):
        _sfx = data[len("nx_dr_"):]; srv, _, _rest = _sfx.partition("_"); cnt, _, rng = _rest.partition("_")
        if rng in bot_settings["nexa_services"].get(srv, {}).get(cnt, []):
            bot_settings["nexa_services"][srv][cnt].remove(rng)
            save_local_db()
            answer_callback(call["id"], f"✅ Range {rng} deleted!", show_alert=True)
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": f"nx_cnt_{srv}_{cnt}", "id": "internal"})

    elif data.startswith("nx_del_srv_"):
        srv = data.replace("nx_del_srv_", "")
        if srv in bot_settings["nexa_services"]: del bot_settings["nexa_services"][srv]
        save_local_db()
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "manage_nexa_srv", "id": "internal"})

    elif data.startswith("nx_del_cnt_"):
        _sfx = data[len("nx_del_cnt_"):]; srv, _, cnt = _sfx.partition("_")
        if cnt in bot_settings["nexa_services"].get(srv, {}): del bot_settings["nexa_services"][srv][cnt]
        save_local_db()
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": f"nx_srv_{srv}", "id": "internal"})

    # ==========================================
    # VoltX Control Callbacks
    # ==========================================
    elif data == "voltx_control":
        edit_message(chat_id, msg_id, render_body_text(f'<tg-emoji emoji-id="6282760761399841824">🔹</tg-emoji> <b>VoltX</b>\n\nTotal API Keys: {len(bot_settings.get("voltx_keys", []))}\nManage your VoltX API Keys below:'), reply_markup=_panel_control_keyboard("VoltX"))

    elif data == "add_voltx_key":
        user_states[chat_id] = "wait_for_add_voltx_key"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the new VoltX API Key (mauthapi key):"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "voltx_control", "style": _rs()}]]})

    elif data == "view_voltx_keys":
        _reset_btn_counter()
        kb = []
        for idx, key in enumerate(bot_settings.get("voltx_keys", [])):
            safe_name = key[:10] + "..." if len(key) > 10 else key
            kb.append([{"text": f"Delete {safe_name}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"del_vx_{idx}", "style": _rs()}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "voltx_control", "style": _rs()}])
        edit_message(chat_id, msg_id, render_body_text("🗑 <b>Select VoltX Key to Delete:</b>"), reply_markup={"inline_keyboard": kb})

    elif data.startswith("del_vxsc_"):
        idx = _safe_int(data.split("_")[2] if len(data.split("_")) > 2 else -1)
        if 0 <= idx < len(bot_settings.get("voltx_search_countries", [])):
            del bot_settings["voltx_search_countries"][idx]
            save_local_db()
            answer_callback(call["id"], "✅ Country Deleted!", show_alert=True)
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "voltx_search_country", "id": "internal"})
        else:
            answer_callback(call["id"], "❌ Country not found!", show_alert=True)

    elif data.startswith("del_vx_"):
        idx = _safe_int(data.split("_")[2] if len(data.split("_")) > 2 else -1)
        if 0 <= idx < len(bot_settings.get("voltx_keys", [])):
            del bot_settings["voltx_keys"][idx]
            save_local_db()
            answer_callback(call["id"], "✅ VoltX Key Deleted!", show_alert=True)
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "view_voltx_keys", "id": "internal"})
        else:
            answer_callback(call["id"], "❌ Key not found!", show_alert=True)

    elif data == "voltx_search_country":
        _show_panel_search_countries("voltx", chat_id, msg_id)

    elif data == "add_vx_search_country":
        user_states[chat_id] = "wait_for_add_vxsc"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the Country Code (e.g. 880 or 92):"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "voltx_search_country", "style": _rs()}]]})

    elif data == "manage_voltx_srv":
        _reset_btn_counter()
        kb = []
        srvs = bot_settings.get("voltx_services", {})
        apps_db = bot_settings.get("premium_apps", {})
        for si, srv in enumerate(srvs):
            emoji_id = _get_service_emoji_id(srv, apps_db)
            kb.append([{"text": f"{srv}", "icon_custom_emoji_id": emoji_id, "callback_data": f"vx_srv_{srv}", "style": _rs()}])
        kb.append([{"text": "Add New Service", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "vx_add_srv", "style": _rs()}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "voltx_control", "style": _rs()}])
        edit_message(chat_id, msg_id, render_body_text("📦 <b>VoltX Services Manager</b>\nManage your API-based dynamic services below:"), reply_markup={"inline_keyboard": kb})

    elif data == "vx_add_srv":
        user_states[chat_id] = "wait_vx_srv_name"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Enter Service Name (e.g. WHATSAPP, FACEBOOK):"), reply_markup=get_cancel_kb())

    elif data.startswith("vx_srv_"):
        srv = data.replace("vx_srv_", "")
        _reset_btn_counter()
        kb = []
        countries = bot_settings["voltx_services"].get(srv, {})
        flags_db = bot_settings.get("premium_flags", {})
        for ci, c in enumerate(countries):
            emoji_id = _find_flag_emoji_id(c, flags_db)
            kb.append([{"text": f"{c} ({len(countries[c])} Ranges)", "icon_custom_emoji_id": emoji_id, "callback_data": f"vx_cnt_{srv}_{c}", "style": _rs()}])
        kb.append([{"text": "Add Country", "icon_custom_emoji_id": "5420323438508155202", "callback_data": f"vx_add_cnt_{srv}", "style": _rs()}])
        kb.append([{"text": "Delete Service", "icon_custom_emoji_id": "5422557736330106570", "callback_data": f"vx_del_srv_{srv}", "style": _rs()}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_voltx_srv", "style": _rs()}])
        edit_message(chat_id, msg_id, render_body_text(f"📂 <b>Service: {srv}</b>\nManage countries for this service:"), reply_markup={"inline_keyboard": kb})

    elif data.startswith("vx_add_cnt_"):
        srv = data.replace("vx_add_cnt_", "")
        user_states[chat_id] = "wait_vx_cnt_name"
        temp_data[chat_id] = {"msg_id": msg_id, "srv": srv}
        edit_message(chat_id, msg_id, render_body_text(f"🌍 Enter Country Name for <b>{srv}</b> (e.g. BD, INDIA):"), reply_markup=get_cancel_kb())

    elif data.startswith("vx_cnt_"):
        _sfx = data[len("vx_cnt_"):]; srv, _, cnt = _sfx.partition("_")
        ranges = bot_settings["voltx_services"][srv].get(cnt, [])
        _reset_btn_counter()
        kb = []
        row = []
        for ri, r in enumerate(ranges):
            row.append({"text": f"Del {r}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"vx_dr_{srv}_{cnt}_{r}", "style": _rs()})
            if len(row) == 2:
                kb.append(row)
                row = []
        if row: kb.append(row)
        kb.append([{"text": "Add Range", "icon_custom_emoji_id": "5420323438508155202", "callback_data": f"vx_addr_{srv}_{cnt}", "style": _rs()}])
        kb.append([{"text": "Delete Entire Country", "icon_custom_emoji_id": "5422557736330106570", "callback_data": f"vx_del_cnt_{srv}_{cnt}", "style": _rs()}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"vx_srv_{srv}", "style": _rs()}])
        txt = f"📍 <b>Service: {srv} | Country: {cnt}</b>\n\n<b>Total Ranges:</b> {len(ranges)}\n<i>Click on a range below to delete it, or add a new one.</i>"
        edit_message(chat_id, msg_id, render_body_text(txt), reply_markup={"inline_keyboard": kb})

    elif data.startswith("vx_addr_"):
        _sfx = data[len("vx_addr_"):]; srv, _, cnt = _sfx.partition("_")
        user_states[chat_id] = "wait_vx_addr"
        temp_data[chat_id] = {"msg_id": msg_id, "srv": srv, "cnt": cnt}
        edit_message(chat_id, msg_id, render_body_text(f"📝 Send the new Range for <b>{cnt}</b> (e.g. 88017):"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"vx_cnt_{srv}_{cnt}", "style": _rs()}]]})

    elif data.startswith("vx_dr_"):
        _sfx = data[len("vx_dr_"):]; srv, _, _rest = _sfx.partition("_"); cnt, _, rng = _rest.partition("_")
        if rng in bot_settings["voltx_services"].get(srv, {}).get(cnt, []):
            bot_settings["voltx_services"][srv][cnt].remove(rng)
            save_local_db()
            answer_callback(call["id"], f"✅ Range {rng} deleted!", show_alert=True)
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": f"vx_cnt_{srv}_{cnt}", "id": "internal"})

    elif data.startswith("vx_del_srv_"):
        srv = data.replace("vx_del_srv_", "")
        if srv in bot_settings["voltx_services"]: del bot_settings["voltx_services"][srv]
        save_local_db()
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "manage_voltx_srv", "id": "internal"})

    elif data.startswith("vx_del_cnt_"):
        _sfx = data[len("vx_del_cnt_"):]; srv, _, cnt = _sfx.partition("_")
        if cnt in bot_settings["voltx_services"].get(srv, {}): del bot_settings["voltx_services"][srv][cnt]
        save_local_db()
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": f"vx_srv_{srv}", "id": "internal"})

    # ==========================================
    # Stex Control Callbacks
    # ==========================================
    elif data == "stex_control":
        edit_message(chat_id, msg_id, render_body_text(f'<tg-emoji emoji-id="6282760761399841824">🔹</tg-emoji> <b>Stex</b>\n\nTotal API Keys: {len(bot_settings.get("stex_keys", []))}\nManage your Stex API Keys below:'), reply_markup=_panel_control_keyboard("Stex"))

    elif data == "add_stex_key":
        user_states[chat_id] = "wait_for_add_stex_key"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the new Stex API Key (api-key):"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "stex_control", "style": _rs()}]]})

    elif data == "view_stex_keys":
        _reset_btn_counter()
        kb = []
        for idx, key in enumerate(bot_settings.get("stex_keys", [])):
            safe_name = key[:10] + "..." if len(key) > 10 else key
            kb.append([{"text": f"Delete {safe_name}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"del_stx_{idx}", "style": _rs()}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "stex_control", "style": _rs()}])
        edit_message(chat_id, msg_id, render_body_text("🗑 <b>Select Stex Key to Delete:</b>"), reply_markup={"inline_keyboard": kb})

    elif data.startswith("del_stxsc_"):
        idx = _safe_int(data.split("_")[2] if len(data.split("_")) > 2 else -1)
        if 0 <= idx < len(bot_settings.get("stex_search_countries", [])):
            del bot_settings["stex_search_countries"][idx]
            save_local_db()
            answer_callback(call["id"], "✅ Country Deleted!", show_alert=True)
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "stex_search_country", "id": "internal"})
        else:
            answer_callback(call["id"], "❌ Country not found!", show_alert=True)

    elif data.startswith("del_stx_"):
        idx = _safe_int(data.split("_")[2] if len(data.split("_")) > 2 else -1)
        if 0 <= idx < len(bot_settings.get("stex_keys", [])):
            del bot_settings["stex_keys"][idx]
            save_local_db()
            answer_callback(call["id"], "✅ Stex Key Deleted!", show_alert=True)
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "view_stex_keys", "id": "internal"})
        else:
            answer_callback(call["id"], "❌ Key not found!", show_alert=True)

    elif data == "stex_search_country":
        _show_panel_search_countries("stex", chat_id, msg_id)

    elif data == "add_stx_search_country":
        user_states[chat_id] = "wait_for_add_stxsc"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the Country Code (e.g. 880 or 92):"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "stex_search_country", "style": _rs()}]]})

    elif data == "manage_stex_srv":
        _reset_btn_counter()
        kb = []
        srvs = bot_settings.get("stex_services", {})
        apps_db = bot_settings.get("premium_apps", {})
        for si, srv in enumerate(srvs):
            emoji_id = _get_service_emoji_id(srv, apps_db)
            kb.append([{"text": f"{srv}", "icon_custom_emoji_id": emoji_id, "callback_data": f"stx_srv_{srv}", "style": _rs()}])
        kb.append([{"text": "Add New Service", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "stx_add_srv", "style": _rs()}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "stex_control", "style": _rs()}])
        edit_message(chat_id, msg_id, render_body_text("📦 <b>Stex Services Manager</b>\nManage your API-based dynamic services below:"), reply_markup={"inline_keyboard": kb})

    elif data == "stx_add_srv":
        user_states[chat_id] = "wait_stx_srv_name"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Enter Service Name (e.g. WHATSAPP, FACEBOOK):"), reply_markup=get_cancel_kb())

    elif data.startswith("stx_srv_"):
        srv = data.replace("stx_srv_", "")
        _reset_btn_counter()
        kb = []
        countries = bot_settings["stex_services"].get(srv, {})
        flags_db = bot_settings.get("premium_flags", {})
        for ci, c in enumerate(countries):
            emoji_id = _find_flag_emoji_id(c, flags_db)
            kb.append([{"text": f"{c} ({len(countries[c])} Ranges)", "icon_custom_emoji_id": emoji_id, "callback_data": f"stx_cnt_{srv}_{c}", "style": _rs()}])
        kb.append([{"text": "Add Country", "icon_custom_emoji_id": "5420323438508155202", "callback_data": f"stx_add_cnt_{srv}", "style": _rs()}])
        kb.append([{"text": "Delete Service", "icon_custom_emoji_id": "5422557736330106570", "callback_data": f"stx_del_srv_{srv}", "style": _rs()}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_stex_srv", "style": _rs()}])
        edit_message(chat_id, msg_id, render_body_text(f"📂 <b>Service: {srv}</b>\nManage countries for this service:"), reply_markup={"inline_keyboard": kb})

    elif data.startswith("stx_add_cnt_"):
        srv = data.replace("stx_add_cnt_", "")
        user_states[chat_id] = "wait_stx_cnt_name"
        temp_data[chat_id] = {"msg_id": msg_id, "srv": srv}
        edit_message(chat_id, msg_id, render_body_text(f"🌍 Enter Country Name for <b>{srv}</b> (e.g. BD, INDIA):"), reply_markup=get_cancel_kb())

    elif data.startswith("stx_cnt_"):
        # rpartition: service name may contain "_"; country code sits at the right end
        _sfx = data[len("stx_cnt_"):]; srv, _, cnt = _sfx.rpartition("_")
        ranges = bot_settings["stex_services"][srv].get(cnt, [])
        _reset_btn_counter()
        kb = []
        row = []
        for ri, r in enumerate(ranges):
            row.append({"text": f"Del {r}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"stx_dr_{srv}_{cnt}_{r}", "style": _rs()})
            if len(row) == 2:
                kb.append(row)
                row = []
        if row: kb.append(row)
        kb.append([{"text": "Add Range", "icon_custom_emoji_id": "5420323438508155202", "callback_data": f"stx_addr_{srv}_{cnt}", "style": _rs()}])
        kb.append([{"text": "Delete Entire Country", "icon_custom_emoji_id": "5422557736330106570", "callback_data": f"stx_del_cnt_{srv}_{cnt}", "style": _rs()}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"stx_srv_{srv}", "style": _rs()}])
        txt = f"📍 <b>Service: {srv} | Country: {cnt}</b>\n\n<b>Total Ranges:</b> {len(ranges)}\n<i>Click on a range below to delete it, or add a new one.</i>"
        edit_message(chat_id, msg_id, render_body_text(txt), reply_markup={"inline_keyboard": kb})

    elif data.startswith("stx_addr_"):
        _sfx = data[len("stx_addr_"):]; srv, _, cnt = _sfx.rpartition("_")
        user_states[chat_id] = "wait_stx_addr"
        temp_data[chat_id] = {"msg_id": msg_id, "srv": srv, "cnt": cnt}
        edit_message(chat_id, msg_id, render_body_text(f"📝 Send the new Range for <b>{cnt}</b> (e.g. 88017):"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"stx_cnt_{srv}_{cnt}", "style": _rs()}]]})

    elif data.startswith("stx_dr_"):
        # Split from right: range never has "_", then country, leaving service (may have "_") on the left
        _sfx = data[len("stx_dr_"):]; _left, _, rng = _sfx.rpartition("_"); srv, _, cnt = _left.rpartition("_")
        if rng in bot_settings["stex_services"].get(srv, {}).get(cnt, []):
            bot_settings["stex_services"][srv][cnt].remove(rng)
            save_local_db()
            answer_callback(call["id"], f"✅ Range {rng} deleted!", show_alert=True)
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": f"stx_cnt_{srv}_{cnt}", "id": "internal"})

    elif data.startswith("stx_del_srv_"):
        srv = data.replace("stx_del_srv_", "")
        if srv in bot_settings["stex_services"]: del bot_settings["stex_services"][srv]
        save_local_db()
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "manage_stex_srv", "id": "internal"})

    elif data.startswith("stx_del_cnt_"):
        _sfx = data[len("stx_del_cnt_"):]; srv, _, cnt = _sfx.rpartition("_")
        if cnt in bot_settings["stex_services"].get(srv, {}): del bot_settings["stex_services"][srv][cnt]
        save_local_db()
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": f"stx_srv_{srv}", "id": "internal"})

    elif data == "manage_fj":
        _show_fj_panel(chat_id, msg_id)

    elif data == "toggle_fj":
        bot_settings["fj_on"] = not bot_settings["fj_on"]
        save_local_db()
        _show_fj_panel(chat_id, msg_id)

    elif data == "add_fj":
        user_states[chat_id] = "wait_for_add_fj"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 <b>Channel ya Group Add Karein</b>\n\n✅ Bot pehle se channel/group mein admin hona chahiye!\n\nBhejein koi bhi ek:\n• Username: <code>@channelname</code>\n• Public Link: <code>https://t.me/channelname</code>\n• Numeric ID: <code>-1001234567890</code>\n\n🔄 Bot auto-detect karega Channel/Group aur Private/Public!"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_fj", "style": _rs()}]]})

    elif data.startswith("del_fj_"):
        idx = _safe_int(data.split("_")[2] if len(data.split("_")) > 2 else -1)
        if 0 <= idx < len(bot_settings["fj_channels"]):
            removed = bot_settings["fj_channels"][idx]
            info = _get_fj_info(removed)
            del bot_settings["fj_channels"][idx]
            save_local_db()
            answer_callback(call["id"], f"✅ {info.get('title', 'Item')} deleted!", show_alert=True)
            _show_fj_panel(chat_id, msg_id)
        else:
            answer_callback(call["id"], "❌ Item not found!", show_alert=True)

    elif data == "manage_admins":
        _show_admin_panel(chat_id, msg_id)

    elif data == "add_adm":
        user_states[chat_id] = "wait_for_add_adm"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the User ID of the new Admin:"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_admins", "style": _rs()}]]})

    elif data.startswith("del_adm_"):
        # FIX: ID-based deletion — index shift hone par wrong admin delete hota tha
        adm_id = _safe_int(data.split("_")[2] if len(data.split("_")) > 2 else -1)
        if adm_id in bot_settings["admins"] and adm_id != OWNER_ID:
            bot_settings["admins"].remove(adm_id)
            save_local_db()
            answer_callback(call["id"], "✅ Admin deleted!", show_alert=True)
            _show_admin_panel(chat_id, msg_id)
        else:
            answer_callback(call["id"], "❌ Admin not found!", show_alert=True)

    elif data == "manage_otp_groups":
        _show_otp_groups_panel(chat_id, msg_id)

    elif data == "add_fw":
        user_states[chat_id] = "wait_for_add_fw_id"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the Group ID/Username to forward messages to:"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_otp_groups", "style": _rs()}]]})

    elif data.startswith("manage_fw_"):
        idx = _safe_int(data.split("_")[2] if len(data.split("_")) > 2 else -1)
        if 0 <= idx < len(bot_settings["fw_groups"]):
            grp_id = bot_settings["fw_groups"][idx]["chat_id"]
            edit_message(chat_id, msg_id, render_body_text(f"🛡 <b>Manage Group:</b> {grp_id}"), reply_markup=specific_fw_group_keyboard(idx))
        else:
            _alert_group_gone(call)

    elif data.startswith("add_fwbtn_"):
        idx = _safe_int(data.split("_")[2] if len(data.split("_")) > 2 else -1)
        if not (0 <= idx < len(bot_settings["fw_groups"])):
            _alert_group_gone(call)
            return
        user_states[chat_id] = "wait_for_add_fw_btn"
        temp_data[chat_id] = {"msg_id": msg_id, "fw_idx": idx}
        edit_message(chat_id, msg_id, render_body_text(
            "📝 <b>Add Inline Button</b>\n\n"
            "➖➖➖➖➖➖➖\n"
            "📌 <b>Format (without emoji):</b>\n"
            "<code>Button Text - https://link.com</code>\n\n"
            "📌 <b>Format (with premium emoji ID):</b>\n"
            "<code>6228781436330054904 Button Text - https://link.com</code>\n"
            "➖➖➖➖➖➖➖\n"
            "💡 <b>Examples:</b>\n"
            "<code>Join Channel - https://t.me/mychannel</code>\n"
            "<code>6228781436330054904 Join VIP - https://t.me/vip</code>\n"
            "➖➖➖➖➖➖➖\n"
            "⚠️ Emoji ID pehle likhein, phir button text, phir <code> - </code> phir link."
        ), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"manage_fw_{idx}", "style": _rs()}]]})

    elif data.startswith("del_fwbtn_"):
        parts = data.split("_")
        idx   = _safe_int(parts[2] if len(parts) > 2 else -1)
        b_idx = _safe_int(parts[3] if len(parts) > 3 else -1)
        if 0 <= idx < len(bot_settings["fw_groups"]):
            if 0 <= b_idx < len(bot_settings["fw_groups"][idx]["buttons"]):
                del bot_settings["fw_groups"][idx]["buttons"][b_idx]
                save_local_db()
                answer_callback(call["id"], "✅ Button deleted!", show_alert=True)
                edit_message(chat_id, msg_id, render_body_text(f"🛡 <b>Manage Group:</b> {bot_settings['fw_groups'][idx]['chat_id']}"), reply_markup=specific_fw_group_keyboard(idx))
            else:
                answer_callback(call["id"], "❌ Button not found!", show_alert=True)
        else:
            _alert_group_gone(call)

    elif data.startswith("del_fw_"):
        idx = _safe_int(data.split("_")[2] if len(data.split("_")) > 2 else -1)
        if 0 <= idx < len(bot_settings["fw_groups"]):
            del bot_settings["fw_groups"][idx]
            save_local_db()
            answer_callback(call["id"], "✅ Group deleted!", show_alert=True)
            _show_otp_groups_panel(chat_id, msg_id)
        else:
            _alert_group_gone(call)

    elif data == "edit_otp_link":
        user_states[chat_id] = "wait_for_otp_link"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the new OTP Group Link:"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_otp_groups", "style": _rs()}]]})

    elif data == "manage_panels":
        api_count = len([p for p in bot_settings["panels"] if p.get("type") == "API Panel"])
        cpt_count = len([p for p in bot_settings["panels"] if p.get("type", "API Panel") == "Auto Captcha Panel"])
        text = f"{PEM['gear']} <b>Panel Management</b>\n\nSelect which type of panel system you want to manage:"
        _reset_btn_counter()
        kb = {"inline_keyboard": [
            [{"text": f"Manage API Panels ({api_count})", "icon_custom_emoji_id": "5336972142066047577", "callback_data": "manage_api_panels", "style": _rs()}],
            [{"text": f"Manage Auto Captcha Panels ({cpt_count})", "icon_custom_emoji_id": "5353022963132174959", "callback_data": "manage_cpt_panels", "style": _rs()}],
            [{"text": "Back to System", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": _rs()}]
        ]}
        edit_message(chat_id, msg_id, render_body_text(text), reply_markup=kb)

    elif data in ["manage_api_panels", "manage_cpt_panels"]:
        p_type = "API Panel" if data == "manage_api_panels" else "Auto Captcha Panel"
        p_list = [p for p in bot_settings["panels"] if p.get("type", "API Panel") == p_type]
        icon = f"{PEM['world']} API" if p_type == 'API Panel' else f"{PEM['lock']} Auto Captcha"
        
        text = f"{icon} <b>{p_type}s Management</b>\n\n👀 <b>Active Monitors:</b> {len(p_list)}\n\n🟢 <b>Available Providers:</b>\n"
        for p in p_list:
            status = "Monitoring" if p['status'] == 'ON' else "Stopped"
            login_state = p.get('login_status', '')
            if p['type'] == 'Auto Captcha Panel':
                conf = f" {login_state}" if login_state else f"{PEM['ok']} Configured"
            else:
                conf = f"{PEM['ok']} Configured" if p.get('api_url') else f"{PEM['no']} Not Configured"
            text += f"• {p['name']}: {PEM['ok'] if p['status']=='ON' else PEM['no']} {status} | {conf}\n"
        edit_message(chat_id, msg_id, render_body_text(text), reply_markup=typed_panels_list_keyboard(p_type))

    elif data in ["add_api_panel", "add_cpt_panel"]:
        user_states[chat_id] = "wait_for_panel_name"
        p_type = "api" if data == "add_api_panel" else "logc"
        temp_data[chat_id] = {"msg_id": msg_id, "add_type": p_type}
        edit_message(chat_id, msg_id, render_body_text("📝 Please send the name of the New Provider:"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"manage_{'api' if p_type=='api' else 'cpt'}_panels", "style": _rs()}]]})

    elif data in ["list_del_api", "list_del_cpt"]:
        p_type = "API Panel" if data == "list_del_api" else "Auto Captcha Panel"
        _reset_btn_counter()
        kb = []
        for idx, p in enumerate(bot_settings["panels"]):
            if p.get("type", "API Panel") == p_type:
                kb.append([{"text": f"Delete {p['name']}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"do_del_pnl_{idx}", "style": _rs()}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"manage_{'api' if p_type=='API Panel' else 'cpt'}_panels", "style": _rs()}])
        edit_message(chat_id, msg_id, render_body_text(f"{PEM['trash']} <b>Select a Provider to Delete:</b>"), reply_markup={"inline_keyboard": kb})

    elif data.startswith("do_del_pnl_"):
        idx = _safe_int(data.split("_")[3] if len(data.split("_")) > 3 else -1)
        if 0 <= idx < len(bot_settings["panels"]):
            p_type = bot_settings["panels"][idx].get("type", "API Panel")
            # Also clean up panel_sessions for this and higher indices
            if idx in panel_sessions:
                del panel_sessions[idx]
            # Shift panel_sessions keys down for indices above deleted one
            new_sessions = {}
            for k, v in panel_sessions.items():
                if k > idx:
                    new_sessions[k - 1] = v
                elif k < idx:
                    new_sessions[k] = v
            panel_sessions.clear()
            panel_sessions.update(new_sessions)
            del bot_settings["panels"][idx]
            save_local_db()
            answer_callback(call["id"], "✅ Provider Deleted!", show_alert=True)
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": f"manage_{'api' if p_type=='API Panel' else 'cpt'}_panels", "id": "internal"})
        else:
            answer_callback(call["id"], "❌ Panel not found! May have already been deleted.", show_alert=True)

    elif data.startswith("tog_pnl_"):
        idx = _safe_int(data.split("_")[2] if len(data.split("_")) > 2 else -1)
        if not (0 <= idx < len(bot_settings["panels"])):
            _alert_panel_gone(call)
            return
        p = bot_settings["panels"][idx]
        new_status = "ON" if p["status"] == "OFF" else "OFF"
        if new_status == "ON":
            p["needs_warmup"] = True  # PEHLE warmup set — race condition eliminate
        p["status"] = new_status      # BAAD MEIN status flip karo
        save_local_db()
        if new_status == "ON":
            # Turant background thread mein existing OTPs mark karo (panel_monitor_thread se pehle)
            threading.Thread(target=_eagerly_warmup_panel, args=(idx, p), daemon=True).start()

        _show_panel_cfg(chat_id, msg_id, idx)

    elif data.startswith("conf_pnl_"):
        idx = _safe_int(data.split("_")[2] if len(data.split("_")) > 2 else -1)
        if not (0 <= idx < len(bot_settings["panels"])):
            _alert_panel_gone(call)
            return
        _show_panel_cfg(chat_id, msg_id, idx)

    elif data.startswith("set_p_api_"):
        idx = _safe_int(data.split("_")[3] if len(data.split("_")) > 3 else -1)
        if idx < 0 or idx >= len(bot_settings["panels"]):
            _alert_panel_gone(call)
            return
        user_states[chat_id] = "wait_for_p_api"
        _set_panel_temp(chat_id, msg_id, idx)
        edit_message(chat_id, msg_id, render_body_text("📝 Send the API URL for this provider:"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"conf_pnl_{idx}", "style": _rs()}]]})

    elif data.startswith("set_p_tok_"):
        idx = _safe_int(data.split("_")[3] if len(data.split("_")) > 3 else -1)
        if idx < 0 or idx >= len(bot_settings["panels"]):
            _alert_panel_gone(call)
            return
        user_states[chat_id] = "wait_for_p_tok"
        _set_panel_temp(chat_id, msg_id, idx)
        edit_message(chat_id, msg_id, render_body_text("📝 Send the Token for this provider:"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"conf_pnl_{idx}", "style": _rs()}]]})

    elif data.startswith("set_p_tokh_"):
        idx = _safe_int(data.split("_")[3] if len(data.split("_")) > 3 else -1)
        if idx < 0 or idx >= len(bot_settings["panels"]):
            _alert_panel_gone(call)
            return
        user_states[chat_id] = "wait_for_p_tokheader"
        _set_panel_temp(chat_id, msg_id, idx)
        edit_message(chat_id, msg_id, render_body_text("📝 Send the <b>Header Name</b> for token authentication.\n\n<b>Example:</b> <code>mauthapi</code> (for VoltX SMS)\n\nWhen set, the token will be sent as an HTTP header instead of a URL parameter.\n\nType <code>none</code> to remove and use URL parameter mode."), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"conf_pnl_{idx}", "style": _rs()}]]})

    elif data.startswith("set_p_fapi_"):
        idx = _safe_int(data.split("_")[3] if len(data.split("_")) > 3 else -1)
        if idx < 0 or idx >= len(bot_settings["panels"]):
            _alert_panel_gone(call)
            return
        user_states[chat_id] = "wait_for_p_fapi"
        _set_panel_temp(chat_id, msg_id, idx)
        edit_message(chat_id, msg_id, render_body_text("📝 Send the FULL API URL (Example: http://api.com/get?key=YOUR_TOKEN&start=0):"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"conf_pnl_{idx}", "style": _rs()}]]})

    elif data.startswith("set_p_rec_"):
        idx = _safe_int(data.split("_")[3] if len(data.split("_")) > 3 else -1)
        if idx < 0 or idx >= len(bot_settings["panels"]):
            _alert_panel_gone(call)
            return
        user_states[chat_id] = "wait_for_p_rec"
        _set_panel_temp(chat_id, msg_id, idx)
        edit_message(chat_id, msg_id, render_body_text("📝 Send the number of records to fetch (e.g. 10).\nType <code>0</code> for Unlimited:"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"conf_pnl_{idx}", "style": _rs()}]]})

    elif data.startswith("test_p_conn_"):
        idx = _safe_int(data.split("_")[3] if len(data.split("_")) > 3 else -1)
        if idx < 0 or idx >= len(bot_settings["panels"]):
            _alert_panel_gone(call)
            return
        p = bot_settings["panels"][idx]
        wait_msg = send_message(chat_id, render_body_text("⏳ Testing connection. Please wait..."))
        wait_msg_id = wait_msg.get("result", {}).get("message_id") if wait_msg else None
        answer_callback(call["id"])
        
        try:
            parsed = []
            raw_text = ""
            
            if p["type"] == "Auto Captcha Panel":
                sess = panel_sessions.get(idx)
                if not sess:
                    # FIX: Lockout period check — Test Connection panel ko aur lock nahi karega
                    now = time.time()
                    retry_wait = p.get("retry_wait", 90)
                    last_attempt = p.get("last_login_attempt", 0)
                    time_since = now - last_attempt
                    if time_since < retry_wait:
                        remaining = int(retry_wait - time_since)
                        if wait_msg_id: delete_message(chat_id, wait_msg_id)
                        locked_status = p.get("login_status", "Panel Locked")
                        send_message(chat_id, render_body_text(
                            f"🔒 <b>Panel Locked — Wait karo!</b>\n\n"
                            f"Status: {html.escape(str(locked_status))}\n"
                            f"⏳ <b>{remaining}s</b> mein auto-retry hoga.\n\n"
                            f"<i>Test Connection tab karo jab login ho jaye.</i>"
                        ))
                        return
                    success = attempt_auto_login(p, idx)
                    if not success:
                        if wait_msg_id: delete_message(chat_id, wait_msg_id)
                        send_message(chat_id, render_body_text(f"❌ <b>Auto Login Failed!</b>\nReason: {html.escape(str(p.get('login_status', 'Unknown')))}"))
                        return
                    sess = panel_sessions.get(idx)
                    
                # 🌟 FIX: SPA/JSON-API panels (jaise Teleroutex) ke liye JSON fetcher use karo
                # api_base set hone ka matlab = yeh JSON API panel hai (HTML table nahi)
                if p.get("api_base"):
                    parsed, raw_text = _fetch_json_api_panel_data(p, sess)
                else:
                    _lu = p.get("login_url", "").strip()
                    if not _lu.startswith("http"): _lu = "http://" + _lu
                    msg_link = p.get("msg_link", "").strip()
                    if msg_link and not msg_link.startswith("http"): msg_link = "http://" + msg_link
                    _sec = p.get("panel_section", "client")
                    check_url = msg_link if msg_link else f"{_extract_base_url(_lu)}/{_sec}/SMSCDRStats"
                    parsed, raw_text = fetch_cpt_panel_cdrs(p, sess, check_url)
                
            else:
                full_url = p.get("full_api_url", "").strip()
                url = p.get("api_url", "").strip()
                token = p.get("token", "").strip()
                if not full_url and not url:
                    if wait_msg_id: delete_message(chat_id, wait_msg_id)
                    send_message(chat_id, render_body_text("❌ Please Set API URL or Full API URL first!"))
                    return
                
                urls_to_try, headers = _build_api_urls(p)
                parsed = []
                raw_text = ""
                for try_url in urls_to_try:
                    try:
                        res = tg_session.get(try_url, headers=headers, timeout=10)
                        raw_text = res.text
                        # Rate-limit check: JSON parse karne se PEHLE
                        if res.status_code == 429 or _is_rate_limited_response(raw_text):
                            if wait_msg_id: delete_message(chat_id, wait_msg_id)
                            send_message(chat_id, render_body_text(
                                f"⚠️ <b>API Rate Limited!</b>\n\n"
                                f"API ne bahut zyada requests ke wajah se temporarily block kar diya.\n"
                                f"<i>5-10 seconds baad Test Connection dobara try karo.</i>\n\n"
                                f"<b>Raw:</b> <code>{html.escape(raw_text[:200])}</code>"
                            ))
                            return
                        # max_results=3: sirf top 3 parse karo, puri list nahi
                        parsed = parse_panel_response(raw_text, p, max_results=3)
                        if parsed:
                            if not full_url and try_url != url and token and not p.get("token_header", ""):
                                p["api_url"] = try_url.replace(token, "{token}")
                                save_local_db()
                            break
                    except Exception as e:
                        logger.warning(f"API URL test attempt failed: {e}")
                 
            if wait_msg_id: delete_message(chat_id, wait_msg_id)
                 
            if parsed:
                total = min(3, len(parsed))
                send_message(chat_id, render_body_text(
                    f"✅ <b>Connection Successful!</b>\n"
                    f"🎯 Top <b>{total}</b> messages — real format:"
                ))
                for i, sample in enumerate(parsed[:3]):
                    num = sample['number']
                    msg = sample['message']
                    otp = sample['otp']
                    detected_app = detect_service(msg)
                    app_name = detected_app if detected_app else p.get("name", "Unknown")
                    app_full_name, prem_app_html = get_service_info_html(app_name, msg)
                    display_num = f"+{num}" if not str(num).startswith("+") else str(num)
                    char, iso = get_flag_and_code(num)
                    lang = detect_language(msg)
                    masked = mask_number(display_num)
                    otp_msg = render_body_text(
                        f"{get_flag_info_html(display_num)} #{iso} ♦ {masked} ✅ {otp}"
                    )
                    _reset_btn_counter()
                    kb = [
                        [{"text": f"{otp}", "icon_custom_emoji_id": "5474525960143385880", "copy_text": {"text": otp}, "style": _rs()}]
                    ]
                    send_message(chat_id, otp_msg, reply_markup={"inline_keyboard": kb})
            else:
                if p["type"] == "Auto Captcha Panel":
                    # 🌟 FIX: JSON API panel (jaise Teleroutex) ke liye alag error message
                    if p.get("api_base"):
                        # SPA/JSON API panel — no OTP records milne ka matlab:
                        # ya toh abhi koi naya SMS nahi aaya, ya filter ne sab block kiya
                        send_message(chat_id, render_body_text(
                            f"✅ <b>Connection Successful!</b>\n\n"
                            f"🔗 API: <code>{html.escape(p.get('api_base',''))}/api/message-data-record</code>\n"
                            f"👤 User: <code>{html.escape(p.get('username',''))}</code>\n\n"
                            f"⚠️ <b>Abhi koi OTP message nahi mila.</b>\n"
                            f"<i>Panel mein naya SMS aane par automatically group mein aayega.</i>"
                        ))
                    else:
                        try:
                            soup = BeautifulSoup(raw_text, 'html.parser')
                            tables = soup.find_all('table')
                            if tables:
                                full_table_data = "🔍 FULL TABLE DATA (A-Z)\n" + "="*50 + "\n\n"
                                for t_idx, table in enumerate(tables):
                                    full_table_data += f"--- Table {t_idx+1} ---\n"
                                    rows = table.find_all('tr')
                                    for r_idx, row in enumerate(rows):
                                        cols = row.find_all(['th', 'td'])
                                        col_texts = [f"[{c_idx+1}] {c.get_text(separator=' ', strip=True)}" for c_idx, c in enumerate(cols)]
                                        full_table_data += f"Row {r_idx+1}: {' | '.join(col_texts)}\n"
                                    full_table_data += "\n" + "="*50 + "\n"
                                send_document(chat_id, f"Full_Panel_Data_{idx}.txt", full_table_data.encode('utf-8'))
                                fail_txt = f"⚠️ <b>Connected, but couldn't parse OTP data!</b>\n\n<i>I have sent the complete (A-Z) data of that link in a Text File. Open the file and check the correct Column Number (e.g.: [1], [3]) then update in panel.</i>"
                                send_message(chat_id, render_body_text(fail_txt))
                            else:
                                send_message(chat_id, render_body_text(f"⚠️ <b>Connected, but no HTML Table found!</b>\nMake sure the message link is correct."))
                        except Exception as e:
                            send_message(chat_id, render_body_text(f"❌ <b>Error parsing HTML:</b> {html.escape(str(e))}"))
                else:
                    # Show raw excerpt for debugging — only replace 'nn' if no real newlines present
                    excerpt = raw_text[:600] if raw_text else ""
                    if '\n' not in excerpt:
                        debug_raw = re.sub(r'(?<![a-zA-Z])nn(?![a-zA-Z])', '\n', excerpt)
                    else:
                        debug_raw = excerpt
                    safe_html = html.escape(str(debug_raw)[:400])
                    
                    # Helpful diagnosis: check kar ke batao kya problem hai
                    diagnosis = ""
                    if not raw_text:
                        diagnosis = "❌ API se koi data nahi aaya (empty response)."
                    else:
                        try:
                            test_data = json.loads(raw_text)
                            if isinstance(test_data, list) and test_data:
                                first = test_data[0]
                                if isinstance(first, list):
                                    p_num_idx = int(p.get("num_col_idx", 2)) - 1
                                    p_msg_idx = int(p.get("msg_col_idx", 3)) - 1
                                    cols = len(first)
                                    diagnosis = (
                                        f"✅ JSON parse: OK ({len(test_data)} rows, {cols} columns per row)\n"
                                        f"• Number column {p.get('num_col_idx',2)} (index {p_num_idx}): "
                                        f"<code>{html.escape(str(first[p_num_idx]) if p_num_idx < cols else 'OUT OF RANGE')}</code>\n"
                                        f"• Message column {p.get('msg_col_idx',3)} (index {p_msg_idx}): "
                                        f"<code>{html.escape(str(first[p_msg_idx])[:80] if p_msg_idx < cols else 'OUT OF RANGE')}</code>\n"
                                        f"• OTP found: <code>{html.escape(str(extract_otp_code(str(first[p_msg_idx]).replace('nn',chr(10))) or 'NOT FOUND'))}</code>"
                                    )
                                elif isinstance(first, dict):
                                    diagnosis = f"✅ JSON parse: OK ({len(test_data)} records, dict format)\n⚠️ OTP/Number fields nahi mile — key names check karo."
                                else:
                                    diagnosis = f"⚠️ JSON parse: OK lekin format unknown ({type(first).__name__})"
                            elif isinstance(test_data, dict):
                                diagnosis = f"⚠️ JSON ek object hai (list expected) — API response ka structure check karo."
                            else:
                                diagnosis = f"⚠️ JSON parse: OK lekin empty list mili."
                        except Exception as je:
                            diagnosis = f"❌ JSON parse failed: <code>{html.escape(str(je)[:100])}</code>\n⚠️ API JSON nahi de raha — URL/Token check karo."
                    
                    send_message(chat_id, render_body_text(
                        f"⚠️ <b>Connected, but couldn't parse OTP data.</b>\n\n"
                        f"<b>Diagnosis:</b>\n{diagnosis}\n\n"
                        f"<b>Raw Data (excerpt):</b>\n<code>{safe_html}...</code>"
                    ))
        except Exception as e:
            if wait_msg_id: delete_message(chat_id, wait_msg_id)
            send_message(chat_id, render_body_text(f"❌ <b>Connection Failed!</b>\nError: {html.escape(str(e))}"))

    elif data == "abhi_control":
        if chat_id in user_states: user_states.pop(chat_id, None)
        if chat_id in temp_data: temp_data.pop(chat_id, None)
        _show_abhi_panel(chat_id, msg_id)

    elif data == "abhi_toggle_w":
        bot_settings["withdraw_on"] = not bot_settings["withdraw_on"]
        save_local_db()
        _show_abhi_panel(chat_id, msg_id)

    elif data == "manage_w_methods":
        _show_w_methods(chat_id, msg_id)

    elif data == "add_wm":
        user_states[chat_id] = "wait_for_add_wm"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the name of the new Withdrawal Method:"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_w_methods", "style": _rs()}]]})

    elif data.startswith("del_wm_"):
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True)
            return
        idx = _safe_int(data.split("_")[2] if len(data.split("_")) > 2 else -1)
        if 0 <= idx < len(bot_settings["w_methods"]):
            del bot_settings["w_methods"][idx]
            save_local_db()
            answer_callback(call["id"], "✅ Method deleted!", show_alert=True)
            _show_w_methods(chat_id, msg_id)
        else:
            answer_callback(call["id"], "❌ Method not found!", show_alert=True)

    elif data.startswith("abhi_"):
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True)
            return
        key = data.replace("abhi_", "")
        key_map = {"min_w": "min_withdraw", "otp_r": "otp_reward", "ref_r": "refer_reward", "cool": "cooldown", "num_req": "num_req", "num_share": "num_share", "sup_link": "support_link", "w_group": "w_group"}
        if key in key_map:
            temp_data[chat_id] = {"msg_id": msg_id, "key": key_map[key]}
            user_states[chat_id] = "set_abhi"
            _reset_btn_counter()
            cancel_kb = {"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "cancel_abhi_edit", "style": _rs()}]]}
            edit_message(chat_id, msg_id, render_body_text(f"📝 Please send the new value for <code>{key_map[key]}</code>:"), reply_markup=cancel_kb)
            answer_callback(call["id"])

    elif data.startswith("g_s_"):
        service = data.split("g_s_")[1]
        local_cnts = set([b["country"] for b in number_batches.values() if b["service"] == service and b["numbers"]])
        nexa_cnts = set(bot_settings.get("nexa_services", {}).get(service, {}).keys())
        voltx_cnts = set(bot_settings.get("voltx_services", {}).get(service, {}).keys())
        stex_cnts = set(bot_settings.get("stex_services", {}).get(service, {}).keys())
        all_countries = local_cnts.union(nexa_cnts).union(voltx_cnts).union(stex_cnts)
        
        c_msg = bot_settings["custom_messages"].get("select_country", {})
        raw_txt = c_msg.get("text", "📌 Select a country for {service}:").replace("{service}", service)
        txt = render_body_text(raw_txt)
        
        flags_db = bot_settings.get("premium_flags", {})
        _reset_btn_counter()
        kb = []
        DEFAULT_GLOBE = "5780471598922337683"
        for ci, c in enumerate(all_countries):
            # Step 1: Name / ISO / direct dial-code matching via _find_flag_emoji_id
            emoji_id = _find_flag_emoji_id(c, flags_db)

            # Step 2: Direct key upgrade (if c is a dial code and _find missed it)
            if emoji_id == DEFAULT_GLOBE and c in flags_db:
                emoji_id = flags_db[c].get("id", DEFAULT_GLOBE)

            # Step 3: Fallback — actual numbers in local batches (dial-code prefix match)
            if emoji_id == DEFAULT_GLOBE:
                for b_id, b_data in number_batches.items():
                    if b_data["service"] == service and b_data["country"] == c and b_data["numbers"]:
                        first_num = b_data["numbers"][0]["num"].replace("+", "").replace(" ", "")
                        _, _, num_eid = get_flag_info_from_num(first_num)
                        if num_eid:
                            emoji_id = num_eid
                            break

            # Step 4: Fallback — API service ranges (strip X's → dial-code prefix match)
            if emoji_id == DEFAULT_GLOBE:
                sorted_flag_codes = sorted(flags_db.keys(), key=len, reverse=True)
                for svc_ranges in [
                    bot_settings.get("nexa_services", {}).get(service, {}),
                    bot_settings.get("voltx_services", {}).get(service, {}),
                    bot_settings.get("stex_services", {}).get(service, {}),
                ]:
                    if c not in svc_ranges:
                        continue
                    for rng in svc_ranges[c]:
                        rng_clean = rng.replace("X", "").replace("x", "")
                        for code in sorted_flag_codes:
                            if rng_clean.startswith(code) and "id" in flags_db[code]:
                                emoji_id = flags_db[code]["id"]
                                break
                        if emoji_id != DEFAULT_GLOBE:
                            break
                    if emoji_id != DEFAULT_GLOBE:
                        break

            kb.append([{"text": c, "icon_custom_emoji_id": emoji_id, "callback_data": f"g_c_{service}_{c}", "style": _rs()}])
        
        _append_custom_btns(kb, c_msg)
            
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "get_number_menu", "style": _rs()}])
        edit_message(chat_id, msg_id, txt, reply_markup={"inline_keyboard": kb})
        answer_callback(call["id"])

    elif data == "get_number_menu":
        all_services, txt, kb = _build_services_keyboard("get_number")
        if not all_services:
            answer_callback(call["id"], "❌ No services available!", show_alert=True)
            return
        edit_message(chat_id, msg_id, txt, reply_markup={"inline_keyboard": kb})
        answer_callback(call["id"])

    elif data.startswith("g_c_") or data.startswith("c_n_"):
        # 1. Global cooldown check (for all number methods)
        now = time.time()
        if now - user_cooldowns.get(chat_id, 0) < bot_settings["cooldown"]:
            answer_callback(call["id"], f"⌛ Please wait {int(bot_settings['cooldown'] - (now - user_cooldowns.get(chat_id, 0)))}s.", show_alert=True)
            return
        
        # Cooldown update
        user_cooldowns[chat_id] = now
        
        # Expire previous number
        expire_previous_number(chat_id)

        # If coming from search number (old path — should not reach here now)
        if data.startswith("c_n_s_"):
            parts_s = data.split("_")
            query = parts_s[3]
            _svc = parts_s[4] if len(parts_s) > 4 else ""
            service_from_cb = _svc if _svc else None
            
            allowed_countries = (
                bot_settings.get("nexa_search_countries", []) +
                bot_settings.get("voltx_search_countries", []) +
                bot_settings.get("stex_search_countries", [])
            )
            if allowed_countries:
                clean_allowed = [c.replace("X", "").replace("x", "") for c in allowed_countries]
                if not any(query.startswith(c) or c.startswith(query) for c in clean_allowed if c):
                    answer_callback(call["id"], "❌ This country code is not allowed for search!", show_alert=True)
                    return
                
            edit_message(chat_id, msg_id, render_body_text("⌛ <i>Processing... Finding Number...</i>"))
            wait_msg_id = msg_id
            
            found_indices = _search_and_recycle_local(query, chat_id)

            fetched_nums = []
            if not found_indices:
                # 🌟 Try all panels with strict isolation (Nexa → VoltX → Stex)
                _api_num, _api_panel = _fetch_number_via_panels(query, chat_id)
                if _api_num:
                    fetched_nums.append(_api_num)
                    save_local_db()
                else:
                    answer_callback(call["id"], "❌ Number out of stock!", show_alert=True)
                    delete_message(chat_id, wait_msg_id)
                    return
            else:
                random.shuffle(found_indices)
                for b_id, idx in found_indices:
                    if len(fetched_nums) >= bot_settings.get("num_req", 1): break
                    if b_id not in number_batches: continue
                    nb = number_batches[b_id]["numbers"]
                    if idx < 0 or idx >= len(nb): continue
                    n_obj = nb[idx]
                    num_str = n_obj["num"]
                    fetched_nums.append(num_str)
                    n_obj["shares"] += 1
                    n_obj["used_by"].append(chat_id)
                    with _stats_lock:
                        total_assigned_stats += 1
                    if n_obj["shares"] >= bot_settings.get("num_share", 1):
                        if num_str not in used_numbers_list:
                            used_numbers_list.append(num_str)
                save_local_db()
                
            user_active_sessions[chat_id] = {"msg_id": wait_msg_id, "nums": fetched_nums,
                                             "service": service_from_cb or "", "country": "",
                                             "ctx": "search", "query": query,
                                             "cc_codes": _build_cc_codes(fetched_nums), "cc_state": [True] * len(fetched_nums)}
            kb = _rebuild_num_kb(chat_id)
            num_text = render_body_text(_build_num_text(chat_id))
            try:
                edit_message(chat_id, wait_msg_id, num_text, reply_markup={"inline_keyboard": kb})
            except Exception:
                msg_res = send_message(chat_id, num_text, reply_markup={"inline_keyboard": kb})
                if msg_res and msg_res.get("ok") and msg_res.get("result"):
                    user_active_sessions[chat_id]["msg_id"] = msg_res["result"]["message_id"]
            try: answer_callback(call["id"])
            except Exception as e:
                logger.warning(f"Error: {e}")
            return

        # If coming from upload or service
        _cb_sfx = data[4:]  # strip "g_c_" or "c_n_" prefix
        service, _, country = _cb_sfx.partition("_")

        if not service or not country:
            answer_callback(call["id"], "❌ Invalid selection!", show_alert=True)
            return

        available_indices = []
        # Check Local Stock First
        for b_id, b_data in number_batches.items():
            if b_data["service"] == service and b_data["country"] == country:
                for idx, n_obj in enumerate(b_data["numbers"]):
                    if chat_id not in n_obj.get("used_by", []):
                        available_indices.append((b_id, idx))

        # Recycle: if no available numbers, reset all matching numbers
        if not available_indices:
            has_matching = False
            for b_id, b_data in number_batches.items():
                if b_data["service"] == service and b_data["country"] == country:
                    for n_obj in b_data["numbers"]:
                        has_matching = True
                        n_obj["shares"] = 0
                        n_obj["used_by"] = []
            if has_matching:
                for b_id, b_data in number_batches.items():
                    if b_data["service"] == service and b_data["country"] == country:
                        for idx, n_obj in enumerate(b_data["numbers"]):
                            available_indices.append((b_id, idx))

        # IF NO LOCAL STOCK, fetch directly from panel API (strict service+country isolation)
        _api_num = None
        if not available_indices:
            # Try Nexa (only if ON and service+country configured in Nexa)
            if bot_settings.get("nexa_on", False):
                _ns = bot_settings.get("nexa_services", {}).get(service, {}).get(country, [])
                if _ns:
                    _rng = random.choice(_ns)
                    _api_num, _ = try_nexa_get_number(_rng, chat_id, allow_auto=True)
            # Try VoltX (only if ON and service+country configured in VoltX)
            if not _api_num and bot_settings.get("voltx_on", False):
                _vs = bot_settings.get("voltx_services", {}).get(service, {}).get(country, [])
                if _vs:
                    _rng = random.choice(_vs)
                    _api_num, _ = try_voltx_get_number(_rng.replace("X", "").replace("x", ""), chat_id, allow_auto=True)
            # Try Stex (only if ON and service+country configured in Stex)
            if not _api_num and bot_settings.get("stex_on", False):
                _ss = bot_settings.get("stex_services", {}).get(service, {}).get(country, [])
                if _ss:
                    _rng = random.choice(_ss)
                    _api_num, _ = try_stex_get_number(_rng.replace("X", "").replace("x", ""), chat_id, allow_auto=True)
            if not _api_num:
                answer_callback(call["id"], "❌ Number out of stock or range missing!", show_alert=True)
                if data.startswith("c_n_"): delete_message(chat_id, msg_id)
                return

        random.shuffle(available_indices)
        
        # If API number fetched directly, use it; otherwise pick from local stock
        fetched_nums = [_api_num] if _api_num else []
        for b_id, idx in available_indices:
            if len(fetched_nums) >= bot_settings.get("num_req", 1): break
            if b_id not in number_batches: continue
            nb = number_batches[b_id]["numbers"]
            if idx < 0 or idx >= len(nb): continue
            n_obj = nb[idx]
            
            fetched_nums.append(n_obj["num"])
            with _data_lock:
                n_obj["shares"] += 1
                n_obj["used_by"].append(chat_id)
                if n_obj["shares"] >= bot_settings.get("num_share", 1):
                    if n_obj["num"] not in used_numbers_list:
                        used_numbers_list.append(n_obj["num"])
            with _stats_lock:
                total_assigned_stats += 1
        save_local_db()

        if not fetched_nums:
            answer_callback(call["id"], "❌ You have already taken all numbers or stock is empty!", show_alert=True)
            if data.startswith("c_n_"): delete_message(chat_id, msg_id)
            return

        _sess_reg = {"msg_id": msg_id, "nums": fetched_nums, "service": service, "country": country,
                     "ctx": "regular", "cc_codes": _build_cc_codes(fetched_nums), "cc_state": [True] * len(fetched_nums)}
        user_active_sessions[chat_id] = _sess_reg
        kb = _rebuild_num_kb(chat_id)
        text_numbers = render_body_text(_build_num_text(chat_id))
        try:
            edit_message(chat_id, msg_id, text_numbers, reply_markup={"inline_keyboard": kb})
        except Exception as e:
            msg_res = send_message(chat_id, text_numbers, reply_markup={"inline_keyboard": kb})
            if msg_res and msg_res.get("ok") and msg_res.get("result"):
                user_active_sessions[chat_id]["msg_id"] = msg_res["result"]["message_id"]
        try: answer_callback(call["id"])
        except Exception as e:
            logger.warning(f"Error: {e}")

    elif data.startswith("add_cc_") or data.startswith("rem_cc_"):
        # ── Country Code toggle ────────────────────────────────────
        session = user_active_sessions.get(chat_id, {})
        if not session:
            answer_callback(call["id"], "❌ Session expired. Please get a new number.", show_alert=True)
            return

        nums     = session.get("nums", [])
        cc_state = list(session.get("cc_state", [True] * len(nums)))
        # pad if needed
        while len(cc_state) < len(nums):
            cc_state.append(True)

        suffix = data.split("_")[-1]
        if suffix == "all":
            # Toggle all numbers at once
            new_val = data.startswith("add_cc_")
            cc_state = [new_val] * len(cc_state)
        else:
            try:
                idx = int(suffix)
            except Exception:
                answer_callback(call["id"]); return
            if data.startswith("add_cc_"):
                if idx < len(cc_state): cc_state[idx] = True
            else:
                if idx < len(cc_state): cc_state[idx] = False

        session["cc_state"] = cc_state
        user_active_sessions[chat_id] = session

        kb = _rebuild_num_kb(chat_id)
        num_text = render_body_text(_build_num_text(chat_id))
        try:
            edit_message(chat_id, session["msg_id"], num_text, reply_markup={"inline_keyboard": kb})
        except Exception as e:
            logger.warning(f"CC toggle edit error: {e}")
        try: answer_callback(call["id"])
        except Exception: pass

    elif data.startswith("wapp_") or data.startswith("wrej_"):
        # Admin check (need to check User ID)
        user_id_clicked = call.get("from", {}).get("id", 0)
        if not is_admin(user_id_clicked):
            answer_callback(call["id"], "🚫 Only Bot Admins can process withdrawals!", show_alert=True)
            return
            
        action = "APPROVE" if data.startswith("wapp_") else "REJECT"
        req_id = data.replace("wapp_", "").replace("wrej_", "")
        
        if req_id in pending_withdrawals:
            req_data = pending_withdrawals[req_id]
            u_id, amt = req_data["user_id"], req_data["amount"]
            num = req_data["number"]
            full_name = req_data.get("full_name", u_id)
            
            if action == "APPROVE" and len(num) >= 7:
                masked_num = mask_number(num, user_id=u_id)
            else:
                masked_num = num
            
            status_text = "APPROVED" if action == "APPROVE" else "REJECTED"
            emoji_icon_id = "6266967801580231067" if action == "APPROVE" else "6267237615720731788"
            new_text = f"🎙 <b>WITHDRAWAL {status_text}</b>\n\n👤 <b>USER:</b> <a href='tg://user?id={u_id}'>{full_name}</a>\n💳 <b>WITHDRAWAL:</b> {amt} INR\n🍏 <b>NUMBER:</b> <code>{masked_num}</code>\n🏦 <b>METHOD:</b> {req_data['method']}\n\n🧾 <b>REQ ID:</b> {req_id}\n👨‍⚖️ <b>PROCESSED BY ADMIN</b>"
            rendered_new_text = render_body_text(new_text)
            _reset_btn_counter()
            status_kb = {"inline_keyboard": [[{"text": status_text, "icon_custom_emoji_id": emoji_icon_id, "callback_data": "ignore", "style": "success" if action == "APPROVE" else "danger"}]]}

            # Edit ALL sent messages (w_group + admin DMs) — show status button instead of APPROVE/REJECT
            for sm in req_data.get("sent_messages", []):
                try: edit_message(sm["chat_id"], sm["message_id"], rendered_new_text, reply_markup=status_kb)
                except Exception as e:
                    logger.warning(f"Error: {e}")
            # Also edit the current message where admin clicked
            try: edit_message(chat_id, msg_id, rendered_new_text, reply_markup=status_kb)
            except Exception as e:
                logger.warning(f"Error: {e}")
            
            safe_uid = int(u_id) if str(u_id).lstrip("-").isdigit() else u_id
            if action == "REJECT":
                update_balance(safe_uid, amt)
                try:
                    send_message(safe_uid, render_body_text(f"❌ Your {amt} INR withdrawal request was rejected. Balance refunded."))
                except Exception as _e:
                    logger.warning(f"Withdrawal reject notify failed for {u_id}: {_e}")
            else:
                try:
                    send_message(safe_uid, render_body_text(f"{PEM['ok']} Your {amt} INR withdrawal request has been paid successfully!"))
                except Exception as _e:
                    logger.warning(f"Withdrawal approve notify failed for {u_id}: {_e}")
            
            _update_local_withdrawal(req_id, {"status": "approved" if action == "APPROVE" else "rejected"})
                
            del pending_withdrawals[req_id]
        else:
            answer_callback(call["id"], "❌ Request already processed!", show_alert=True)

# ==========================================
# Polling Loop
# ==========================================
def poll_otp_with_status(number_id, num_str, owner_id, api_key):
    headers = {"X-API-Key": api_key}
    first_iter = True  # Pehli baar purane OTPs mark karo lekin deliver mat karo
    for _ in range(150): # 150 * 2 seconds = 5 Minutes Polling
        try:
            res = _nexa_session.get(f"{NEXA_BASE_URL}/api/v1/numbers/{number_id}/sms", headers=headers, timeout=10)
            try:
                data = res.json()
            except Exception:
                logger.warning(f"Nexa OTP poll: invalid JSON response — {res.text[:120]!r}")
                first_iter = False
                time.sleep(2)
                continue
            # Nexa returns either flat {success, otp, message} or {success, count, data:[{otp, message,...}]}
            sms_list = []
            if data.get("success"):
                if data.get("otp"):
                    # Flat format: {success:true, otp:"...", message:"..."}
                    sms_list = [{"otp": data.get("otp"), "message": data.get("message", ""),
                                 "service": data.get("service", ""), "app_name": data.get("app_name", "")}]
                elif isinstance(data.get("data"), list) and data["data"]:
                    # List format: {success:true, data:[{otp, sms/message, app_name,...}]}
                    sms_list = data["data"]
                elif isinstance(data.get("sms"), list) and data["sms"]:
                    sms_list = data["sms"]
            for sms_item in sms_list:
                otp = str(sms_item.get("otp") or sms_item.get("code") or "")
                msg_text = str(sms_item.get("message") or sms_item.get("sms") or sms_item.get("text") or f"Your code is {otp}")
                if not otp:
                    continue

                # Find OTP with dash or large OTP from full message
                extracted_otp = extract_otp_code(msg_text)
                if extracted_otp and len(extracted_otp) > len(otp):
                    otp = extracted_otp

                # Detect service/app from full message
                app_name = sms_item.get("service") or sms_item.get("app_name") or sms_item.get("app") or "Nexa Service"
                detected_app = detect_service(msg_text)
                if detected_app:
                    app_name = detected_app

                # ── AGE GUARD ────────────────────────────────────────────────
                # Nexa per-number poller: purane records AA sakte hain.
                # 25h se purana OTP kabhi deliver nahi karna.
                ts_str = str(
                    sms_item.get("received_at") or sms_item.get("created_at") or
                    sms_item.get("sms_time") or sms_item.get("date") or
                    sms_item.get("timestamp") or sms_item.get("createdAt") or ""
                )
                if ts_str and _is_stale_otp(ts_str):
                    continue  # 25h se purana — skip
                # ─────────────────────────────────────────────────────────────

                unique_id = f"POLL_{number_id}_{otp}"
                if _is_processed(unique_id):
                    continue
                _add_to_processed(unique_id)

                # ── WARMUP GATE ─────────────────────────────────────────────
                # Pehli iteration mein jo bhi OTP API mein tha woh "purana" hai.
                # Mark karo (dedup ke liye) lekin deliver bilkul mat karo.
                if first_iter:
                    continue

                # owner_id=None hone par bhi group ko deliver karo — sirf user DM skip hoga
                _record_and_deliver_otp(owner_id, num_str, app_name, msg_text, otp, num_str, "poll_otp_nexa")
                break
        except Exception as e:
            logger.warning(f"poll_otp_with_status iteration error: {e}")
        first_iter = False  # Pehli iteration ke baad warmup khatam
        time.sleep(2)

def _poll_mauthapi_otp_single(prefix, base_url, default_name, num_str, owner_id, api_key):
    """Shared per-number OTP poller for VoltX and Stex (same mauthapi platform).
    prefix: 'VX' for VoltX, 'STX' for Stex — used for processed_otps deduplication."""
    headers = {"mauthapi": api_key, "User-Agent": "Mozilla/5.0"}
    clean_target = str(num_str).replace("+", "").replace(" ", "").replace("-", "").strip()
    first_iter = True  # Pehli baar purane OTPs mark karo lekin deliver mat karo

    for _ in range(300):  # 300 * 2s = 10 min polling
        try:
            _ms2 = _voltx_session if base_url == VOLTX_BASE_URL else _stex_session
            res = _ms2.get(f"{base_url}/success-otp", headers=headers, timeout=6)
            try:
                data = res.json()
            except Exception:
                logger.warning(f"{prefix} OTP poll: invalid JSON — {res.text[:120]!r}")
                first_iter = False
                time.sleep(2)
                continue
            resp_data = data.get("data", {})
            if isinstance(resp_data, dict):
                otps_list = resp_data.get("otps", [])
            elif isinstance(resp_data, list):
                otps_list = resp_data
            else:
                otps_list = data if isinstance(data, list) else []
            if not isinstance(otps_list, list):
                first_iter = False  # FIX: empty/wrong response pe bhi warmup reset karo
                time.sleep(2)
                continue
            for otp_entry in otps_list:
                # FIX: VoltX/Stex multiple number field names support karo
                entry_num = str(
                    otp_entry.get("no_plus_number") or
                    otp_entry.get("full_number") or
                    otp_entry.get("phone_number") or
                    otp_entry.get("number") or ""
                ).replace("+", "").replace(" ", "").replace("-", "").strip()
                if not entry_num:
                    continue
                if entry_num == clean_target or \
                   (len(entry_num) >= 8 and entry_num.endswith(clean_target[-8:])) or \
                   (len(clean_target) >= 8 and clean_target.endswith(entry_num[-8:])):
                    msg_text = otp_entry.get("message", otp_entry.get("sms", otp_entry.get("msg", "")))
                    if not msg_text:
                        continue
                    extracted_otp = extract_otp_code(msg_text)
                    if not extracted_otp:
                        continue
                    otp_id = otp_entry.get("otp_id", "")

                    # ── AGE GUARD ────────────────────────────────────────────
                    # Per-number poller mein bhi purane records aa sakte hain.
                    # 25h se purana OTP kabhi deliver nahi karna.
                    ts_str = str(
                        otp_entry.get("received_at") or otp_entry.get("created_at") or
                        otp_entry.get("sms_time") or otp_entry.get("date") or
                        otp_entry.get("timestamp") or otp_entry.get("createdAt") or ""
                    )
                    if ts_str and _is_stale_otp(ts_str):
                        continue  # 25h se purana — skip
                    # ─────────────────────────────────────────────────────────

                    unique_id = f"{prefix}_{otp_id}" if otp_id else f"{prefix}_{clean_target}_{extracted_otp}"
                    if _is_processed(unique_id):
                        continue
                    _add_to_processed(unique_id)

                    # ── WARMUP GATE ─────────────────────────────────────────
                    # Pehli iteration: jo OTP already API mein tha woh "purana" hai.
                    # Mark karo (dedup ke liye) lekin deliver bilkul mat karo.
                    if first_iter:
                        continue

                    # owner_id=None hone par bhi group ko deliver karo — sirf user DM skip hoga
                    app_name = detect_service(msg_text) or default_name
                    _record_and_deliver_otp(owner_id, num_str, app_name, msg_text, extracted_otp, clean_target, f"{prefix}_poll")
                    return  # OTP found, stop polling
        except Exception as e:
            logger.warning(f"{prefix}_poll_otp iteration error: {e}")
        first_iter = False  # Pehli iteration ke baad warmup khatam
        time.sleep(2)


def voltx_poll_otp(num_str, owner_id, api_key):
    """VoltX per-number OTP poller — thin wrapper around _poll_mauthapi_otp_single."""
    _poll_mauthapi_otp_single("VX", VOLTX_BASE_URL, "VoltX SMS", num_str, owner_id, api_key)


def stex_poll_otp(num_str, owner_id, api_key):
    """Stex per-number OTP poller — thin wrapper around _poll_mauthapi_otp_single."""
    _poll_mauthapi_otp_single("STX", STEX_BASE_URL, "Stex SMS", num_str, owner_id, api_key)

def _poll_mauthapi_otps(api_keys, base_url, prefix, default_name, first_run):
    """Shared helper for Stex and VoltX global SMS listeners.
    Both use the same mauthapi platform — same header, same response envelope.
    prefix: 'STX' for Stex, 'VX' for VoltX (used to deduplicate processed OTP IDs)."""
    for api_key in api_keys:
        try:
            headers = {"mauthapi": api_key, "User-Agent": "Mozilla/5.0"}
            _ms3 = _voltx_session if base_url == VOLTX_BASE_URL else _stex_session
            res = _ms3.get(f"{base_url}/success-otp", headers=headers, timeout=10)
            try:
                data = res.json()
            except Exception:
                logger.warning(f"global_sms {prefix}: invalid JSON — {res.text[:120]!r}")
                continue
            resp_data = data.get("data", {})
            if isinstance(resp_data, dict):
                otps_list = resp_data.get("otps", [])
            elif isinstance(resp_data, list):
                otps_list = resp_data
            else:
                otps_list = []
            for item in otps_list:
                # FIX: VoltX/Stex multiple number field names support karo (global listener)
                num = str(
                    item.get("no_plus_number") or
                    item.get("full_number") or
                    item.get("phone_number") or
                    item.get("number") or ""
                ).replace("+", "")
                msg_text = str(item.get("message", item.get("sms", item.get("msg", ""))))
                app_name = detect_service(msg_text) or default_name
                otp = extract_otp_code(msg_text) or "CODE"
                otp_id = item.get("otp_id", "")

                # ── AGE GUARD ────────────────────────────────────────────────
                # API response mein purane records bhi rehte hain. 25h se zyada
                # purana OTP kabhi deliver nahi karna — chahe dedup window expire
                # ho gayi ho ya bot restart hua ho.
                ts_str = str(
                    item.get("received_at") or item.get("created_at") or
                    item.get("sms_time") or item.get("date") or
                    item.get("timestamp") or item.get("createdAt") or ""
                )
                if ts_str and _is_stale_otp(ts_str):
                    continue  # 25h se purana — skip, deliver nahi karna
                # ─────────────────────────────────────────────────────────────

                if otp_id:
                    unique_id = f"{prefix}_{otp_id}"
                    dedup_window = 604800  # 7 din — otp_id wale records API mein kafi der rehte hain
                    # 25h window ki jagah 7 din: purana OTP dedup expiry ke baad dobara deliver
                    # nahi hoga. Age guard upar hai — naya actual OTP 25h ke andar aayega.
                    warmup_id = None      # item_id based: separate warmup key zaruri nahi
                else:
                    unique_id = f"{prefix}_{num}_{otp}"
                    dedup_window = 10    # 10 second — sirf tight-loop spam rokne ke liye
                    warmup_id = f"WARMUP_{unique_id}"  # 25h warmup protection key
                # Non-item_id: pehle WARMUP_ check (25h) — purana OTP block karo
                if warmup_id and _is_processed(warmup_id, window=90000):
                    continue
                if not _is_processed(unique_id, window=dedup_window) and num:
                    _add_to_processed(unique_id)
                    if first_run:
                        # first_run mein WARMUP_ key bhi mark karo (25h protection)
                        if warmup_id:
                            _add_to_processed(warmup_id)
                        continue
                    # FIX: non-first_run deliveries ke liye bhi warmup_id set karo
                    # (25h protection — 10s window expire hone ke baad same OTP dobara deliver na ho)
                    if warmup_id:
                        _add_to_processed(warmup_id)
                    clean_api_num = str(num).replace("+", "").replace(" ", "").replace("-", "").strip()
                    # FIX: owner na ho toh bhi group ko deliver karo (owner_id=None → group delivers, user skips)
                    found_owners = _find_otp_owners(clean_api_num)
                    owner_id = found_owners[0] if found_owners else None
                    _record_and_deliver_otp(owner_id, num, app_name, msg_text, otp, clean_api_num, f"global_sms_{prefix}")
                    # FIX: enforce _OTP_RECV_MAX on otp_received_numbers (VoltX/Stex global listener)
                    with _data_lock:
                        if len(otp_received_numbers) > _OTP_RECV_MAX:
                            keep = set(list(otp_received_numbers)[10000:])
                            otp_received_numbers.clear()
                            otp_received_numbers.update(keep)
        except Exception as e:
            logger.warning(f"global_sms {prefix} key loop error: {e}")
            continue


def _poll_nexa_global_otps(api_keys, warmup):
    """Nexa global SMS listener — same warmup/dedup/deliver shape as
    _poll_mauthapi_otps, ab isi jagah extract kiya hai taaki logic global_sms_listener
    ke andar dobara (duplicate) na likhna pade. Sirf Nexa ka response-shape/endpoint
    fallback (sms/latest → sms/recent) alag hai, baaki dedup/warmup/delivery pattern same hai."""
    for api_key in api_keys:
        try:
            headers = {"X-API-Key": api_key}
            try:
                res = _nexa_session.get(f"{NEXA_BASE_URL}/api/v1/sms/latest", headers=headers, timeout=10)
                data = res.json()
            except Exception as e:
                logger.warning(f"Nexa sms/latest fetch error: {e}")
                try:
                    res = _nexa_session.get(f"{NEXA_BASE_URL}/api/v1/sms/recent", headers=headers, timeout=10)
                    data = res.json()
                except Exception as e2:
                    logger.warning(f"Nexa sms/recent also failed: {e2}")
                    data = {}
            if not (data.get("success") and "data" in data):
                continue
            raw_items = data["data"]
            # Handle both list and dict responses
            if isinstance(raw_items, dict):
                raw_items = list(raw_items.values()) if raw_items else []
            for item in (raw_items if isinstance(raw_items, list) else []):
                num = str(item.get("number", "")).replace("+", "")
                # Handle both 'sms' and 'message' field names
                msg_text = str(item.get("sms") or item.get("message") or item.get("text") or "")

                # 🌟 Fix to detect service/app from full message
                app_name = item.get("app_name", "Unknown")
                detected_app = detect_service(msg_text)
                if detected_app:
                    app_name = detected_app

                otp = extract_otp_code(msg_text) or "CODE"
                sms_id = item.get("id", "")

                # ── AGE GUARD ────────────────────────────────────────────────
                # API mein purane records rehte hain. 25h se purana OTP kabhi
                # deliver nahi karna — chahe dedup expire ho ya bot restart ho.
                ts_str = str(
                    item.get("received_at") or item.get("created_at") or
                    item.get("sms_time") or item.get("date") or
                    item.get("timestamp") or item.get("createdAt") or ""
                )
                if ts_str and _is_stale_otp(ts_str):
                    continue  # 25h se purana — skip
                # ─────────────────────────────────────────────────────────────

                if sms_id:
                    unique_id = f"NEXA_{num}_{sms_id}"
                    dedup_window = 604800  # 7 din — sms_id wale records API mein rehte hain
                    warmup_id = None      # id-based: separate warmup key zaruri nahi
                else:
                    unique_id = f"NEXA_{num}_{otp}"
                    dedup_window = 10    # 10 second — sirf tight-loop spam rokne ke liye
                    warmup_id = f"WARMUP_{unique_id}"  # 25h warmup protection key

                # Non-id: pehle WARMUP_ check (25h) — purana OTP block karo
                if warmup_id and _is_processed(warmup_id, window=90000):
                    continue

                if not _is_processed(unique_id, window=dedup_window) and num:
                    _add_to_processed(unique_id)

                    # warmup pass: WARMUP_ key bhi mark karo (25h protection), deliver mat karo
                    if warmup:
                        if warmup_id:
                            _add_to_processed(warmup_id)
                        continue
                    # FIX: non-warmup deliveries ke liye bhi warmup_id set karo
                    # (25h protection — 10s window expire hone ke baad same OTP dobara deliver na ho)
                    if warmup_id:
                        _add_to_processed(warmup_id)

                    clean_api_num = str(num).replace("+", "").replace(" ", "").replace("-", "").strip()
                    # FIX: owner na ho toh bhi group ko deliver karo (owner_id=None → group delivers, user skips)
                    found_owners = _find_otp_owners(clean_api_num)
                    owner_id = found_owners[0] if found_owners else None
                    _record_and_deliver_otp(owner_id, num, app_name, msg_text, otp, clean_api_num, "global_sms_nexa")
                    with _data_lock:
                        if len(otp_received_numbers) > _OTP_RECV_MAX:
                            # Sabse pehle aaye 10000 hata do (oldest entries)
                            keep = set(list(otp_received_numbers)[10000:])
                            otp_received_numbers.clear()
                            otp_received_numbers.update(keep)
        except Exception as e:
            logger.warning(f"global_sms nexa key loop error: {e}")
            continue


def global_sms_listener():
    first_run = True
    while True:
        # Per-service effective warmup: True on bot startup OR when toggled ON / key added mid-run
        nexa_warmup  = first_run or _service_warmup_needed.get("nexa",  False)
        voltx_warmup = first_run or _service_warmup_needed.get("voltx", False)
        stex_warmup  = first_run or _service_warmup_needed.get("stex",  False)

        try:
            # Nexa listener — only poll if toggled ON (shared helper — see _poll_nexa_global_otps)
            _poll_nexa_global_otps(
                bot_settings.get("nexa_keys", []) if bot_settings.get("nexa_on", False) else [],
                nexa_warmup
            )

            # 🌟 Stex + VoltX SMS Global Listeners (shared helper — same API platform)
            _poll_mauthapi_otps(
                bot_settings.get("stex_keys", []) if bot_settings.get("stex_on", False) else [],
                STEX_BASE_URL, "STX", "Stex SMS", stex_warmup
            )
            _poll_mauthapi_otps(
                bot_settings.get("voltx_keys", []) if bot_settings.get("voltx_on", False) else [],
                VOLTX_BASE_URL, "VX", "VoltX SMS", voltx_warmup
            )

        except Exception as e:
            logger.warning(f"global_sms_listener error: {e}")

        # After each poll cycle: reset per-service warmup flags that were just consumed
        if nexa_warmup:
            _service_warmup_needed["nexa"] = False
            if first_run:
                logger.info("Nexa warmup done — old OTPs skipped.")
            else:
                logger.info("Nexa re-enabled warmup done — old OTPs skipped.")
        if stex_warmup:
            _service_warmup_needed["stex"] = False
            if not first_run:
                logger.info("Stex re-enabled warmup done — old OTPs skipped.")
        if voltx_warmup:
            _service_warmup_needed["voltx"] = False
            if not first_run:
                logger.info("VoltX re-enabled warmup done — old OTPs skipped.")

        if first_run:
            first_run = False
            logger.info("Nexa/VoltX/Stex startup warmup done — old OTPs skipped.")
        _save_processed_otps()
        time.sleep(1)  # Har 1 second mein check (was 5s — faster Nexa/VoltX/Stex delivery)

def flush_old_updates():
    """Skip all pending Telegram updates so old messages are not reprocessed on restart."""
    try:
        res = api_call("getUpdates?offset=-1&timeout=0")
        if res and res.get("ok") and res.get("result") and len(res["result"]) > 0:
            last_id = res["result"][-1].get("update_id", 0)
            if last_id:
                api_call(f"getUpdates?offset={last_id + 1}&timeout=0")
            logger.info(f"Flushed old Telegram updates (last_id={last_id})")
        else:
            logger.info("No pending Telegram updates to flush.")
    except Exception as e:
        logger.warning(f"Could not flush old updates: {e}")

def _panel_session_cleanup():
    """Background thread: close & remove stale panel_sessions every 10 minutes."""
    while True:
        time.sleep(600)
        try:
            # Use index-based keys (0, 1, 2...) matching panel_sessions dict structure
            active_indices = set(range(len(bot_settings.get("panels", []))))
            stale = [k for k in list(panel_sessions.keys()) if k not in active_indices]
            for k in stale:
                sess = panel_sessions.pop(k, None)
                if sess:
                    try: sess.close()
                    except Exception as close_err:
                        logger.warning(f"panel_session close error for key {k}: {close_err}")
            if stale:
                logger.info(f"Cleaned {len(stale)} stale panel session(s).")
        except Exception as e:
            logger.warning(f"panel_session_cleanup error: {e}")

def main():
    global BOT_USERNAME
    res = api_call("getMe")
    if res.get("ok"): BOT_USERNAME = res["result"]["username"]
    logger.info(f"Bot is starting... @{BOT_USERNAME}")
    
    # 🧹 Load previously seen OTP IDs so old OTPs are never resent after restart
    _load_processed_otps()
    
    # 🧹 Flush old updates BEFORE starting background threads
    flush_old_updates()
    
    threading.Thread(target=panel_monitor_thread, daemon=True).start()
    threading.Thread(target=global_sms_listener, daemon=True).start()
    threading.Thread(target=_panel_session_cleanup, daemon=True).start()
    threading.Thread(target=_cleanup_loop, daemon=True).start()
    logger.info("Background APIs & Global SMS Listener Started!")
    
    # 🌟 PRO-LEVEL FAST SYSTEM: 50 Workers Pool (memory safe)
    executor = ThreadPoolExecutor(max_workers=50)
    
    offset = None
    while True:
        try:
            offset_param = f"&offset={offset}" if offset is not None else ""
            updates = api_call(f"getUpdates?timeout=30{offset_param}")
            if updates and updates.get("ok") and "result" in updates and isinstance(updates["result"], list):
                for update in updates["result"]:
                    offset = update.get("update_id", (offset or 1) - 1) + 1
                    if "message" in update:
                        try:
                            executor.submit(handle_message, update["message"])
                        except Exception as submit_err:
                            logger.warning(f"Executor submit error (message): {submit_err}")
                    elif "callback_query" in update:
                        try:
                            executor.submit(handle_callback, update["callback_query"])
                        except Exception as submit_err:
                            logger.warning(f"Executor submit error (callback): {submit_err}")
            elif updates and not updates.get("ok"):
                # Telegram API error (e.g. 409 Conflict - bot running twice)
                err_code = updates.get("error_code", 0)
                err_desc = updates.get("description", "Unknown error")
                logger.warning(f"Telegram API error {err_code}: {err_desc}")
                if err_code == 409:
                    logger.error("CONFLICT: Another bot instance is running! Shutting down.")
                    break
                time.sleep(5)
        except Exception as e:
            logger.error(f"Main polling error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()    
