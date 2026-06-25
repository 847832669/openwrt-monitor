"""MAC OUI vendor detection and LAN device display helpers."""

from fnmatch import fnmatch
from typing import Any


OUI_PREFIXES = {
    # Apple
    "000393": "Apple",
    "000502": "Apple",
    "000A27": "Apple",
    "000A95": "Apple",
    "000D93": "Apple",
    "001124": "Apple",
    "001451": "Apple",
    "0016CB": "Apple",
    "0017F2": "Apple",
    "0019E3": "Apple",
    "001B63": "Apple",
    "001CB3": "Apple",
    "001D4F": "Apple",
    "001E52": "Apple",
    "001EC2": "Apple",
    "001F5B": "Apple",
    "001FF3": "Apple",
    "0021E9": "Apple",
    "002241": "Apple",
    "002312": "Apple",
    "002332": "Apple",
    "00236C": "Apple",
    "0023DF": "Apple",
    "002436": "Apple",
    "002500": "Apple",
    "00254B": "Apple",
    "0025BC": "Apple",
    "002608": "Apple",
    "00264A": "Apple",
    "0026B0": "Apple",
    "0026BB": "Apple",
    "041E64": "Apple",
    "04DB56": "Apple",
    "086D41": "Apple",
    "0C3E9F": "Apple",
    "109ADD": "Apple",
    "18AF61": "Apple",
    "1C36BB": "Apple",
    "24A160": "Apple",
    "28CFDA": "Apple",
    "2C1F23": "Apple",
    "341298": "Apple",
    "3C0754": "Apple",
    "403004": "Apple",
    "40A6D9": "Apple",
    "482CA0": "Apple",
    "5C5948": "Apple",
    "60F81D": "Apple",
    "68A86D": "Apple",
    "70CD60": "Apple",
    "784F43": "Apple",
    "7C0191": "Apple",
    "84A134": "Apple",
    "8C2937": "Apple",
    "90B21F": "Apple",
    "98E0D9": "Apple",
    "A4C361": "Apple",
    "AC87A3": "Apple",
    "B8E856": "Apple",
    "C0847A": "Apple",
    "CC08E0": "Apple",
    "D0A637": "Apple",
    "DC3714": "Apple",
    "E0ACCB": "Apple",
    "E80688": "Apple",
    "F0D1A9": "Apple",
    "F82793": "Apple",
    # Xiaomi ecosystem
    "0C1DAF": "小米",
    "18F0E4": "小米",
    "185936": "小米",
    "249EAB": "小米",
    "2459E5": "小米",
    "28E347": "小米",
    "34CE00": "小米",
    "38A4ED": "小米",
    "3C5A37": "小米",
    "3CBD3E": "小米",
    "3CCD57": "小米",
    "508F4C": "小米",
    "5C02B5": "小米",
    "64B473": "小米",
    "64CC2E": "小米",
    "7451BA": "小米",
    "78FFCA": "小米",
    "7C1DD9": "小米",
    "8CBE24": "小米",
    "98FAE3": "小米",
    "A086C6": "小米",
    "ACF7F3": "小米",
    "B0E235": "小米",
    "C46AB7": "小米",
    "D4970B": "小米",
    "E4A115": "小米",
    "F0B429": "小米",
    "FC64BA": "小米",
    # Huawei / Honor
    "00E0FC": "华为",
    "001882": "华为",
    "001E10": "华为",
    "001FA4": "华为",
    "00259E": "华为",
    "04BD88": "华为",
    "0819A6": "华为",
    "0C37DC": "华为",
    "104780": "华为",
    "18DED7": "华为",
    "2008ED": "华为",
    "283152": "华为",
    "2CAB00": "华为",
    "346BD3": "华为",
    "38F889": "华为",
    "3C4711": "华为",
    "4846FB": "华为",
    "5425EA": "华为",
    "5C4CA9": "华为",
    "60DE44": "华为",
    "70723C": "华为",
    "78D752": "华为",
    "84A8E4": "华为",
    "8853D4": "华为",
    "9094E4": "华为",
    "A08CFD": "华为",
    "AC4E91": "华为",
    "B0E5ED": "华为",
    "C8D12A": "华为",
    "D07AB5": "华为",
    "E0247F": "华为",
    "F44EFD": "华为",
    # Intel
    "0002B3": "Intel",
    "000347": "Intel",
    "000423": "Intel",
    "0007E9": "Intel",
    "000CF1": "Intel",
    "000E0C": "Intel",
    "000E35": "Intel",
    "001111": "Intel",
    "0012F0": "Intel",
    "001302": "Intel",
    "001320": "Intel",
    "0013CE": "Intel",
    "001500": "Intel",
    "00166F": "Intel",
    "001676": "Intel",
    "0016EA": "Intel",
    "0018DE": "Intel",
    "0019D1": "Intel",
    "001B21": "Intel",
    "001CBF": "Intel",
    "001DE0": "Intel",
    "001E64": "Intel",
    "001E65": "Intel",
    "001F3B": "Intel",
    "001FC6": "Intel",
    "00215C": "Intel",
    "00216A": "Intel",
    "002170": "Intel",
    "0022FA": "Intel",
    "0024D6": "Intel",
    "0024D7": "Intel",
    "0026C6": "Intel",
    "002710": "Intel",
    "0C8BFD": "Intel",
    "1002B5": "Intel",
    "185E0F": "Intel",
    "1C1B0D": "Intel",
    "3CA9F4": "Intel",
    "4851B7": "Intel",
    "58946B": "Intel",
    "5C514F": "Intel",
    "605718": "Intel",
    "685D43": "Intel",
    "6C2995": "Intel",
    "701CE7": "Intel",
    "74E5F9": "Intel",
    "7C67A2": "Intel",
    "801934": "Intel",
    "843A4B": "Intel",
    "887873": "Intel",
    "8C554A": "Intel",
    "9061AE": "Intel",
    "A0510B": "Intel",
    "A4C3F0": "Intel",
    "B46D83": "Intel",
    "C82158": "Intel",
    "D4D252": "Intel",
    "DC5360": "Intel",
    "E4A471": "Intel",
    "F0421C": "Intel",
    "F40669": "Intel",
    "F81654": "Intel",
    # Realtek
    "00E04C": "Realtek",
    "001A3F": "Realtek",
    "001D92": "Realtek",
    "002268": "Realtek",
    "0023CD": "Realtek",
    "002421": "Realtek",
    "002618": "Realtek",
    "107B44": "Realtek",
    "14DAE9": "Realtek",
    "2016D8": "Realtek",
    "24050F": "Realtek",
    "2C4D54": "Realtek",
    "40B034": "Realtek",
    "441CA8": "Realtek",
    "503EAA": "Realtek",
    "54E1AD": "Realtek",
    "645A04": "Realtek",
    "704D7B": "Realtek",
    "74DA38": "Realtek",
    "801F02": "Realtek",
    "8C882B": "Realtek",
    "D85ED3": "Realtek",
    "E0D55E": "Realtek",
    "EC086B": "Realtek",
    "F44D30": "Realtek",
    # Common home network vendors
    "0C722C": "TP-Link",
    "14CC20": "TP-Link",
    "18A6F7": "TP-Link",
    "50C7BF": "TP-Link",
    "54E6FC": "TP-Link",
    "6466B3": "TP-Link",
    "8416F9": "TP-Link",
    "A0F3C1": "TP-Link",
    "B04E26": "TP-Link",
    "C025E9": "TP-Link",
    "C4E984": "TP-Link",
    "E8DE27": "TP-Link",
    "F4F26D": "TP-Link",
    "500FF5": "Tenda",
    "C83A35": "Tenda",
    "D83214": "Tenda",
    "E8F332": "Tenda",
    "10DA43": "NETGEAR",
    "A040A0": "NETGEAR",
    "B03956": "NETGEAR",
    "C03F0E": "NETGEAR",
    "C40415": "NETGEAR",
    "001E58": "D-Link",
    "1CBDB9": "D-Link",
    "340804": "D-Link",
    "B8A386": "D-Link",
    "C0A0BB": "D-Link",
    "60A44C": "ASUS",
    "04D9F5": "ASUS",
    "2C4D54": "ASUS",
    "50465D": "ASUS",
    "AC220B": "ASUS",
    "F07959": "ASUS",
    "B827EB": "Raspberry Pi",
    "DCA632": "Raspberry Pi",
    "E45F01": "Raspberry Pi",
    "240AC4": "Espressif",
    "246F28": "Espressif",
    "2CF432": "Espressif",
    "30AEA4": "Espressif",
    "5CCF7F": "Espressif",
    "7C9EBD": "Espressif",
    "84F3EB": "Espressif",
    "A020A6": "Espressif",
    "ACD074": "Espressif",
    "C44F33": "Espressif",
    "D8F15B": "Espressif",
    # Phones / PCs / media devices
    "ACD618": "OPPO",
    "C4F081": "OPPO",
    "BC1C81": "Samsung",
    "001632": "Samsung",
    "1867B0": "Samsung",
    "24DBED": "Samsung",
    "34BE00": "Samsung",
    "5C0A5B": "Samsung",
    "8C7712": "Samsung",
    "A8F274": "Samsung",
    "C4731E": "Samsung",
    "F0D7AA": "Samsung",
    "3C2EFF": "Microsoft",
    "485073": "Microsoft",
    "7CED8D": "Microsoft",
    "0017F2": "Apple",
    "001B77": "Dell",
    "18DBF2": "Dell",
    "3C2C30": "Dell",
    "D4BED9": "Dell",
    "F8B156": "Dell",
    "001A4B": "HP",
    "3CD92B": "HP",
    "D067E5": "HP",
    "001EEC": "Lenovo",
    "60EB69": "Quanta/Lenovo",
    "A4BB6D": "Lenovo",
    "FC4596": "Sony",
    "001C62": "LG",
    "B4E62D": "LG",
    "F8A45F": "LG",
    "F4F5D8": "Google",
    "A47733": "Google",
    "DCA904": "Amazon",
    "F0272D": "Amazon",
    "001D6A": "Roku",
    "00D0D0": "Vizio",
    "645299": "Sharp",
    "A0369F": "Intelbras",
}


