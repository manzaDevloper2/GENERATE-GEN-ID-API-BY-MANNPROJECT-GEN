from flask import Flask, request, jsonify
import hmac
import hashlib
import requests
import string
import random
import secrets
import json
import base64
import re
import os
import time
import threading
import uuid
import ipaddress
import concurrent.futures
from datetime import datetime, timezone
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ═══ TAHAP 1 PATCH — IMPORT CLEANUP MODULE ═══
try:
    from cleanup import start_cleanup_thread, run_cleanup, get_cleanup_stats
    _CLEANUP_OK = True
except Exception as _e:
    print(f"[!] cleanup module not loaded: {_e}")
    _CLEANUP_OK = False
# ═══ END TAHAP 1 PATCH ═══

app = Flask(__name__)

# ═══════════════════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════════════════

APP_ID         = 100067
RELEASE_VER    = "OB55"
GAME_VERSION   = "2.132.4"
CLIENT_SECRET  = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
HEX_KEY        = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"

URL_GUEST_REGISTER = "https://100067.connect.garena.com/api/v2/oauth/guest:register"
URL_TOKEN_GRANT    = "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant"
URL_MAJOR_LOGIN    = "https://loginbp.ppmainecoonghj.com/MajorLogin"
URL_MAJOR_REGISTER = "https://loginbp.ppmainecoonghj.com/MajorRegister"
URL_NEWBIE_CHOICE  = "https://loginbp.ppmainecoonghj.com/ChooseNewbieChoice"

FORCE_REGION       = "ID"
FORCE_NAME_PREFIX  = "MANN"
FORCE_PASS_PREFIX  = "MANN_"

REGION_LANG = {
    "ME": "ar", "IND": "hi", "ID": "id", "JP": "ja",
    "VN": "vi", "TH": "th", "BD": "bn", "PK": "ur",
    "TW": "zh", "CIS": "ru", "SAC": "es", "BR": "pt",
    "SG": "en", "US": "en", "EU": "en", "LK": "en",
}

_AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
_AES_IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

FIELD_22 = bytes.fromhex(
    "4747524501010100620200001052aa0d669c6a368f08338060d2ee0690053af84a41edcd3558556ec10f24f4"
    "6c93ac64ca41a16732c46a2cb071246a79b8929032f9e1b6f4ef331bd53cabf29b09b97349a46e9863c0314e"
    "1a0d80819fef8aabf03876b3d037db354a7ccb5c1bce96411fb3753f6f50e44c69c4ed617fa30efb8ffc0517"
    "ff2f636739be1f304d999cfd6fd48bf69454199794c3dc88f55a4bdbd66534d5a061359cdfd1fb680cd37918"
    "df9fdb3cf7d80067b0a3506c90063cf62b2ccec11e23913a2fd7c4ef091331967bb518a5ad1e551146b90821"
    "be800883abadde39d6c80a5d798611466c748f075481806c5842ce45e6bd4e3368ec08fe2ec41ceb880cd862"
    "49eb71693f79f0bccf9e590c3fae12519fe08c7a1905d0927690109e0df28574bb14847225db1a59230e6662"
    "ed7730e15ff9a6c815cb41b420edeada735a4b03e181037c37c2c850257311df2f07b0a56e759372cbd0268e"
    "3f13a292ee4373e38ab5096e0342a5e0d7fec6da2bbc265d74baadd2b24ee4f74862f82c21d6694bac53f8ce"
    "80312a30068a6276a641c19b11d0305c6fe2f531ac7de578b29f543697f5c73663e6f23aa15277b6122dcd4d"
    "4171e38f9ac0b173f39c58416a16c5c1f4a35acd065ce78f449cf538a249339e763272d458e4ed86c976591a"
    "9c066b3a37111e44091eb6b5a795249f3e5145db022a6055f2cc675936391312f688f89627845df222a91156"
    "555225be36f9714a0ba50246d0f003bda3c9c1292ab73b4f79635ddd023218eda93a302d79e023404c143965"
    "44a930b98ed54771aca7fec10d095587685b473e81a9619764fad9256529dcd6e911f4f4629612287d4ee3ec"
    "5389f6ec4ec020b0e2aac017232a9197be9e46239ce690fe5d4872b2e98e651510c971667f3aca8b59f3e9d5"
    "0e43"
)

# ═══════════════════════════════════════════════════════════════════════════
#  IP POOL — RATUSAN IP (proxy header spoofing)
# ═══════════════════════════════════════════════════════════════════════════

