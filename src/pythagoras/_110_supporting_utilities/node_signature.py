"""
Generate a stable, privacy-preserving, globally unique identifier for the
machine (or container / VM) running this Python process.

Why this exists
---------------
Traditional identifiers such as MAC addresses or hostnames are no longer
reliable:

* MACs can be randomised, duplicated in clones, or absent in cloud instances.
* Hostnames/usernames collide constantly (think *ubuntu*, *Administrator*).
* OS fingerprints change after upgrades and add negligible entropy.

Instead, this module builds an identifier from a hierarchy of signals that are
both stable and widely available:

1. Native operating-system machine ID
   • ``/etc/machine-id``, Windows ``MachineGuid``, macOS ``IOPlatformUUID``
2. Cloud instance ID (AWS, GCP, Azure metadata services)
3. Hardware UUID exposed via SMBIOS
4. First globally-administered MAC address (falls back only if it is not
   “locally administered”)
5. Persisted random UUID stored in system or user directory – guarantees
   determinism when everything else fails

The selected signals are not returned directly. A candidate is chosen, a
version string is included as part of the payload, then the result is hashed
with SHA‑256 and encoded using this project's base32 alphabet (``0-9`` then
``a-v``). The output is an opaque signature with extremely low collision
probability across large fleets.

Public API
----------
get_node_signature() → str
    Return the string identifier for the current node. The result is memoised
    (``functools.cache``) for the lifetime of the Python process.

Internal helpers beginning with an underscore are not part of the public
contract and may change without notice.
"""

from __future__ import annotations
import os
import platform
import subprocess
import uuid
from functools import cache
from pathlib import Path
import re
from typing import Callable
from urllib import request
from urllib.error import URLError, HTTPError

from .constants_for_signatures_and_converters import PTH_METADATA_TIMEOUT, PTH_METADATA_READ_LIMIT, PTH_APP_NAME
from .constants_for_signatures_and_converters import SMBIOS_UUID_PATH, PTH_NODE_SIGNATURE_VERSION
from .hash_signature import get_hash_signature


# --- helpers ------------------------------------------------------

