from __future__ import annotations

import re
from collections import defaultdict

MOBILE_HOSTNAME_PATTERNS = (
    "iphone",
    "android",
    "samsung",
    "pixel",
    "xiaomi",
    "oneplus",
    "huawei",
    "redmi",
    "galaxy",
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
    h = (hostname or "").lower()
    v = (vendor or "").lower()
    if any(k in h for k in MOBILE_HOSTNAME_PATTERNS):
        return True
    if any(k in v for k in MOBILE_VENDOR_KEYWORDS):
        return True
    if mac_address and maybe_randomized_mac(mac_address):
        return True
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