def _build_ip_pool():
    """Generate ratusan IP publik dari range realistis."""
    pool = set()
    ranges = [
        # (prefix, jumlah) — prefix dari range publik populer
        ("1.",       400), ("5.",       400), ("14.",      400), ("27.",      400),
        ("31.",      400), ("36.",      400), ("37.",      400), ("39.",      400),
        ("41.",      400), ("42.",      400), ("43.",      400), ("45.",      400),
        ("46.",      400), ("47.",      400), ("49.",      400), ("58.",      400),
        ("59.",      400), ("60.",      400), ("61.",      400), ("62.",      400),
        ("77.",      400), ("78.",      400), ("79.",      400), ("80.",      400),
        ("81.",      400), ("82.",      400), ("83.",      400), ("84.",      400),
        ("85.",      400), ("86.",      400), ("87.",      400), ("88.",      400),
        ("89.",      400), ("90.",      400), ("91.",      400), ("92.",      400),
        ("93.",      400), ("94.",      400), ("95.",      400), ("101.",     400),
        ("102.",     400), ("103.",     400), ("104.",     400), ("105.",     400),
        ("106.",     400), ("107.",     400), ("108.",     400), ("109.",     400),
        ("110.",     400), ("111.",     400), ("112.",     400), ("113.",     400),
        ("114.",     400), ("115.",     400), ("116.",     400), ("117.",     400),
        ("118.",     400), ("119.",     400), ("120.",     400), ("121.",     400),
        ("122.",     400), ("123.",     400), ("124.",     400), ("125.",     400),
        ("126.",     400), ("128.",     400), ("129.",     400), ("130.",     400),
        ("131.",     400), ("132.",     400), ("133.",     400), ("134.",     400),
        ("135.",     400), ("136.",     400), ("137.",     400), ("138.",     400),
        ("139.",     400), ("140.",     400), ("141.",     400), ("142.",     400),
        ("143.",     400), ("144.",     400), ("145.",     400), ("146.",     400),
        ("147.",     400), ("148.",     400), ("149.",     400), ("150.",     400),
        ("151.",     400), ("152.",     400), ("153.",     400), ("154.",     400),
        ("155.",     400), ("156.",     400), ("157.",     400), ("158.",     400),
        ("159.",     400), ("160.",     400), ("161.",     400), ("162.",     400),
        ("163.",     400), ("164.",     400), ("165.",     400), ("166.",     400),
        ("167.",     400), ("168.",     400), ("169.",     400), ("170.",     400),
        ("171.",     400), ("172.",     400), ("173.",     400), ("174.",     400),
        ("175.",     400), ("176.",     400), ("177.",     400), ("178.",     400),
        ("179.",     400), ("180.",     400), ("181.",     400), ("182.",     400),
        ("183.",     400), ("184.",     400), ("185.",     400), ("186.",     400),
        ("187.",     400), ("188.",     400), ("189.",     400), ("190.",     400),
        ("191.",     400), ("192.",     400), ("193.",     400), ("194.",     400),
        ("195.",     400), ("196.",     400), ("197.",     400), ("198.",     400),
        ("199.",     400), ("200.",     400), ("201.",     400), ("202.",     400),
        ("203.",     400), ("204.",     400), ("205.",     400), ("206.",     400),
        ("207.",     400), ("208.",     400), ("209.",     400), ("210.",     400),
        ("211.",     400), ("212.",     400), ("213.",     400), ("214.",     400),
        ("215.",     400), ("216.",     400), ("217.",     400), ("218.",     400),
        ("219.",     400), ("220.",     400), ("221.",     400), ("222.",     400),
        ("223.",     400),
    ]

    private_ranges = [
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("169.254.0.0/16"),
        ipaddress.ip_network("224.0.0.0/4"),
        ipaddress.ip_network("240.0.0.0/4"),
    ]

    for prefix, count in ranges:
        for _ in range(count):
            b = random.randint(0, 255)
            c = random.randint(0, 255)
            d = random.randint(1, 254)
            ip_str = f"{prefix}{b}.{c}.{d}"
            try:
                ip_obj = ipaddress.ip_address(ip_str)
                if any(ip_obj in net for net in private_ranges):
                    continue
                pool.add(ip_str)
            except Exception:
                continue

    pool_list = list(pool)
    random.shuffle(pool_list)
    return pool_list


print("[*] Building IP pool...")
IP_POOL = _build_ip_pool()
print(f"[+] IP pool ready: {len(IP_POOL)} IPs")

_ip_idx = 0
_ip_lock = threading.Lock()


def pick_ip():
    """Round-robin random dari IP pool besar."""
    global _ip_idx
    if not IP_POOL:
        return None
    with _ip_lock:
        i = random.randint(0, len(IP_POOL) - 1)
        return IP_POOL[i]