DEFAULT_VENDOR = "未知厂商"
RANDOMIZED_VENDOR = "随机 MAC"

HOST_VENDOR_HINTS = (
    (("oneplus", "one-plus"), "OnePlus"),
    (("oppo", "reno", "find x", "find-x"), "OPPO"),
    (("realme", "rmx"), "realme"),
    (("iqoo", "i-qoo"), "iQOO"),
    (("midea", "美的"), "美的"),
    (("mijia", "miio", "yeelight", "lumi", "chuangmi"), "米家"),
    (("aqara",), "Aqara"),
    (("poco",), "POCO"),
    (("redmi",), "Redmi"),
    (("vivo",), "vivo"),
    (("honor", "magicbook", "荣耀"), "荣耀"),
    (("huawei", "matebook"), "华为"),
    (("xiaomi", "redmi", "mi-", "mibox"), "小米"),
    (("samsung", "galaxy"), "Samsung"),
    (("pixel", "google"), "Google"),
    (("motorola", "moto-"), "Motorola"),
    (("sony", "xperia"), "Sony"),
    (("meizu",), "魅族"),
    (("zte",), "中兴"),
    (("nubia",), "nubia"),
    (("nothing",), "Nothing"),
    (("surface",), "Microsoft"),
    (("thinkpad", "lenovo", "yoga-"), "Lenovo"),
    (("dell", "xps-", "alienware"), "Dell"),
    (("hp-", "hp_", "hewlett"), "HP"),
    (("acer", "predator"), "Acer"),
    (("asus",), "ASUS"),
    (("msi",), "MSI"),
    (("gigabyte", "aorus"), "GIGABYTE"),
    (("synology", "diskstation"), "Synology"),
    (("qnap",), "QNAP"),
    (("terramaster",), "TerraMaster"),
    (("asustor",), "ASUSTOR"),
    (("netgear",), "NETGEAR"),
    (("tenda",), "Tenda"),
    (("linksys",), "Linksys"),
    (("d-link", "dlink"), "D-Link"),
    (("mercusys",), "Mercusys"),
    (("mikrotik",), "MikroTik"),
    (("ubiquiti", "unifi"), "Ubiquiti"),
    (("tplink", "tp-link"), "TP-Link"),
    (("apple", "iphone", "ipad", "macbook"), "Apple"),
    (("epson",), "Epson"),
    (("canon",), "Canon"),
    (("brother",), "Brother"),
    (("hikvision",), "Hikvision"),
    (("dahua",), "Dahua"),
    (("reolink",), "Reolink"),
    (("roku",), "Roku"),
    (("chromecast", "google-tv"), "Google"),
    (("homepod",), "Apple"),
    (("sonos",), "Sonos"),
    (("bose",), "Bose"),
    (("jbl",), "JBL"),
    (("echo", "alexa"), "Amazon"),
    (("kindle", "firetv", "fire-tv"), "Amazon"),
)

