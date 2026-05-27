from __future__ import annotations

import re
from collections import defaultdict

PHONE_OUI_VENDORS: dict[str, str] = {
    # Apple
    "000502": "Apple", "000a27": "Apple", "000a95": "Apple", "001124": "Apple",
    "001451": "Apple", "001cb3": "Apple", "001e52": "Apple", "001ff3": "Apple",
    "0021e9": "Apple", "002332": "Apple", "002408": "Apple", "0025bc": "Apple",
    "002608": "Apple", "003065": "Apple", "04f7e4": "Apple", "086d41": "Apple",
    "0c774b": "Apple", "101c0c": "Apple", "1040f3": "Apple", "14109f": "Apple",
    "18af61": "Apple", "18e7f4": "Apple", "1c91ab": "Apple", "2078f0": "Apple",
    "24240e": "Apple", "246ab7": "Apple", "286ab8": "Apple", "28a02b": "Apple",
    "2cbe08": "Apple", "34c059": "Apple", "38898c": "Apple", "3c0754": "Apple",
    "3ca832": "Apple", "4098ad": "Apple", "40a6d9": "Apple", "44d884": "Apple",
    "48437c": "Apple", "4c57ca": "Apple", "4c7c5f": "Apple", "50eac0": "Apple",
    "547245": "Apple", "5c969d": "Apple", "600308": "Apple", "606944": "Apple",
    "60f445": "Apple", "6476ba": "Apple", "6c4008": "Apple", "6c94f8": "Apple",
    "703eac": "Apple", "70cd60": "Apple", "74e1b6": "Apple", "78ca39": "Apple",
    "7c0191": "Apple", "80be05": "Apple", "843838": "Apple", "8c2937": "Apple",
    "907240": "Apple", "90b0ed": "Apple", "90c1c6": "Apple", "94f6a3": "Apple",
    "9801a7": "Apple", "9810e8": "Apple", "9cf387": "Apple", "a0999b": "Apple",
    "a43135": "Apple", "a4d18c": "Apple", "a82066": "Apple", "a85c2c": "Apple",
    "a8fad8": "Apple", "ac7f3e": "Apple", "b019c6": "Apple", "b065bd": "Apple",
    "b4f0ab": "Apple", "b8098a": "Apple", "b817c2": "Apple", "b8c75d": "Apple",
    "bc52b7": "Apple", "c0847a": "Apple", "c0ccf8": "Apple", "c42c03": "Apple",
    "c82a14": "Apple", "c8bcc8": "Apple", "cc088d": "Apple", "d023db": "Apple",
    "d0817a": "Apple", "d4619d": "Apple", "d88f76": "Apple", "d8a25e": "Apple",
    "dc0c5c": "Apple", "dc86d8": "Apple", "e0accb": "Apple", "e425e7": "Apple",
    "e49adc": "Apple", "e8040b": "Apple", "e8802e": "Apple", "ec3586": "Apple",
    "f01898": "Apple", "f0d1a9": "Apple", "f45c89": "Apple", "f4f15a": "Apple",
    # Samsung
    "001247": "Samsung", "001632": "Samsung", "0017c9": "Samsung", "001a8a": "Samsung",
    "001e7d": "Samsung", "001fe1": "Samsung", "002198": "Samsung", "0022aa": "Samsung",
    "002339": "Samsung", "002490": "Samsung", "0025aa": "Samsung", "0026e8": "Samsung",
    "040ecf": "Samsung", "08d4f6": "Samsung", "0c1420": "Samsung", "18227e": "Samsung",
    "1c62b8": "Samsung", "205476": "Samsung", "24c696": "Samsung", "283928": "Samsung",
    "300b8e": "Samsung", "340386": "Samsung", "38aa3c": "Samsung", "3c5a54": "Samsung",
    "400e85": "Samsung", "44571d": "Samsung", "484df0": "Samsung", "4c3c16": "Samsung",
    "5001bb": "Samsung", "5492be": "Samsung", "5c0a5b": "Samsung", "60a4d0": "Samsung",
    "6477b1": "Samsung", "68ebbe": "Samsung", "70f927": "Samsung", "7445c3": "Samsung",
    "781fdb": "Samsung", "84254b": "Samsung", "8843e1": "Samsung", "8c7712": "Samsung",
    "90187c": "Samsung", "940b19": "Samsung", "9852b5": "Samsung", "9c0298": "Samsung",
    "a007c0": "Samsung", "a4ebd3": "Samsung", "a80600": "Samsung", "b072bf": "Samsung",
    "b43a28": "Samsung", "bc20a4": "Samsung", "c0bdd1": "Samsung", "c44202": "Samsung",
    "c4576e": "Samsung", "c81479": "Samsung", "cc07ab": "Samsung", "d022be": "Samsung",
    "d4e8b2": "Samsung", "d857ef": "Samsung", "dc7196": "Samsung", "e440e2": "Samsung",
    "e8e5d6": "Samsung", "ec9bf3": "Samsung", "f05a09": "Samsung", "f47b5e": "Samsung",
    "f877b8": "Samsung", "fc1947": "Samsung",
    # Xiaomi / Redmi / POCO
    "002802": "Xiaomi", "0c1daf": "Xiaomi", "142a5b": "Xiaomi", "18595f": "Xiaomi",
    "28e31f": "Xiaomi", "34ce00": "Xiaomi", "382591": "Xiaomi", "3c7aa0": "Xiaomi",
    "40a0dc": "Xiaomi", "4c4994": "Xiaomi", "506413": "Xiaomi", "58443d": "Xiaomi",
    "64b473": "Xiaomi", "6c5ab5": "Xiaomi", "74ffc7": "Xiaomi", "7c1dd9": "Xiaomi",
    "88c3cf": "Xiaomi", "8c7ce2": "Xiaomi", "987b30": "Xiaomi", "9c99a0": "Xiaomi",
    "a086c6": "Xiaomi", "a46be6": "Xiaomi", "b0a7f3": "Xiaomi", "c80fea": "Xiaomi",
    "d0518f": "Xiaomi", "f0b429": "Xiaomi", "fc64ba": "Xiaomi",
    # Huawei / Honor
    "001e10": "Huawei", "0022a1": "Huawei", "00259e": "Huawei", "00e0fc": "Huawei",
    "042ae2": "Huawei", "04bd70": "Huawei", "04f938": "Huawei", "087a4c": "Huawei",
    "0c96bf": "Huawei", "18cf5e": "Huawei", "1c8e5c": "Huawei", "28312b": "Huawei",
    "2c9d1e": "Huawei", "3401fb": "Huawei", "38bc01": "Huawei", "3cc397": "Huawei",
    "40cbaa": "Huawei", "48db50": "Huawei", "4c8bf4": "Huawei", "502284": "Huawei",
    "5448de": "Huawei", "587f66": "Huawei", "60de44": "Huawei", "6416f0": "Huawei",
    "6c8d37": "Huawei", "704a0e": "Huawei", "748966": "Huawei", "7c1cf1": "Huawei",
    "803012": "Huawei", "842888": "Huawei", "88a2d7": "Huawei", "8c34fd": "Huawei",
    "9017ac": "Huawei", "942273": "Huawei", "9c37f4": "Huawei", "a47b2f": "Huawei",
    "a8ca89": "Huawei", "ac4ede": "Huawei", "b035b5": "Huawei", "b4430d": "Huawei",
    "bc7670": "Huawei", "c0bfc0": "Huawei", "c43a35": "Huawei", "c81450": "Huawei",
    "ccca61": "Huawei", "d09466": "Huawei", "d46aa8": "Huawei", "dca553": "Huawei",
    "e03e44": "Huawei", "e4c2d1": "Huawei", "e8cd2d": "Huawei", "fc4819": "Huawei",
    # Motorola
    "000a28": "Motorola", "001374": "Motorola", "001e56": "Motorola",
    "0023ab": "Motorola", "002478": "Motorola", "003a9a": "Motorola",
    "04d3cf": "Motorola", "14761a": "Motorola", "1c8810": "Motorola",
    "24da9b": "Motorola", "28d244": "Motorola", "3480b3": "Motorola",
    "3c2854": "Motorola", "44804f": "Motorola", "4cc7d9": "Motorola",
    "60bf1a": "Motorola", "74a78e": "Motorola", "846a0d": "Motorola",
    "88d7f6": "Motorola", "984b4a": "Motorola", "9c3426": "Motorola",
    "a07b4e": "Motorola", "b0f9e4": "Motorola", "c4640a": "Motorola",
    "d8b377": "Motorola", "e063e5": "Motorola", "f04da2": "Motorola",
    # Google
    "043d7e": "Google", "1c97c5": "Google", "20df77": "Google", "40349c": "Google",
    "486592": "Google", "54607e": "Google", "70d6bf": "Google", "9cf370": "Google",
    "a47a52": "Google", "a4c67f": "Google", "f80e42": "Google",
    # OnePlus
    "041680": "OnePlus", "10491f": "OnePlus", "2017fb": "OnePlus",
    "2465d4": "OnePlus", "44004d": "OnePlus", "5440ad": "OnePlus",
    "64680c": "OnePlus", "90e47a": "OnePlus", "a46f21": "OnePlus",
    "b0f4ef": "OnePlus", "c8f750": "OnePlus",
    # OPPO / Realme
    "001999": "OPPO", "18e2c2": "OPPO", "1c77f6": "OPPO", "2c1d45": "OPPO",
    "3c8d20": "OPPO", "40a1d9": "OPPO", "4c1075": "OPPO", "4cfca5": "OPPO",
    "544d42": "OPPO", "60d7e3": "OPPO", "6c5c14": "OPPO", "7c8bca": "OPPO",
    "8440fc": "OPPO", "8c73fa": "OPPO", "9459cb": "OPPO", "98035b": "OPPO",
    "a89f18": "OPPO", "b441e3": "OPPO", "cc83cd": "OPPO", "d4504f": "OPPO",
    "dc724e": "OPPO", "e0f6b5": "OPPO",
    # Vivo
    "207c8f": "Vivo", "285f30": "Vivo", "38c98f": "Vivo", "487345": "Vivo",
    "4c7ab5": "Vivo", "5829ae": "Vivo", "5c0fa0": "Vivo", "68f728": "Vivo",
    "74cc2c": "Vivo", "7ce5c4": "Vivo", "90a4a5": "Vivo", "a00b86": "Vivo",
    "a4b9b4": "Vivo", "c0f2fb": "Vivo", "d41b81": "Vivo", "e4c08e": "Vivo",
    # Nokia / HMD
    "20ab37": "Nokia", "24b6fd": "Nokia", "2c3386": "Nokia", "30e1c5": "Nokia",
    "5810e7": "Nokia", "685a11": "Nokia", "7c84c1": "Nokia", "803719": "Nokia",
    "90f1aa": "Nokia", "a04f16": "Nokia", "b4864a": "Nokia",
    # Sony
    "001a75": "Sony", "001bfb": "Sony", "001e8c": "Sony", "002345": "Sony",
    "08d4db": "Sony", "0c74a7": "Sony", "10cef9": "Sony", "1811ae": "Sony",
    "20677c": "Sony", "2c5f20": "Sony", "3c7e93": "Sony", "40b837": "Sony",
    "4c21d0": "Sony", "5c515b": "Sony", "60455b": "Sony", "78843c": "Sony",
    "7c9a54": "Sony", "84cf93": "Sony", "8c0dba": "Sony", "90c795": "Sony",
    "9c5cf9": "Sony", "a8d8f8": "Sony", "b4527e": "Sony", "bc4cc4": "Sony",
    "c489b7": "Sony", "ccfab2": "Sony", "d0579e": "Sony", "e4c5d5": "Sony",
    # LG
    "001e75": "LG", "003214": "LG", "04d6aa": "LG", "10684b": "LG",
    "20213a": "LG", "288a1c": "LG", "30766f": "LG", "3ccd93": "LG",
    "40b091": "LG", "404e36": "LG", "488a0c": "LG", "502bf6": "LG",
    "54b80a": "LG", "5c4ca9": "LG", "5c70a3": "LG", "64899a": "LG",
    "64bc0c": "LG", "7010c3": "LG", "743877": "LG", "78f882": "LG",
    "8c3b13": "LG", "8c7e75": "LG", "90e6ba": "LG", "94653f": "LG",
    "a0916e": "LG", "a87750": "LG", "b4079a": "LG", "b4e6df": "LG",
    "bc4760": "LG", "c025e9": "LG", "c4d987": "LG", "cc94d3": "LG",
    "dc0b30": "LG", "e0cbee": "LG", "e81132": "LG", "f06ff2": "LG",
    "f802d4": "LG",
}