def ip_headers():
    """Generate header spoof IP + chain fake."""
    real = pick_ip() or f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    chain = [real]
    for _ in range(random.randint(1, 3)):
        chain.append(pick_ip() or real)
    forwarded_for = ", ".join(chain)
    return {
        "X-Forwarded-For": forwarded_for,
        "X-Real-IP": real,
        "X-Client-IP": real,
        "X-Originating-IP": real,
        "X-Remote-IP": real,
        "X-Remote-Addr": real,
        "Forwarded": f"for={real};proto=https",
        "CF-Connecting-IP": real,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  DEVICE POOL — 200+ UA
# ═══════════════════════════════════════════════════════════════════════════

USER_AGENTS_POOL = [
    # === Existing (dari kodemu) ===
    "GarenaMSDK/4.0.39(SM-A325M;Android 13;en;HK;)",
    "GarenaMSDK/4.0.38(Redmi Note 10;Android 12;en;ID;)",
    "GarenaMSDK/4.0.40(Poco X3;Android 11;en;SG;)",
    "GarenaMSDK/4.0.41(SM-S918B;Android 14;en;IN;)",
    "GarenaMSDK/4.0.42(OnePlus 11;Android 13;en;US;)",
    "GarenaMSDK/4.0.39(Xiaomi 13 Pro;Android 13;pt;BR;)",
    "GarenaMSDK/4.0.40(Pixel 7 Pro;Android 14;en;US;)",
    "GarenaMSDK/4.0.38(ASUS ROG Phone 7;Android 13;id;ID;)",
    "GarenaMSDK/4.0.41(Infinix Note 12;Android 12;th;TH;)",
    "GarenaMSDK/4.0.43(SM-G998B;Android 13;ar;EG;)",
    "GarenaMSDK/4.0.37(Redmi Note 11;Android 11;es;MX;)",
    "GarenaMSDK/4.0.40(Poco F5;Android 13;en;VN;)",
    "GarenaMSDK/4.0.42(Realme GT 3;Android 13;hi;IN;)",
    "GarenaMSDK/4.0.39(Vivo V27;Android 13;en;PH;)",
    "GarenaMSDK/4.0.41(OPPO Reno 10;Android 13;id;ID;)",
    "GarenaMSDK/4.0.38(Tecno Camon 20;Android 13;fr;FR;)",
    "GarenaMSDK/4.0.40(Huawei P50;Android 11;ar;SA;)",
    "GarenaMSDK/4.0.42(Lenovo Legion Y70;Android 12;zh;TW;)",
    "GarenaMSDK/4.0.39(Zuck Z5 Pro;Android 11;en;US;)",
    "GarenaMSDK/4.0.44(SM-S928B;Android 14;en;SG;)",
    "GarenaMSDK/4.0.42(Xiaomi 14;Android 14;id;ID;)",
    "GarenaMSDK/4.0.40(Poco X5 Pro;Android 12;en;MY;)",
    "GarenaMSDK/4.0.41(Oppo Find X5;Android 13;th;TH;)",
    "GarenaMSDK/4.0.39(Vivo X80;Android 12;vi;VN;)",
    "GarenaMSDK/4.0.43(Realme 11 Pro;Android 13;hi;IN;)",
    "GarenaMSDK/4.0.38(Infinix Zero 30;Android 13;ar;SA;)",
    "GarenaMSDK/4.0.40(Tecno Phantom V;Android 13;pt;BR;)",
    "GarenaMSDK/4.0.42(Samsung A54;Android 13;es;MX;)",
    "GarenaMSDK/4.0.39(Samsung A34;Android 13;en;PH;)",
]

# === Samsung A-series & S-series (7 region × 15 model) ===
_SAMSUNG_MODELS = [
    ("SM-A325M", "13"), ("SM-A525F", "13"), ("SM-A725F", "13"),
    ("SM-A127F", "12"), ("SM-A037F", "11"), ("SM-A546E", "14"),
    ("SM-A346E", "14"), ("SM-A146P", "13"), ("SM-M236B", "13"),
    ("SM-M536B", "14"),
    ("SM-S901E", "13"), ("SM-S908E", "13"), ("SM-S918B", "14"),
    ("SM-G998B", "13"), ("SM-G991B", "13"), ("SM-A135F", "13"),
    ("SM-A226B", "13"), ("SM-A536B", "14"), ("SM-M135F", "13"),
    ("SM-A045F", "13"),
]
_SAMSUNG_REGS = ["HK", "ID", "SG", "MY", "PH", "TH", "VN"]

for _model, _osv in _SAMSUNG_MODELS:
    for _reg in _SAMSUNG_REGS:
        USER_AGENTS_POOL.append(
            f"GarenaMSDK/4.0.39({_model};Android {_osv};en;{_reg};)"
        )

# === Xiaomi / Poco / Redmi (7 region × 20 model) ===
_XIAOMI_MODELS = [
    "Poco X3", "Poco X3 Pro", "Poco F3", "Poco F4", "Poco F5",
    "Poco M4 Pro", "Poco M5",
    "Xiaomi 12", "Xiaomi 12 Pro", "Xiaomi 13 Pro", "Xiaomi 14", "Xiaomi 14 Pro",
    "Xiaomi 11T", "Xiaomi 11T Pro",
    "Redmi Note 10", "Redmi Note 11", "Redmi Note 12", "Redmi Note 13",
    "Redmi 9", "Redmi 10", "Redmi 12",
]
_XIAOMI_OS = ["11", "12", "13", "14"]

for _model in _XIAOMI_MODELS:
    for _osv in _XIAOMI_OS:
        for _reg in _SAMSUNG_REGS:
            USER_AGENTS_POOL.append(
                f"GarenaMSDK/4.0.40({_model};Android {_osv};en;{_reg};)"
            )

# === Oppo (CPH series) ===
_OPPO_MODELS = [
    "CPH2025", "CPH2219", "CPH2345", "CPH2449",
    "CPH2557", "CPH2509", "CPH2601",
]
for _model in _OPPO_MODELS:
    for _osv in ["12", "13", "14"]:
        for _reg in _SAMSUNG_REGS:
            USER_AGENTS_POOL.append(
                f"GarenaMSDK/4.0.39({_model};Android {_osv};en;{_reg};)"
            )

# === Vivo (V-series) ===
_VIVO_MODELS = [
    "V2024", "V2048", "V2120", "V2146", "V2229", "V2307",
]
for _model in _VIVO_MODELS:
    for _osv in ["12", "13", "14"]:
        for _reg in _SAMSUNG_REGS:
            USER_AGENTS_POOL.append(
                f"GarenaMSDK/4.0.39({_model};Android {_osv};en;{_reg};)"
            )

# === Realme (RMX series) ===
_REALME_MODELS = [
    "RMX2020", "RMX3360", "RMX3363", "RMX3630", "RMX3700",
    "RMX3686", "RMX3636", "RMX3624",
]
for _model in _REALME_MODELS:
    for _osv in ["11", "12", "13", "14"]:
        for _reg in _SAMSUNG_REGS:
            USER_AGENTS_POOL.append(
                f"GarenaMSDK/4.0.39({_model};Android {_osv};en;{_reg};)"
            )

# === OnePlus ===
_ONEPLUS_MODELS = ["CPH2411", "CPH2451", "CPH2477", "CPH2487", "CPH2493"]
for _model in _ONEPLUS_MODELS:
    for _osv in ["13", "14"]:
        for _reg in _SAMSUNG_REGS:
            USER_AGENTS_POOL.append(
                f"GarenaMSDK/4.0.39({_model};Android {_osv};en;{_reg};)"
            )

# Dedup
USER_AGENTS_POOL = list(dict.fromkeys(USER_AGENTS_POOL))

print(f"[+] UA pool ready: {len(USER_AGENTS_POOL)} UAs")

# ═══ TAHAP 1 PATCH — START AUTO CLEANUP THREAD ═══
if _CLEANUP_OK:
    start_cleanup_thread()
# ═══ END TAHAP 1 PATCH ═══


def random_ua():
    return random.choice(USER_AGENTS_POOL)


# ═══════════════════════════════════════════════════════════════════════════
#  DEVICE INFO BUILDER (untuk MajorLogin proto field)
# ═══════════════════════════════════════════════════════════════════════════

DEVICE_MODELS = [
    ("Asus ASUS_AI2501_B", "Android OS 12 / API-31 (SP1A.210812.016.C2)", "Adreno (TM) 640"),
    ("Redmi Note 12 Pro", "Android OS 13 / API-33 (TP1A.220624.014)", "Adreno (TM) 618"),
    ("Samsung SM-M135F", "Android OS 13 / API-33 (TP1A.220624.014)", "Mali-G68"),
    ("Realme RMX3630", "Android OS 12 / API-31 (SP1A.210812.016)", "Adreno (TM) 610"),
    ("Vivo V2149", "Android OS 13 / API-33 (TP1A.220624.014)", "Adreno (TM) 642L"),
    ("OnePlus CPH2411", "Android OS 13 / API-33 (TP1A.220624.014)", "Adreno (TM) 730"),
    ("Poco M4 Pro 5G", "Android OS 12 / API-31 (SP1A.210812.016)", "Mali-G57 MC2"),
    ("iQOO I2012", "Android OS 13 / API-33 (TP1A.220624.014)", "Adreno (TM) 650"),
    ("Oppo CPH2477", "Android OS 13 / API-33 (TP1A.220624.014)", "Adreno (TM) 619"),
    ("Tecno KI8", "Android OS 13 / API-33 (TP1A.220624.014)", "Mali-G57"),
    ("Infinix X6819", "Android OS 12 / API-31 (SP1A.210812.016)", "Mali-G52 MC2"),
    ("Motorola moto g73", "Android OS 13 / API-33 (TP1A.220624.014)", "Adreno (TM) 619"),
    ("Xiaomi 2201122G", "Android OS 13 / API-33 (TP1A.220624.014)", "Adreno (TM) 730"),
    ("Realme RMX3700", "Android OS 14 / API-34 (UP1A.231005.007)", "Mali-G710"),
    ("OnePlus CPH2451", "Android OS 13 / API-33 (TP1A.220624.014)", "Adreno (TM) 740"),
    ("OPPO CPH2611", "Android OS 14 / API-34 (UP1A.231005.007)", "Adreno (TM) 720"),
    ("Samsung SM-G998B", "Android OS 12 / API-31 (SP1A.210812.016)", "Adreno (TM) 660"),
    ("Poco M2102J20SG", "Android OS 13 / API-33 (TP1A.220624.014)", "Adreno (TM) 660"),
    ("Vivo V2203", "Android OS 12 / API-31 (SP1A.210812.016)", "Mali-G710"),
    ("Xiaomi 2201117TG", "Android OS 12 / API-31 (SP1A.210812.016)", "Adreno (TM) 618"),
    ("Samsung SM-A546E", "Android OS 14 / API-34 (UP1A.231005.007)", "Mali-G68"),
    ("Xiaomi 23127PN0CG", "Android OS 14 / API-34 (UP1A.231005.007)", "Adreno (TM) 750"),
    ("Poco F5 Pro", "Android OS 13 / API-33 (TP1A.220624.014)", "Adreno (TM) 730"),
    ("Vivo V2307", "Android OS 14 / API-34 (UP1A.231005.007)", "Mali-G610"),
    ("Oppo CPH2557", "Android OS 14 / API-34 (UP1A.231005.007)", "Adreno (TM) 710"),
]


def generate_device_info():
    model, os_str, gpu = random.choice(DEVICE_MODELS)
    return {
        "model": model,
        "os_string": os_str,
        "gpu": gpu,
        "gpu_full": "OpenGL ES 3.2",
        "device_id": f"Google|{uuid.uuid4()}",
        "device_uuid": f"02-{uuid.uuid4()}",
    }


# ═══════════════════════════════════════════════════════════════════════════
#  THREAD-LOCAL SESSION (non stuck)
# ═══════════════════════════════════════════════════════════════════════════

_thread_local = threading.local()


def get_session():
    if not hasattr(_thread_local, "session"):
        s = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=200,
            pool_maxsize=200,
            max_retries=0,
            pool_block=False,
        )
        s.mount("https://", adapter)
        s.mount("http://", adapter)
        s.verify = False
        s.headers.update({
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        })
        _thread_local.session = s
    return _thread_local.session