BRAND_ICON_HINTS = (
    (("midea", "美的"), "brand-midea"),
    (("mijia", "米家", "miio", "yeelight", "lumi", "chuangmi"), "brand-mijia"),
    (("redmi",), "brand-redmi"),
    (("poco",), "brand-poco"),
    (("xiaomi", "小米", "redmi", "mibox"), "brand-xiaomi"),
    (("honor", "荣耀", "magicbook"), "brand-honor"),
    (("huawei", "华为", "matebook"), "brand-huawei"),
    (("apple", "iphone", "ipad", "macbook"), "brand-apple"),
    (("samsung", "galaxy"), "brand-samsung"),
    (("realme", "rmx"), "brand-realme"),
    (("iqoo", "i-qoo"), "brand-iqoo"),
    (("motorola", "moto-"), "brand-motorola"),
    (("tenda",), "brand-tenda"),
    (("netgear",), "brand-netgear"),
    (("asus",), "brand-asus"),
    (("thinkpad",), "brand-thinkpad"),
    (("dell", "xps-", "alienware"), "brand-dell"),
    (("hp-", "hp_", "hewlett", "pavilion", "envy"), "brand-hp"),
    (("acer", "predator"), "brand-acer"),
    (("msi",), "brand-msi"),
    (("synology", "diskstation"), "brand-synology"),
    (("qnap",), "brand-qnap"),
    (("epson",), "brand-epson"),
    (("canon",), "brand-canon"),
    (("brother",), "brand-brother"),
    (("hikvision",), "brand-hikvision"),
    (("dahua",), "brand-dahua"),
    (("roku",), "brand-roku"),
    (("sonos",), "brand-sonos"),
    (("bose",), "brand-bose"),
    (("tp-link", "tplink"), "brand-tplink"),
    (("oneplus", "one-plus"), "brand-oneplus"),
    (("vivo",), "brand-vivo"),
)