def _read_first(path: str) -> str | None:
    """Read up to PTH_METADATA_READ_LIMIT bytes from a file.

    Returns None if the file cannot be read or is empty.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read(PTH_METADATA_READ_LIMIT).strip() or None
    except Exception:
        return None

def _run(cmd: list[str]) -> str | None:
    """Execute a command and return its stdout, or None on any failure."""
    try:
        result = subprocess.check_output(cmd, text=True, timeout=PTH_METADATA_TIMEOUT)
        result = result.strip()
        return result or None
    except Exception:
        return None

def _linux_machine_id() -> str | None:
    """Retrieve the machine ID on Linux from standard locations."""
    return _read_first("/etc/machine-id") or _read_first("/var/lib/dbus/machine-id")

def _windows_machine_guid() -> str | None:
    """Retrieve the MachineGuid from the Windows Registry."""
    if platform.system() != "Windows":
        return None
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
            access=winreg.KEY_READ | winreg.KEY_WOW64_64KEY
        ) as h:
            return winreg.QueryValueEx(h, "MachineGuid")[0]
    except Exception:
        return None

def _mac_platform_uuid() -> str | None:
    """Retrieve the IOPlatformUUID on macOS using ioreg."""
    if platform.system() != "Darwin":
        return None
    try:
        output = _run(["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"])
        if not output:
            return None
        # Extract UUID from output like: "IOPlatformUUID" = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
        match = re.search(r'"IOPlatformUUID"\s*=\s*"([^"]+)"', output)
        return match.group(1) if match else None
    except Exception:
        return None


def _os_machine_id() -> str | None:
    """Dispatch to the correct OS-specific identifier logic."""
    system = platform.system()
    if system == "Linux":
        return _linux_machine_id()
    if system == "Windows":
        return _windows_machine_guid()
    if system == "Darwin":
        return _mac_platform_uuid()
    return None


def _is_non_trivial_id(value: str | None) -> str | None:
    """Return stripped value if valid; return None if empty or trivial (e.g. all zeros)."""
    if not value:
        return None
    stripped_value = value.strip()
    if not stripped_value:
        return None

    # Remove common separators (hyphens, colons, curly braces) for the check
    clean_str = re.sub(r'[^0-9a-zA-Z]', '', stripped_value).lower()

    # If the ID was purely special chars (unlikely) or empty after cleaning, treat as empty
    if not clean_str:
        return None

    if all(char == "0" for char in clean_str) or all(char == "f" for char in clean_str):
        return None

    return stripped_value

def _http_get_metadata(url: str, headers: dict[str, str]) -> str | None:
    """Fetch metadata from a URL with specified headers and a timeout."""
    try:
        req = request.Request(url, headers=headers)
        with request.urlopen(req, timeout=PTH_METADATA_TIMEOUT) as resp:
            if resp.status != 200:
                return None
            data = resp.read(PTH_METADATA_READ_LIMIT)
            if not data:
                return None
            return data.decode(errors="ignore").strip() or None
    except (URLError, HTTPError, TimeoutError, OSError, Exception):
        return None


def _cloud_instance_id() -> str | None:
    """Retrieve instance ID from local hypervisor or cloud metadata services (AWS, GCP, Azure)."""
    hypervisor_uuid_path = Path("/sys/hypervisor/uuid")
    if hypervisor_uuid_path.exists():
        hypervisor_uuid = _is_non_trivial_id(_read_first(str(hypervisor_uuid_path)))
        if hypervisor_uuid:
            return hypervisor_uuid

    meta_urls = [
        ("AWS", "http://169.254.169.254/latest/meta-data/instance-id", {}),
        ("GCP", "http://metadata.google.internal/computeMetadata/v1/instance/id", {"Metadata-Flavor": "Google"}),
        ("AZURE", "http://169.254.169.254/metadata/instance/compute/vmId?api-version=2021-02-01", {"Metadata": "true"}),
    ]

    for _, url, headers in meta_urls:
        candidate = _is_non_trivial_id(_http_get_metadata(url, headers))
        if candidate:
            return candidate
    return None

def _local_cloud_id() -> str | None:
    """Fast check for cloud-init instance ID.

    This resolves identity for cloned VMs where /etc/machine-id might be stale.
    """
    return _read_first("/var/lib/cloud/data/instance-id")

def _stable_mac() -> str | None:
    """Return the first hardware MAC address if it is universally administered."""
    mac = uuid.getnode()
    if not mac:
        return None
    first_octet = (mac >> 40) & 0xFF
    if first_octet & 0x02:  # locally-administered bit set → likely random
        return None
    if first_octet & 0x01:  # multicast bit → not a unicast hardware MAC
        return None
    return _is_non_trivial_id(f"{mac:012x}")


def _system_node_id_path() -> Path:
    """Determine the platform-specific path for a system-wide node ID file."""
    if platform.system() == "Windows":
        root = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
        return root / PTH_APP_NAME / "node-id"
    elif platform.system() == "Darwin":
        return Path("/Library/Application Support") / PTH_APP_NAME / "node-id"
    else:                                   # Linux / *BSD / etc.
        return Path("/var/lib") / PTH_APP_NAME / "node-id"

def _fallback_user_path() -> Path:
    """Determine the path for a user-specific node ID file."""
    return Path.home() / f".{PTH_APP_NAME}" / "node-id"


def _persistent_random() -> str | None:
    """Retrieve or create a persistent random node ID (system-wide or user-local)."""
    for candidate in (_system_node_id_path(), _fallback_user_path()):
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)

            # Try to read existing file first
            if candidate.exists():
                content = candidate.read_text().strip()
                if content:  # Validate non-empty
                    return content
                # Empty file detected - regenerate
                rid = uuid.uuid4().hex
                candidate.write_text(rid)
                return rid

            # Atomic create-if-not-exists
            rid = uuid.uuid4().hex
            try:
                with open(candidate, 'x') as f:
                    f.write(rid)
                return rid
            except FileExistsError:
                # Another process won the race, read their value
                content = candidate.read_text().strip()
                if content:
                    return content
                # Empty file - overwrite it
                rid = uuid.uuid4().hex
                candidate.write_text(rid)
                return rid
        except (PermissionError, OSError):
            continue

    return None

# --- public API ---------------------------------------------------

@cache
def get_node_signature() -> str:
    """Return a unique, persistent, opaque identifier for the execution host.

    The signature is a string that uniquely identifies the machine running the
    code. It is designed to be stable, globally unique, portable, and
    privacy-preserving.

    Design Goals:
        - Stability: Remains the same across reboots, network changes, and OS
          upgrades.
        - Global uniqueness: Collision probability ~ 10^-20 even with billions
          of nodes.
        - Portability: Works on bare-metal, VMs, containers, and major public
          clouds.
        - Privacy: Exposes no raw system details; only a salted SHA-256 digest
          is returned.

    Signal Sources (first non-empty source wins):
        0. Local Cloud-Init ID (fastest check for cloned VMs).
        1. OS machine identifier:
            - /etc/machine-id (Linux)
            - HKLM\\...\\MachineGuid (Windows)
            - IOPlatformUUID (macOS)
        2. Cloud instance-ID (AWS / GCP / Azure metadata services).
        3. Hardware UUID from SMBIOS (/sys/class/dmi/id/product_uuid).
        4. First globally-administered MAC address.
        5. Persistent random UUID stored in system or user directory.

    Algorithm:
        1. Iterate through signal sources in priority order.
        2. Select the first available (non-empty) signal.
        3. Include the scheme version string (currently ``"version 2"``)
           in the payload.
        4. Calculate the base32 hash signature.

    Returns:
        A string representing the node signature.

    Note:
        The result is cached for the lifetime of the Python process.
    """
    signal_suppliers: tuple[Callable[[], str | None], ...] = (
        _local_cloud_id,
        _os_machine_id,
        _cloud_instance_id,
        lambda: _read_first(SMBIOS_UUID_PATH),
        _stable_mac,
        _persistent_random)

    chosen_signal = ""
    for supplier in signal_suppliers:
        candidate = _is_non_trivial_id(supplier())
        if candidate:
            chosen_signal = candidate
            break

    if not chosen_signal:
        return "signatureless_node_signatureless"

    payload: list[str] = [PTH_NODE_SIGNATURE_VERSION, chosen_signal]
    return get_hash_signature(payload)