# ═══════════════════════════════════════════════════════════════════════════
#  STATS
# ═══════════════════════════════════════════════════════════════════════════

STATS = {
    "total_requests": 0,
    "total_success": 0,
    "total_fail": 0,
    "fail_register": 0,
    "fail_token": 0,
    "fail_major": 0,
    "last_success_at": None,
    "last_fail_at": None,
}
STATS_LOCK = threading.Lock()


def record_success():
    with STATS_LOCK:
        STATS["total_requests"] += 1
        STATS["total_success"] += 1
        STATS["last_success_at"] = datetime.now(timezone.utc).isoformat()


def record_fail(kind="major"):
    with STATS_LOCK:
        STATS["total_requests"] += 1
        STATS["total_fail"] += 1
        STATS["last_fail_at"] = datetime.now(timezone.utc).isoformat()
        if kind == "reg":
            STATS["fail_register"] += 1
        elif kind == "tok":
            STATS["fail_token"] += 1
        elif kind == "major":
            STATS["fail_major"] += 1


# ═══════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def generate_random_name(base):
    chars = string.ascii_letters + string.digits
    return f"{base[:4]}{''.join(random.choice(chars) for _ in range(8))}"


def encode_varint(n):
    if n < 0:
        return b""
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            b |= 0x80
        out.append(b)
        if not n:
            break
    return bytes(out)