VENDOR_ICON_HINTS = {
    "Acer": "brand-acer",
    "ASUS": "brand-asus",
    "Apple": "brand-apple",
    "Bose": "brand-bose",
    "Brother": "brand-brother",
    "Canon": "brand-canon",
    "Dahua": "brand-dahua",
    "Dell": "brand-dell",
    "Epson": "brand-epson",
    "HP": "brand-hp",
    "Hikvision": "brand-hikvision",
    "MSI": "brand-msi",
    "Motorola": "brand-motorola",
    "NETGEAR": "brand-netgear",
    "OnePlus": "brand-oneplus",
    "POCO": "brand-poco",
    "QNAP": "brand-qnap",
    "Redmi": "brand-redmi",
    "Roku": "brand-roku",
    "Samsung": "brand-samsung",
    "Sonos": "brand-sonos",
    "Synology": "brand-synology",
    "Tenda": "brand-tenda",
    "ThinkPad": "brand-thinkpad",
    "TP-Link": "brand-tplink",
    "vivo": "brand-vivo",
    "iQOO": "brand-iqoo",
    "realme": "brand-realme",
    "华为": "brand-huawei",
    "小米": "brand-xiaomi",
    "米家": "brand-mijia",
    "美的": "brand-midea",
    "荣耀": "brand-honor",
}

