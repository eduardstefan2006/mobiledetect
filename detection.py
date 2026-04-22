from __future__ import annotations

import re
from collections import defaultdict

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

    if mac_address and maybe_randomized_mac(mac_address):
        if h and not any(k in h for k in MOBILE_HOSTNAME_PATTERNS):
            return False
        if v and not any(k in v for k in MOBILE_VENDOR_KEYWORDS):
            return False
        if not h and not v:
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
        primary = bucket[0].copy()
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