def create_proto_field(field_num, value):
    try:
        if isinstance(value, int):
            return encode_varint((field_num << 3) | 0) + encode_varint(value)
        elif isinstance(value, (str, bytes)):
            v = value.encode() if isinstance(value, str) else value
            return encode_varint((field_num << 3) | 2) + encode_varint(len(v)) + v
        elif isinstance(value, dict):
            nested = build_proto(value)
            return encode_varint((field_num << 3) | 2) + encode_varint(len(nested)) + nested
        return b""
    except Exception:
        return b""


def build_proto(fields):
    try:
        return b"".join(create_proto_field(k, v) for k, v in fields.items())
    except Exception:
        return b""


def aes_encrypt(hex_data):
    try:
        data = bytes.fromhex(hex_data)
        return AES.new(_AES_KEY, AES.MODE_CBC, _AES_IV).encrypt(pad(data, AES.block_size))
    except Exception:
        return b""


def encrypt_api(plain_hex):
    try:
        plain = bytes.fromhex(plain_hex)
        return AES.new(_AES_KEY, AES.MODE_CBC, _AES_IV).encrypt(pad(plain, AES.block_size)).hex()
    except Exception:
        return ""


def _make_field_f14(open_id):
    keystream = [
        0x30, 0x30, 0x30, 0x32, 0x30, 0x31, 0x37, 0x30,
        0x30, 0x30, 0x30, 0x30, 0x32, 0x30, 0x31, 0x37,
        0x30, 0x30, 0x30, 0x30, 0x30, 0x32, 0x30, 0x31,
        0x37, 0x30, 0x30, 0x30, 0x30, 0x30, 0x32, 0x30,
    ]
    ob = open_id.encode("latin1", errors="ignore") if isinstance(open_id, str) else open_id
    return bytes((ob[i] ^ keystream[i % len(keystream)]) & 0xFF for i in range(len(ob)))