HOST_VENDOR_OVERRIDEABLE = {
    DEFAULT_VENDOR,
    RANDOMIZED_VENDOR,
    "OnePlus/OPPO",
    "OPPO",
    "小米",
}

PHONE_KEYWORDS = (
    "iphone", "android", "oneplus", "one-plus", "oppo", "reno", "find x", "find-x",
    "realme", "rmx", "iqoo", "vivo", "redmi", "poco", "huawei", "honor", "荣耀",
    "pixel", "galaxy", "samsung", "sony", "xperia", "motorola", "moto-", "meizu",
    "zte", "nubia", "nothing", "nokia", "phone",
)
TABLET_KEYWORDS = ("ipad", "tablet", "pad", "tab-", "galaxy tab", "surface go")
DESKTOP_KEYWORDS = (
    "desktop", "pc", "workstation", "dell", "alienware", "lenovo", "hp-", "hp_",
    "acer", "msi", "gigabyte", "aorus", "nuc", "mini-pc", "imac", "mac-mini",
)
LAPTOP_KEYWORDS = (
    "laptop", "macbook", "notebook", "thinkpad", "matebook", "magicbook", "surface",
    "xps-", "yoga-", "rog", "tuf", "predator", "envy", "pavilion",
)
TV_KEYWORDS = (
    "tv", "box", "mibox", "roku", "chromecast", "google-tv", "firetv", "fire-tv",
    "shield", "appletv", "apple-tv", "webostv", "bravia", "hisense", "tcl",
)
CAMERA_KEYWORDS = (
    "camera", "cam", "ipc", "hikvision", "dahua", "reolink", "ezviz", "arlo",
    "tapo-c", "wyze",
)
PRINTER_KEYWORDS = ("printer", "print", "epson", "canon", "brother", "xerox", "ricoh")
SPEAKER_KEYWORDS = (
    "speaker", "sound", "audio", "echo", "alexa", "homepod", "sonos", "bose",
    "jbl", "xiaodu", "tmallgenie",
)
NAS_KEYWORDS = (
    "nas", "storage", "synology", "diskstation", "qnap", "terramaster", "asustor",
    "truenas", "freenas", "unraid", "openmediavault",
)
IOT_KEYWORDS = (
    "esp", "plug", "light", "sensor", "iot", "mijia", "miio", "yeelight", "lumi",
    "aqara", "tuya", "tasmota", "shelly", "sonoff", "broadlink", "midea",
    "homeassistant", "home-assistant",
)


def normalize_mac(mac: str) -> str:
    chars = "".join(ch for ch in (mac or "").upper() if ch in "0123456789ABCDEF")
    if len(chars) != 12:
        return (mac or "").upper()
    return ":".join(chars[i:i + 2] for i in range(0, 12, 2))


def mac_prefix(mac: str) -> str:
    normalized = normalize_mac(mac)
    return "".join(normalized.split(":")[:3])


def normalize_oui_prefix(value: str) -> str:
    chars = "".join(ch for ch in (value or "").upper() if ch in "0123456789ABCDEF")
    return chars[:12]


def is_randomized_mac(mac: str) -> bool:
    normalized = normalize_mac(mac)
    try:
        first_octet = int(normalized.split(":")[0], 16)
    except (IndexError, ValueError):
        return False
    return bool(first_octet & 0x02)


