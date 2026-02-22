"""Samsung TV remote control via encrypted WebSocket (2014 H-series).

Protocol based on SmartCrypto/IPRemote for H-series (2014) Samsung TVs.
Uses AES-encrypted commands over Socket.IO on port 8000,
with pairing via HTTP on port 8080.
"""

import binascii
import hashlib
import json
import socket
import struct
import time

import requests
import websocket as ws_module
from Crypto.Cipher import AES

from xml.etree import ElementTree as ET

from lib._rijndael import encrypt as _rijndael_encrypt
from lib.config import (
    TV_IP, TV_MAC_SOURCE, TV_MAC_SOURCE_ID, TV_TOKEN_PATH, TV_UPNP_PORT,
)

# --- Crypto constants (from SmartCrypto) ---

_PUBLIC_KEY = (
    "2cb12bb2cbf7cec713c0fff7b59ae68a96784ae517f41d259a45d20556177c0ffe951ca60"
    "ec03a990c9412619d1bee30adc7773088c5721664cffcedacf6d251cb4b76e2fd7aef09b3"
    "ae9f9496ac8d94ed2b262eee37291c8b237e880cc7c021fb1be0881f3d0bffa4234d3b8e6"
    "a61530c00473ce169c025f47fcc001d9b8051"
)
_PRIVATE_KEY = (
    "2fd6334713816fae018cdee4656c5033a8d6b00e8eaea07b3624999242e96247112dcd019"
    "c4191f4643c3ce1605002b2e506e7f1d1ef8d9b8044e46d37c0d5263216a87cd783aa1854"
    "90436c4a0cb2c524e15bc1bfeae703bcbc4b74a0540202e8d79cadaae85c6f9c218bc1107"
    "d1f5b4b9bd87160e782f4e436eeb17485ab4d"
)
_WB_KEY = "abbb120c09e7114243d1fa0102163b27"
_TRANS_KEY = "6c9474469ddf7578f3e5ad8a4c703d99"
_PRIME = (
    "b361eb0ab01c3439f2c16ffda7b05e3e320701ebee3e249123c3586765fd5bf6c1dfa88bb"
    "6bb5da3fde74737cd88b6a26c5ca31d81d18e3515533d08df619317063224cf0943a2f29a"
    "5fe60c1c31ddf28334ed76a6478a1122fb24c4a94c8711617ddfe90cf02e643cd82d4748d"
    "6d4a7ca2f47d88563aa2baf6482e124acd7dd"
)

_APP_ID = "654321"
_DEVICE_ID = "7e509404-9d7c-46b4-8f6a-e2a9668ad184"
_USER_ID = "654321"
_BLOCK_SIZE = 16
_SHA_DIGEST_LENGTH = 20


class TVError(Exception):
    """Raised when a TV command fails."""


# --- Crypto helpers ---

def _sha1(*parts: bytes) -> bytes:
    """Compute SHA-1 digest over concatenated parts."""
    h = hashlib.sha1()
    for p in parts:
        h.update(p)
    return h.digest()


def _bytes2str(data):
    return data.decode("utf-8") if isinstance(data, bytes) else data


def _encrypt_param(data):
    """AES-ECB encrypt with whitebox key (128 bytes)."""
    cipher = AES.new(binascii.unhexlify(_WB_KEY), AES.MODE_ECB)
    return cipher.encrypt(data)


def _decrypt_param(data):
    """AES-ECB decrypt with whitebox key (128 bytes)."""
    cipher = AES.new(binascii.unhexlify(_WB_KEY), AES.MODE_ECB)
    return cipher.decrypt(data)


def _samy_go_transform(data):
    """Reduced-round Rijndael (3 rounds) with transform key."""
    return _rijndael_encrypt(binascii.unhexlify(_TRANS_KEY), data)