JWT_RE = re.compile(r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+")


def extract_jwt(content: bytes):
    if not content:
        return None
    try:
        text = content.decode("utf-8", errors="ignore")
        m = JWT_RE.search(text)
        if m:
            return m.group(0)
    except Exception:
        pass
    try:
        m = re.search(rb"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+", content)
        if m:
            return m.group(0).decode("utf-8", errors="ignore")
    except Exception:
        pass
    return None


def is_valid_jwt(tok):
    return bool(tok) and tok.startswith("eyJ") and tok.count(".") >= 2 and len(tok) > 50


# ═══════════════════════════════════════════════════════════════════════════
#  GARENA API CALLS — NON STUCK, NO SLEEP
# ═══════════════════════════════════════════════════════════════════════════

def guest_register(password):
    try:
        body = json.dumps({
            "app_id": APP_ID,
            "client_type": 2,
            "password": password,
            "source": 2,
        }, separators=(",", ":"))
        sig = hmac.new(HEX_KEY.encode(), body.encode(), hashlib.sha256).hexdigest()

        ua = random_ua()
        headers = {
            "User-Agent": ua,
            "Connection": "Keep-Alive",
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "Authorization": f"Signature {sig}",
            "Content-Type": "application/json; charset=utf-8",
            "Host": "100067.connect.garena.com",
        }
        headers.update(ip_headers())

        r = get_session().post(
            URL_GUEST_REGISTER,
            headers=headers,
            data=body,
            timeout=(3, 6),
            verify=False,
        )
        if r.status_code != 200:
            return None
        j = r.json()
        if j.get("code") != 0:
            return None
        return j["data"]["uid"]
    except Exception:
        return None


def token_grant(uid, password):
    try:
        body = json.dumps({
            "client_id": APP_ID,
            "client_secret": HEX_KEY,
            "client_type": 2,
            "device_id": f"02-{uuid.uuid4()}",
            "password": password,
            "response_type": "token",
            "uid": uid,
        }, separators=(",", ":"))

        ua = random_ua()
        headers = {
            "User-Agent": ua,
            "Connection": "Keep-Alive",
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "Content-Type": "application/json; charset=utf-8",
            "Host": "100067.connect.garena.com",
        }
        headers.update(ip_headers())

        r = get_session().post(
            URL_TOKEN_GRANT,
            headers=headers,
            data=body,
            timeout=(3, 6),
            verify=False,
        )
        if r.status_code != 200:
            return None
        j = r.json()
        if j.get("code") != 0:
            return None
        return j["data"]["access_token"], j["data"]["open_id"]
    except Exception:
        return None


def build_majorlogin_proto(open_id, access_token, lang="en",
                           client_version="1.132.1",
                           client_version_code="2019116753"):
    device = generate_device_info()
    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    fields = {
        3: now_ts,
        4: "free fire",
        5: 4,
        7: client_version,
        8: client_version_code,
        9: device["os_string"],
        10: "Handheld",
        11: device["model"],
        12: 1280,
        13: 720,
        14: "240",
        15: "x86-64 SSE3 SSE4.1 SSE4.2 AVX AVX2 | 2400 | 4",
        16: random.choice([5951, 6000, 6100, 5500, 6500]),
        17: device["gpu"],
        18: "OpenGL ES 3.1 v1.46",
        19: device["device_id"],
        20: "127.0.0.1",
        21: lang,
        22: open_id,
        23: "4",
        24: "Handheld",
        25: device["model"],
        26: "IND",
        29: access_token,
        30: 1,
        41: "Jio",
        42: "WIFI",
        92: random.choice([19788, 20000, 21000]),
        93: "android_max",
        97: 1,
        98: 1,
        99: "4",
        100: "4",
        104: 77149,
        105: 1,
    }
    proto = build_proto(fields)
    return bytes.fromhex(encrypt_api(proto.hex()))


def major_register(access_token, open_id, uid, password, region, nick, lang):
    try:
        field_f14 = _make_field_f14(open_id)
        payload = {
            1: nick,
            2: access_token,
            3: open_id,
            5: 102000007,
            6: 4,
            7: 1,
            13: 1,
            14: field_f14,
            15: lang,
            16: 1,
            17: 1,
            22: FIELD_22,
        }
        enc = aes_encrypt(build_proto(payload).hex())

        ua = random_ua()
        headers = {
            "User-Agent": ua,
            "Accept-Encoding": "deflate, gzip",
            "X-GA-SV": "1789535859",
            "Authorization": "Bearer",
            "X-GA": "v1 1",
            "ReleaseVersion": RELEASE_VER,
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Unity-Version": "2018.4.12f1",
            "Host": "loginbp.ppmainecoonghj.com",
        }
        headers.update(ip_headers())

        get_session().post(
            URL_MAJOR_REGISTER,
            headers=headers,
            data=enc,
            verify=False,
            timeout=(3, 6),
        )
        return major_login(access_token, open_id, lang)
    except Exception:
        return None


def major_login(access_token, open_id, lang="en"):
    try:
        payload = build_majorlogin_proto(open_id, access_token, lang)

        ua = random_ua()
        headers = {
            "User-Agent": ua,
            "Accept-Encoding": "deflate, gzip",
            "X-GA-SV": "1789535859",
            "Authorization": f"Bearer {access_token}",
            "X-GA": "v1 1",
            "ReleaseVersion": RELEASE_VER,
            "Content-Type": "application/octet-stream",
            "X-Unity-Version": "2018.4.12f1",
            "Host": "loginbp.ppmainecoonghj.com",
        }
        headers.update(ip_headers())

        r = get_session().post(
            URL_MAJOR_LOGIN,
            headers=headers,
            data=payload,
            verify=False,
            timeout=(3, 6),
        )
        if r.status_code != 200 or not r.content or len(r.content) < 20:
            return None

        body = r.content
        jwt = extract_jwt(body)
        account_id = None

        if jwt and is_valid_jwt(jwt):
            try:
                p = jwt.split(".")[1]
                p += "=" * (4 - len(p) % 4)
                dec = json.loads(base64.urlsafe_b64decode(p))
                account_id = dec.get("account_id") or dec.get("external_id") or dec.get("uid")
            except Exception:
                pass

        if not account_id:
            txt = body.decode("utf-8", errors="ignore")
            nums = re.findall(r"\b\d{10,12}\b", txt)
            if nums:
                account_id = nums[0]

        if account_id:
            return {"account_id": str(account_id), "jwt_token": jwt or ""}
        return None
    except Exception:
        return None


def force_region_bind(region, jwt_token):
    try:
        rc = "RU" if region.upper() == "CIS" else region.upper()
        payload = bytes.fromhex(encrypt_api(build_proto({1: rc}).hex()))
        headers = {
            "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
            "Accept-Encoding": "deflate, gzip",
            "X-GA-SV": "1789535859",
            "Authorization": f"Bearer {jwt_token}",
            "X-GA": "v1 1",
            "ReleaseVersion": RELEASE_VER,
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Unity-Version": "2018.4.12f1",
        }
        headers.update(ip_headers())

        get_session().post(
            URL_NEWBIE_CHOICE,
            data=payload,
            headers=headers,
            timeout=(3, 6),
            verify=False,
        )
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════
#  RARITY
# ═══════════════════════════════════════════════════════════════════════════

def analyze_pattern(account_id):
    try:
        if not account_id or account_id == "N/A" or not str(account_id).isdigit():
            return "", 0
        freq = {}
        for d in str(account_id):
            freq[d] = freq.get(d, 0) + 1
        best = max(freq.values()) if freq else 0
        if best < 4:
            return "", 0
        return f"{max(freq, key=freq.get)}x{best}", best
    except Exception:
        return "", 0


def analyze_unique_pattern(account_id):
    try:
        if not account_id or account_id == "N/A" or not str(account_id).isdigit():
            return False, 0, ""
        aid = str(account_id)
        length = len(aid)
        if length < 6:
            return False, 0, ""
        for pat_len in range(2, (length // 3) + 1):
            if length % pat_len != 0:
                continue
            pattern = aid[:pat_len]
            if len(set(pattern)) == 1:
                continue
            repeat = length // pat_len
            if all(aid[k * pat_len:(k + 1) * pat_len] == pattern for k in range(1, repeat)) and repeat >= 3:
                return True, repeat, pattern
        return False, 0, ""
    except Exception:
        return False, 0, ""


def get_rarity_info(account_id):
    detail, score = analyze_pattern(account_id)
    is_unik, ucount, upair = analyze_unique_pattern(account_id)
    unik_label = f"X{ucount} ({upair})" if (is_unik and ucount >= 3) else ""
    if score >= 8:
        label_ = "EDYAN TENAN"
    elif score >= 7:
        label_ = "GWENDENG"
    elif score >= 5:
        label_ = "APIK NJIR"
    elif score >= 4:
        label_ = "MAYAN"
    else:
        label_ = "COMMON"
    if is_unik and ucount >= 3:
        label_ = f"UNIK {unik_label}"
    return {
        "rarity": label_,
        "rarity_reason": detail,
        "rarity_score": score,
        "is_unik": is_unik,
        "unik_label": unik_label,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  PIPELINE
# ═══════════════════════════════════════════════════════════════════════════

def create_account(region, account_name, password_prefix, is_ghost=False):
    try:
        password = secrets.token_hex(16)

        uid = guest_register(password)
        if not uid:
            record_fail("reg")
            return None

        tok = token_grant(uid, password)
        if not tok:
            record_fail("tok")
            return None
        access_token, open_id = tok

        lang = "pt" if is_ghost else REGION_LANG.get(region.upper(), "en")
        nick = generate_random_name(account_name)
        login = major_register(access_token, open_id, uid, password, region, nick, lang)
        if not login:
            record_fail("major")
            return None

        account_id = login["account_id"]
        jwt = login.get("jwt_token", "")
        final_region = "GHOST" if is_ghost else region.upper()

        if jwt and region.upper() != "BR":
            try:
                force_region_bind(region, jwt)
            except Exception:
                pass

        record_success()
        return {
            "uid": str(uid),
            "password": password,
            "account_id": str(account_id),
            "name": nick,
            "region": final_region,
            "jwt_token": jwt,
            "access_token": access_token,
            "open_id": open_id,
            "is_ghost": is_ghost,
            "status": "success",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception:
        record_fail("major")
        return None


def create_single_account(args):
    """Sekali coba — no retry delay, no sleep."""
    region, name_prefix, pass_prefix, is_ghost = args
    result = create_account(region, name_prefix, pass_prefix, is_ghost)
    if result and result.get("uid"):
        return result
    return None


# ═══════════════════════════════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/")
def home():
    return jsonify({
        "message": "MANZA-DEV API — Big IP Pool + Big UA Pool + Non Stuck",
        "status": "active",
        "release_version": RELEASE_VER,
        "game_version": GAME_VERSION,
        "pools": {
            "ip_pool_size": len(IP_POOL),
            "ua_pool_size": len(USER_AGENTS_POOL),
            "device_models": len(DEVICE_MODELS),
        },
        "config": {
            "region": FORCE_REGION,
            "name_prefix": FORCE_NAME_PREFIX,
            "password_prefix": FORCE_PASS_PREFIX,
        },
        "endpoints": {
            "/gen": "GET  ?count=N&region=ID&ghost=false",
            "/health": "GET  health check",
            "/stats": "GET  statistics",
            "/cleanup": "GET  storage cleanup info (force=true untuk trigger)",
        },
        "max_count": 15,
    })


@app.route("/gen", methods=["GET"])
def generate_accounts():
    start_time = time.time()

    try:
        count = int(request.args.get("count", "1"))
        count = max(1, min(count, 15))
    except Exception:
        count = 1

    region = request.args.get("region", FORCE_REGION).upper()
    is_ghost = request.args.get("ghost", "false").lower() in ("true", "1", "yes")
    name = request.args.get("name", FORCE_NAME_PREFIX)[:4] or FORCE_NAME_PREFIX
    pass_pfx = request.args.get("pass_prefix", FORCE_PASS_PREFIX)

    max_workers = min(count, 10)
    results = []
    attempts = 0
    max_total_attempts = count * 10

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        while len(results) < count and attempts < max_total_attempts:
            needed = count - len(results)
            current_batch = min(needed, max_workers)
            futures = [
                executor.submit(create_single_account, (region, name, pass_pfx, is_ghost))
                for _ in range(current_batch)
            ]
            for future in concurrent.futures.as_completed(futures):
                attempts += 1
                result = future.result()
                if result and result.get("uid"):
                    rarity = get_rarity_info(result.get("account_id", "N/A"))
                    result.update(rarity)
                    results.append(result)
                if len(results) >= count:
                    break

    elapsed = round(time.time() - start_time, 2)

    return jsonify({
        "success": len(results) > 0,
        "total_requested": count,
        "total_created": len(results),
        "attempts_made": attempts,
        "elapsed_sec": elapsed,
        "workers": max_workers,
        "region": region,
        "ghost": is_ghost,
        "ip_pool_used": len(IP_POOL),
        "ua_pool_used": len(USER_AGENTS_POOL),
        "accounts": results,
        "release_version": RELEASE_VER,
    })


@app.route("/health")
def health():
    with STATS_LOCK:
        stats = dict(STATS)
    return jsonify({
        "status": "healthy",
        "release_version": RELEASE_VER,
        "pools": {
            "ip_pool_size": len(IP_POOL),
            "ua_pool_size": len(USER_AGENTS_POOL),
            "device_models": len(DEVICE_MODELS),
        },
        "stats": stats,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.route("/stats")
def stats_route():
    with STATS_LOCK:
        return jsonify(dict(STATS))


# ═══ TAHAP 1 PATCH — ROUTE /cleanup ═══
@app.route("/cleanup", methods=["GET", "POST"])
def cleanup_route():
    if not _CLEANUP_OK:
        return jsonify({"success": False, "error": "cleanup module not loaded"}), 500
    try:
        force = request.args.get("force", "false").lower() in ("true", "1", "yes")
        if force:
            result = run_cleanup()
        else:
            result = get_cleanup_stats()
        return jsonify({"success": True, "cleanup": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
# ═══ END TAHAP 1 PATCH ═══


# ═══════════════════════════════════════════════════════════════════════════
#  WSGI
# ═══════════════════════════════════════════════════════════════════════════

def application(environ, start_response):
    return app(environ, start_response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=False, threaded=True)