def detect_vendor(mac: str, oui_overrides: dict[str, str] | None = None) -> dict[str, Any]:
    normalized = normalize_mac(mac)
    if not normalized or normalized in {"00:00:00:00:00:00", "(INCOMPLETE)"}:
        return {
            "mac": normalized,
            "vendor": DEFAULT_VENDOR,
            "vendor_key": "unknown",
            "oui": "",
            "mac_is_randomized": False,
        }

    if is_randomized_mac(normalized):
        return {
            "mac": normalized,
            "vendor": RANDOMIZED_VENDOR,
            "vendor_key": "randomized",
            "oui": mac_prefix(normalized),
            "mac_is_randomized": True,
        }

    prefix = mac_prefix(normalized)
    vendor = DEFAULT_VENDOR
    for size in (12, 9, 6):
        candidate = normalize_oui_prefix(normalized)[:size]
        if candidate and oui_overrides and candidate in oui_overrides:
            vendor = oui_overrides[candidate]
            break
    else:
        vendor = OUI_PREFIXES.get(prefix, DEFAULT_VENDOR)
    return {
        "mac": normalized,
        "vendor": vendor,
        "vendor_key": vendor.lower().replace("/", "-").replace(" ", "-") if vendor != DEFAULT_VENDOR else "unknown",
        "oui": prefix,
        "mac_is_randomized": False,
    }


def infer_vendor_from_hostname(entry: dict) -> str:
    text = " ".join([
        str(entry.get("hostname") or ""),
        str(entry.get("display_name") or ""),
        str(entry.get("custom_name") or ""),
    ]).lower()

    for keywords, vendor in HOST_VENDOR_HINTS:
        if any(keyword in text for keyword in keywords):
            return vendor
    return ""


def suggest_lan_icon(entry: dict) -> str:
    text = " ".join([
        str(entry.get("hostname") or ""),
        str(entry.get("display_name") or ""),
        str(entry.get("custom_name") or ""),
        str(entry.get("vendor") or ""),
        str(entry.get("ip") or ""),
    ]).lower()

    for keywords, icon in BRAND_ICON_HINTS:
        if any(keyword in text for keyword in keywords):
            return icon

    vendor_icon = VENDOR_ICON_HINTS.get(str(entry.get("vendor") or ""))
    if vendor_icon:
        return vendor_icon

    if any(word in text for word in PHONE_KEYWORDS):
        return "phone"
    if any(word in text for word in TABLET_KEYWORDS):
        return "tablet"
    if any(word in text for word in DESKTOP_KEYWORDS):
        return "desktop"
    if any(word in text for word in LAPTOP_KEYWORDS):
        return "laptop"
    if any(word in text for word in TV_KEYWORDS):
        return "tv"
    if any(word in text for word in CAMERA_KEYWORDS):
        return "camera"
    if any(word in text for word in PRINTER_KEYWORDS):
        return "printer"
    if any(word in text for word in SPEAKER_KEYWORDS):
        return "speaker"
    if any(word in text for word in NAS_KEYWORDS):
        return "nas"
    if any(word in text for word in IOT_KEYWORDS):
        return "iot"
    return "device"


def suggest_device_type(entry: dict) -> str:
    icon = str(entry.get("suggested_icon") or entry.get("icon") or suggest_lan_icon(entry))
    if icon.startswith("brand-"):
        text = " ".join([
            str(entry.get("hostname") or ""),
            str(entry.get("display_name") or ""),
            str(entry.get("vendor") or ""),
        ]).lower()
        if any(word in text for word in TV_KEYWORDS):
            return "media"
        if any(word in text for word in PRINTER_KEYWORDS):
            return "printer"
        if any(word in text for word in CAMERA_KEYWORDS):
            return "camera"
        if any(word in text for word in NAS_KEYWORDS):
            return "storage"
        return "phone"
    return {
        "phone": "phone",
        "tablet": "tablet",
        "desktop": "computer",
        "laptop": "computer",
        "tv": "media",
        "camera": "camera",
        "printer": "printer",
        "speaker": "media",
        "nas": "storage",
        "iot": "home",
    }.get(icon, "device")