def _generate_server_hello(user_id, pin):
    aes_key = _sha1(pin.encode("utf-8"))[:16]
    iv = b"\x00" * _BLOCK_SIZE
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(binascii.unhexlify(_PUBLIC_KEY))
    swapped = _encrypt_param(encrypted)
    data = struct.pack(">I", len(user_id)) + user_id.encode("utf-8") + swapped
    data_hash = _sha1(data)
    server_hello = (
        b"\x01\x02"
        + b"\x00" * 5
        + struct.pack(">I", len(user_id) + 132)
        + data
        + b"\x00" * 5
    )
    return {"serverHello": server_hello, "hash": data_hash, "AES_key": aes_key}


def _parse_client_hello(client_hello_hex, data_hash, aes_key, user_id):
    GX_SIZE = 0x80
    data = binascii.unhexlify(client_hello_hex)
    user_id_len = struct.unpack(">I", data[11:15])[0]
    third_len = user_id_len + 132
    dest = data[11 : third_len + 11] + data_hash
    client_user_id = data[15 : user_id_len + 15]
    enc_wb_gx = data[15 + user_id_len : GX_SIZE + 15 + user_id_len]
    enc_gx = _decrypt_param(enc_wb_gx)
    iv = b"\x00" * _BLOCK_SIZE
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    gx = cipher.decrypt(enc_gx)

    bn_gx = int(_bytes2str(binascii.hexlify(gx)), 16)
    bn_prime = int(_PRIME, 16)
    bn_private = int(_PRIVATE_KEY, 16)
    secret_hex = hex(pow(bn_gx, bn_private, bn_prime)).rstrip("L").lstrip("0x")
    secret_hex = ((len(secret_hex) % 2) * "0") + secret_hex
    secret = binascii.unhexlify(secret_hex)

    start = 15 + user_id_len + GX_SIZE
    hash2 = data[start : start + _SHA_DIGEST_LENGTH]
    hash3 = _sha1(client_user_id + secret)
    if hash2 != hash3:
        return None  # wrong PIN

    flag_pos = user_id_len + 15 + GX_SIZE + _SHA_DIGEST_LENGTH
    if ord(data[flag_pos : flag_pos + 1]):
        return None
    if struct.unpack(">I", data[flag_pos + 1 : flag_pos + 5])[0]:
        return None

    final = (
        client_user_id
        + user_id.encode("utf-8")
        + gx
        + binascii.unhexlify(_PUBLIC_KEY)
        + secret
    )
    sk_prime = _sha1(final)
    ctx = _samy_go_transform(_sha1(sk_prime + b"\x00")[:16])
    return {"ctx": ctx, "SKPrime": sk_prime}


def _generate_server_ack(sk_prime):
    h = _sha1(sk_prime + b"\x01")
    return (
        "0103000000000000000014"
        + _bytes2str(binascii.hexlify(h)).upper()
        + "0000000000"
    )


def _parse_client_ack(client_ack, sk_prime):
    h = _sha1(sk_prime + b"\x02")
    expected = (
        "0104000000000000000014"
        + _bytes2str(binascii.hexlify(h)).upper()
        + "0000000000"
    )
    return client_ack == expected


# --- AES command encryption ---

def _aes_encrypt_command(ctx_hex, session_id, key_press):
    key = binascii.unhexlify(ctx_hex.upper())
    payload = json.dumps(
        {
            "method": "POST",
            "body": {
                "plugin": "RemoteControl",
                "param1": "uuid:12345",
                "param2": "Click",
                "param3": key_press,
                "param4": False,
                "api": "SendRemoteKey",
                "version": "1.000",
            },
        }
    )
    # PKCS7 padding
    pad_len = _BLOCK_SIZE - len(payload) % _BLOCK_SIZE
    padded = payload + chr(pad_len) * pad_len
    cipher = AES.new(key, AES.MODE_ECB)
    encrypted = cipher.encrypt(padded.encode("utf-8"))
    body = list(encrypted)
    msg = json.dumps({"name": "callCommon", "args": [{"Session_Id": session_id, "body": body}]})
    return "5::/com.samsung.companion:" + msg