MOBILE_HOSTNAME_PATTERNS = (
    # Phones
    "iphone",
    "android",
    "samsung",
    "pixel",
    "xiaomi",
    "oneplus",
    "huawei",
    "redmi",
    "galaxy",
    "a54",
    "a53",
    "a52",
    "a51",
    "a50",
    "a34",
    "a33",
    "a32",
    "a23",
    "a22",
    "a21",
    "a20",
    "a14",
    "a13",
    "a12",
    "s22",
    "s23",
    "s24",
    "s25",
    "motorola",
    "moto",
    "nokia",
    "oppo",
    "vivo",
    "realme",
    "infinix",
    "tecno",
    "itel",
    "poco",
    "mi-",
    "mi_",
    # Tablets
    "ipad",
    "tablet",
    "tab-",
    "tab_",
    "galaxytab",
    "galaxy-tab",
    "mediapad",
    "matepad",
    "lenovo-tab",
    "fire-",
    "kindle",
    # Smartwatches
    "watch",
    "smartwatch",
    "garmin",
    "fitbit",
    "amazfit",
    # Common MikroTik hostname suffixes
    "-al-utilizatorului-",
    "-ul-lui-",
    "-ul-ei-",
)

MOBILE_VENDOR_KEYWORDS = (
    "apple",
    "samsung",
    "google",
    "xiaomi",
    "huawei",
    "oneplus",
    "motorola",
    "oppo",
    "vivo",
    "sony",
    "nokia",
    "realme",
    "infinix",
    "tecno",
    "garmin",
    "fitbit",
    "amazfit",
    "fossil",
    "zte",
    "alcatel",
    "wiko",
    "meizu",
)