def _text_matches(pattern: str, text: str) -> bool:
    pattern = (pattern or "").strip().lower()
    text = (text or "").lower()
    if not pattern:
        return False
    if "*" in pattern or "?" in pattern:
        return fnmatch(text, pattern)
    return pattern in text


def _rule_matches(entry: dict, rule: Any) -> bool:
    match_type = str(getattr(rule, "match_type", "") or "").lower()
    pattern = str(getattr(rule, "pattern", "") or "").strip()
    if not pattern:
        return False

    if match_type == "mac_prefix":
        return normalize_oui_prefix(entry.get("mac", "")).startswith(normalize_oui_prefix(pattern))
    if match_type == "vendor":
        return _text_matches(pattern, str(entry.get("vendor") or ""))
    if match_type == "ip":
        return _text_matches(pattern, str(entry.get("ip") or ""))

    text = " ".join([
        str(entry.get("hostname") or ""),
        str(entry.get("display_name") or ""),
        str(entry.get("custom_name") or ""),
    ])
    return _text_matches(pattern, text)


def apply_custom_recognition_rules(entry: dict, rules: list[Any] | None = None) -> dict:
    for rule in sorted(rules or [], key=lambda item: getattr(item, "priority", 50)):
        if not getattr(rule, "enabled", True):
            continue
        if not _rule_matches(entry, rule):
            continue

        vendor = str(getattr(rule, "vendor", "") or "").strip()
        icon = str(getattr(rule, "icon", "") or "").strip()
        device_type = str(getattr(rule, "device_type", "") or "").strip()
        if vendor:
            entry["vendor"] = vendor[:64]
            entry["vendor_key"] = vendor.lower().replace("/", "-").replace(" ", "-")
        if icon:
            entry["suggested_icon"] = icon[:64]
        if device_type:
            entry["suggested_type"] = device_type[:32]
        entry["recognition_rule"] = {
            "id": getattr(rule, "id", None),
            "name": getattr(rule, "name", "") or getattr(rule, "pattern", ""),
            "match_type": getattr(rule, "match_type", ""),
        }
        break
    return entry


def apply_lan_device_profiles(
    lan_data: dict,
    profiles: dict[str, Any] | None = None,
    rules: list[Any] | None = None,
    oui_overrides: dict[str, str] | None = None,
) -> dict:
    profiles = profiles or {}
    for item in lan_data.get("leases", []):
        normalized_mac = normalize_mac(item.get("mac", ""))
        vendor_info = detect_vendor(normalized_mac, oui_overrides)
        item.update(vendor_info)

        profile = profiles.get(normalized_mac)
        custom_name = getattr(profile, "name", "") if profile else ""
        icon = getattr(profile, "icon", "") if profile else ""
        custom_icon = getattr(profile, "custom_icon", "") if profile else ""
        important = bool(getattr(profile, "important", False)) if profile else False
        note = getattr(profile, "note", "") if profile else ""

        item["custom_name"] = custom_name
        item["display_name"] = custom_name or item.get("hostname") or item.get("ip") or "未知设备"

        hostname_vendor = infer_vendor_from_hostname(item)
        if hostname_vendor and item.get("vendor") in HOST_VENDOR_OVERRIDEABLE:
            item["vendor"] = hostname_vendor
            item["vendor_key"] = hostname_vendor.lower().replace("/", "-").replace(" ", "-")

        item["suggested_icon"] = suggest_lan_icon(item)
        apply_custom_recognition_rules(item, rules)
        item["suggested_type"] = item.get("suggested_type") or suggest_device_type(item)
        item["icon"] = icon or item["suggested_icon"]
        item["custom_icon"] = custom_icon
        item["important"] = important
        item["note"] = note
    return lan_data