# --- Pairing ---

def _pair(host):
    """Pair with the TV. Shows PIN on screen, prompts for input. Returns token string."""
    base = f"http://{host}:8080"
    pin_url = f"{base}/ws/apps/CloudPINPage"
    pair_url = f"{base}/ws/pairing?app_id={_APP_ID}&device_id={_DEVICE_ID}"

    # Show PIN on TV
    resp = requests.get(pin_url, timeout=5)
    try:
        from lxml import etree

        root = etree.fromstring(resp.content)
        # Strip namespace
        for el in root.iter():
            if "}" in (el.tag or ""):
                el.tag = el.tag.split("}", 1)[1]
        state = root.find("state")
        if state is not None and state.text == "stopped":
            requests.post(pin_url, data="pin4", timeout=5)
    except Exception:
        requests.post(pin_url, data="pin4", timeout=5)

    ctx = None
    sk_prime = None

    while ctx is None:
        pin = input("Enter PIN shown on TV: ")

        # Step 1
        requests.get(f"{pair_url}&step=0&type=1", timeout=5)

        # Step 2: hello exchange
        hello = _generate_server_hello(_USER_ID, pin)
        content = {
            "auth_Data": {
                "auth_type": "SPC",
                "GeneratorServerHello": _bytes2str(
                    binascii.hexlify(hello["serverHello"])
                ).upper(),
            }
        }
        resp = requests.post(f"{pair_url}&step=1", json=content, timeout=5)
        try:
            auth_data = json.loads(resp.json()["auth_data"])
            client_hello = auth_data["GeneratorClientHello"]
            request_id = auth_data["request_id"]
        except (ValueError, KeyError):
            print("Pairing failed. Try again...")
            continue

        result = _parse_client_hello(
            client_hello, hello["hash"], hello["AES_key"], _USER_ID
        )
        if not result:
            print("Wrong PIN. Try again...")
            continue

        ctx = _bytes2str(binascii.hexlify(result["ctx"]))
        sk_prime = result["SKPrime"]

    # Step 3: acknowledge
    ack_msg = _generate_server_ack(sk_prime)
    content = {
        "auth_Data": {
            "auth_type": "SPC",
            "request_id": str(request_id),
            "ServerAckMsg": ack_msg,
        }
    }
    resp = requests.post(f"{pair_url}&step=2", json=content, timeout=5)
    try:
        auth_data = json.loads(resp.json()["auth_data"])
        client_ack = auth_data["ClientAckMsg"]
        session_id = auth_data["session_id"]
    except (ValueError, KeyError):
        raise TVError("Failed to get session_id from TV")

    if not _parse_client_ack(client_ack, sk_prime):
        raise TVError("Client acknowledge verification failed")

    # Close PIN page
    requests.delete(f"{pin_url}/run", timeout=5)

    token = f"{ctx}:{session_id}"
    return token


def _load_token():
    """Load saved token, or pair and save."""
    try:
        with open(TV_TOKEN_PATH) as f:
            token = f.read().strip()
            if token:
                return token
    except FileNotFoundError:
        pass

    token = _pair(TV_IP)
    with open(TV_TOKEN_PATH, "w") as f:
        f.write(token)
    print(f"Token saved to {TV_TOKEN_PATH}")
    return token