NON_MOBILE_HOSTNAME_PATTERNS = (
    "-pc",
    "-desktop",
    "-laptop",
    "pc-",
    "desktop-",
    "laptop-",
    # Apple laptops
    "macbook",
    # ASUS laptops
    "vivobook",
    "zenbook",
    "rog-",
    "tuf-",
    "expertbook",
    # Lenovo laptops
    "thinkpad",
    "ideapad",
    "yoga",
    "legion",
    # Dell laptops
    "latitude",
    "inspiron",
    "xps-",
    "vostro",
    "alienware",
    # HP laptops
    "pavilion",
    "elitebook",
    "probook",
    "spectre",
    "envy-",
    "omen-",
    "zbook",
    # Huawei laptops
    "matebook",
    # Microsoft
    "surface-",
    # Acer laptops
    "swift-",
    "aspire",
    "nitro-",
    # Other laptops
    "chromebook",
    "gram-",
    # Printers
    "canon",
    "epson",
    "kyocera",
    "ricoh",
    "brother-",
    "xerox",
    "konica",
    "lexmark",
    "printer",
    "camera",
    "nvr",
    "dvr",
    "router",
    "switch",
    "ap-",
    "access-point",
    "server",
    "nas-",
    "mikrotik",
    "ubiquiti",
    "projector",
    "smartboard",
    "sbid",
    "tv-",
    "-tv",
    # Infrastructure and servers
    "pihole",
    "pi-hole",
    "raspberry",
    "raspi",
    "resurseumane",
    "resurseum",
    "proxmox",
    "homeassistant",
    "home-assistant",
    "synology",
    "qnap",
    "unraid",
    "pfsense",
    "opnsense",
    "esxi",
    "vmware",
    "hyperv",
    "docker",
    "ubuntu",
    "debian",
    "centos",
    "fedora",
    "windows",
    "win-",
    "-win",
    "srv-",
    "-srv",
    "host-",
    "-host",
    "node-",
    "-node",
    "wlan",
    "eth0",
    "ens",
    "enp",
)


def normalize_mac(raw_mac: str | None) -> str | None:
    if not raw_mac:
        return None
    only_hex = re.sub(r"[^0-9a-fA-F]", "", raw_mac)
    if len(only_hex) != 12:
        return None
    pairs = [only_hex[i : i + 2].lower() for i in range(0, 12, 2)]
    return ":".join(pairs)


def normalize_hostname(hostname: str | None) -> str | None:
    if not hostname:
        return None
    name = hostname.strip()
    return name if name else None


def vendor_from_oui(mac_address: str | None) -> str | None:
    """Returnează numele producătorului din OUI-ul MAC sau None dacă MAC-ul este invalid."""
    if not mac_address:
        return None
    oui = mac_address.replace(":", "").replace("-", "").lower()[:6]
    if len(oui) < 6:
        return None
    return PHONE_OUI_VENDORS.get(oui)


def vendor_from_client_id(client_id: str | None) -> str | None:
    """Extrage indicii de vendor din câmpul client-id DHCP."""
    if not client_id:
        return None
    cid = client_id.lower().strip()
    if "apple" in cid:
        return "Apple"
    if "iphone" in cid or "ios" in cid:
        return "Apple"
    if "android" in cid:
        return "Android"
    if "samsung" in cid:
        return "Samsung"
    if "xiaomi" in cid or "miui" in cid:
        return "Xiaomi"
    if "huawei" in cid:
        return "Huawei"
    return None