def _send_keys(keys, delay=0.7):
    """Connect via Socket.IO and send encrypted key commands."""
    token = _load_token()
    ctx, session_id = token.rsplit(":", 1)
    try:
        session_id = int(session_id)
    except ValueError:
        pass

    # Get Socket.IO session
    millis = int(round(time.time() * 1000))
    resp = requests.get(f"http://{TV_IP}:8000/socket.io/1/?t={millis}", timeout=5)
    sid = resp.text.split(":")[0]
    ws_url = f"ws://{TV_IP}:8000/socket.io/1/websocket/{sid}"

    ws = ws_module.create_connection(ws_url, timeout=5)
    try:
        ws.recv()  # Socket.IO connect message
        ws.send("1::/com.samsung.companion")
        time.sleep(0.5)
        for key in keys:
            ws.send(_aes_encrypt_command(ctx, session_id, key))
            time.sleep(delay)
    finally:
        ws.close()


# --- UPnP SOAP (direct input switching) ---

_SOAP_NS = "urn:samsung.com:service:MainTVAgent2:1"
_soap_url: str | None = None  # lazily discovered


def _discover_soap_url(timeout: float = 3.0) -> str:
    """Discover MainTVAgent2 controlURL via SSDP + device description XML.

    The TV reassigns /smp_N_ paths on reboot, so we can't hardcode them.
    """
    # SSDP M-SEARCH for MainTVAgent2
    msg = (
        "M-SEARCH * HTTP/1.1\r\n"
        "HOST: 239.255.255.250:1900\r\n"
        'MAN: "ssdp:discover"\r\n'
        "MX: 3\r\n"
        f"ST: {_SOAP_NS}\r\n\r\n"
    )
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    s.settimeout(timeout)
    try:
        s.sendto(msg.encode(), ("239.255.255.250", 1900))
        location = None
        while True:
            data, addr = s.recvfrom(4096)
            if addr[0] != TV_IP:
                continue
            for line in data.decode(errors="replace").split("\r\n"):
                if line.upper().startswith("LOCATION:"):
                    location = line.split(":", 1)[1].strip()
                    break
            if location:
                break
    except socket.timeout:
        pass
    finally:
        s.close()

    if not location:
        raise TVError(f"SSDP discovery failed — MainTVAgent2 not found at {TV_IP}")

    # Fetch device description XML and extract controlURL
    resp = requests.get(location, timeout=5)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    ns = {"upnp": "urn:schemas-upnp-org:device-1-0"}
    for svc in root.iter("{urn:schemas-upnp-org:device-1-0}service"):
        stype = svc.findtext("{urn:schemas-upnp-org:device-1-0}serviceType", "")
        if stype == _SOAP_NS:
            ctrl = svc.findtext("{urn:schemas-upnp-org:device-1-0}controlURL", "")
            if ctrl:
                url = f"http://{TV_IP}:{TV_UPNP_PORT}{ctrl}"
                print(f"Discovered SOAP control URL: {url}")
                return url
    raise TVError(f"controlURL for MainTVAgent2 not found in {location}")


def _get_soap_url() -> str:
    """Return cached SOAP URL, discovering on first call."""
    global _soap_url
    if _soap_url is None:
        _soap_url = _discover_soap_url()
    return _soap_url


def _soap_request(action: str, args: str = "") -> str:
    """POST a SOAP envelope to MainTVAgent2. Returns the response body XML.

    Retries up to 3 times (2s between) on connection, timeout, or HTTP errors.
    On persistent 400, re-discovers the control URL once in case paths changed.
    """
    envelope = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"'
        ' s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
        "<s:Body>"
        f'<u:{action} xmlns:u="{_SOAP_NS}">'
        f"{args}"
        f"</u:{action}>"
        "</s:Body>"
        "</s:Envelope>"
    )
    headers = {
        "Content-Type": 'text/xml; charset="utf-8"',
        "SOAPAction": f'"{_SOAP_NS}#{action}"',
    }
    global _soap_url
    rediscovered = False
    for attempt in range(3):
        try:
            url = _get_soap_url()
            resp = requests.post(url, data=envelope, headers=headers, timeout=5)
            resp.raise_for_status()
            return resp.text
        except (requests.HTTPError, requests.ConnectionError, requests.Timeout) as e:
            if isinstance(e, requests.HTTPError) and resp.status_code == 400 and not rediscovered:
                print(f"SOAP {action} got 400, re-discovering control URL...")
                _soap_url = None
                rediscovered = True
                continue
            if attempt == 2:
                raise
            print(f"SOAP {action} failed ({e}), retrying in 2s...")
            time.sleep(2)


def get_current_source() -> str:
    """Get the TV's current input source (e.g. "HDMI2")."""
    xml = _soap_request("GetCurrentExternalSource")
    root = ET.fromstring(xml)
    # Find CurrentExternalSource in response, ignoring namespaces
    for el in root.iter():
        if el.tag.endswith("CurrentExternalSource"):
            return el.text or ""
    raise TVError("CurrentExternalSource not found in SOAP response")


def get_source_list() -> dict[str, int]:
    """Get available sources as {name: id} mapping."""
    xml = _soap_request("GetSourceList")
    root = ET.fromstring(xml)
    # The SourceList element contains an inner XML string
    for el in root.iter():
        if el.tag.endswith("SourceList"):
            inner = ET.fromstring(el.text)
            sources = {}
            for src in inner.iter("Source"):
                name_el = src.find("SourceType")
                id_el = src.find("ID")
                if name_el is not None and id_el is not None:
                    sources[name_el.text] = int(id_el.text)
            return sources
    raise TVError("SourceList not found in SOAP response")


def set_source(name: str, source_id: int) -> None:
    """Switch TV input directly via SOAP."""
    args = f"<Source>{name}</Source><ID>{source_id}</ID><UiID>0</UiID>"
    _soap_request("SetMainTVSource", args)


# --- Public API ---

def send_key(key: str) -> None:
    """Send a single remote key press to the TV via encrypted WebSocket."""
    if not TV_IP:
        raise TVError("TV_IP not set in lib/config.py — run step_wait_samsung with 'discover' to find it")
    _send_keys([key])


def switch_to_hdmi1() -> None:
    """Switch TV input back to HDMI1 via SOAP."""
    if not TV_IP:
        raise TVError("TV_IP not set in lib/config.py — run step_wait_samsung with 'discover' to find it")

    print("Switching TV input to HDMI1 via SOAP...")
    set_source("HDMI1", 57)
    print("TV input switched to HDMI1.")


def switch_to_mac() -> None:
    """Switch TV input to Mac's HDMI port via SOAP."""
    if not TV_IP:
        raise TVError("TV_IP not set in lib/config.py — run step_wait_samsung with 'discover' to find it")

    current = get_current_source()
    print(f"TV current input: {current}")
    if current == TV_MAC_SOURCE:
        print("Already on Mac input, skipping switch.")
        return
    print(f"Switching TV input to {TV_MAC_SOURCE} via SOAP...")
    set_source(TV_MAC_SOURCE, TV_MAC_SOURCE_ID)
    print(f"TV input switched to {TV_MAC_SOURCE}.")


def discover(timeout: float = 3.0) -> list[str]:
    """Discover Samsung TVs on the local network via SSDP."""
    SSDP_ADDR = "239.255.255.250"
    SSDP_PORT = 1900
    ST = "urn:samsung.com:device:RemoteControlReceiver:1"

    msg = (
        "M-SEARCH * HTTP/1.1\r\n"
        f"HOST: {SSDP_ADDR}:{SSDP_PORT}\r\n"
        'MAN: "ssdp:discover"\r\n'
        "MX: 2\r\n"
        f"ST: {ST}\r\n"
        "\r\n"
    )

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack("b", 2))
    sock.settimeout(timeout)
    sock.sendto(msg.encode(), (SSDP_ADDR, SSDP_PORT))

    ips: list[str] = []
    try:
        while True:
            data, addr = sock.recvfrom(4096)
            if addr[0] not in ips:
                ips.append(addr[0])
    except TimeoutError:
        pass
    finally:
        sock.close()

    return ips