def is_phone_device(
    hostname: str | None,
    vendor: str | None,
    mac_address: str | None = None,
) -> bool:
    h = (hostname or "").lower().strip()
    v = (vendor or "").lower().strip()

    if h and any(k in h for k in NON_MOBILE_HOSTNAME_PATTERNS):
        return False
    if h and any(k in h for k in MOBILE_HOSTNAME_PATTERNS):
        return True
    if v and any(k in v for k in MOBILE_VENDOR_KEYWORDS):
        return True

    oui_vendor = vendor_from_oui(mac_address)
    if oui_vendor:
        oui_v = oui_vendor.lower()
        if any(k in oui_v for k in MOBILE_VENDOR_KEYWORDS):
            return True

    if mac_address and maybe_randomized_mac(mac_address):
        if not h and not v and not oui_vendor:
            return False

    return False


def maybe_randomized_mac(mac_address: str) -> bool:
    """Locally-administered bit indicates potential randomized MAC."""
    first_octet = int(mac_address.split(":")[0], 16)
    return bool(first_octet & 0b10)


def deduplicate_records(records: list[dict]) -> list[dict]:
    """
    De-duplicate across routers by stable key.
    - Prefer MAC when available and non-randomized.
    - Fallback to hostname correlation for randomized MACs.
    """
    grouped: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        mac = rec.get("mac_address")
        hostname = (rec.get("hostname") or "").strip().lower()

        if mac and not maybe_randomized_mac(mac):
            key = f"mac:{mac}"
        elif hostname:
            key = f"host:{hostname}"
        else:
            key = f"fallback:{rec.get('router_ip')}:{rec.get('ip_address')}"
        grouped[key].append(rec)

    merged: list[dict] = []
    for bucket in grouped.values():
        def record_score(row: dict) -> tuple[int, int, int, int]:
            hostname = (row.get("hostname") or "").strip()
            vendor = (row.get("vendor") or "").strip()
            mac = row.get("mac_address")

            phone_signal = int(is_phone_device(hostname, vendor, mac))
            has_vendor = int(bool(vendor))
            has_hostname = int(bool(hostname))
            stable_mac = int(bool(mac and not maybe_randomized_mac(mac)))
            return (phone_signal, has_vendor, has_hostname, stable_mac)

        primary = max(bucket, key=record_score).copy()
        primary["sources"] = [
            {
                "ip_address": row.get("ip_address"),
                "vlan": row.get("dhcp_server"),
                "router_ip": row.get("router_ip"),
            }
            for row in bucket
        ]
        merged.append(primary)
    return merged
