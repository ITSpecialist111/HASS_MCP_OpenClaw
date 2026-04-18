"""§54 Identity & secrets (password mgrs, keychain, PKI, OAuth, mail, TOTP, SMS, e-sign)."""
from __future__ import annotations

import base64
import json
import os
from typing import Any

import httpx

from .. import shell as _shell
from ._helpers import tool

_PKI_DIR = "/data/pki"


async def _hit(method: str, url: str, **kw) -> Any:
    async with httpx.AsyncClient(timeout=60.0, verify=kw.pop("verify", True)) as c:
        r = await c.request(method.upper(), url, **kw)
        try: body = r.json()
        except Exception: body = r.text
        return {"status_code": r.status_code, "body": body}


def register(mcp) -> int:

    # ---- Bitwarden / Vaultwarden via bw CLI ----
    @tool(mcp)
    async def bitwarden_command(args: str, session: str | None = None) -> Any:
        """§54 Run `bw <args>` (Bitwarden CLI). Pass session token if unlocked."""
        env = f"BW_SESSION={session!r} " if session else ""
        return await _shell.shell_exec(f"{env}bw {args}", timeout=60.0)

    @tool(mcp)
    async def bitwarden_get_item(name_or_id: str, session: str) -> Any:
        """§54 bw get item <name|id> --session <s>."""
        out = await _shell.shell_exec(
            f"BW_SESSION={session!r} bw get item {name_or_id!r}", timeout=30.0)
        try: return json.loads(out.get("stdout", ""))
        except Exception: return out

    # ---- Vaultwarden / 1Password / KeePass shells (op / kpcli) ----
    @tool(mcp)
    async def onepassword_command(args: str) -> Any:
        """§54 1Password CLI `op <args>` (must be signed-in via env vars)."""
        return await _shell.shell_exec(f"op {args}", timeout=60.0)

    @tool(mcp)
    async def keepass_query(database: str, password: str, entry: str) -> Any:
        """§54 keepassxc-cli show entry."""
        return await _shell.shell_exec(
            f"echo {password!r} | keepassxc-cli show -s {database!r} {entry!r}",
            timeout=30.0)

    # ---- YubiKey ----
    @tool(mcp)
    async def yubikey_list() -> Any:
        """§54 ykman list."""
        return await _shell.shell_exec("ykman list", timeout=10.0)

    @tool(mcp)
    async def yubikey_command(args: str) -> Any:
        """§54 ykman <args>."""
        return await _shell.shell_exec(f"ykman {args}", timeout=60.0)

    # ---- PKI CA ----
    @tool(mcp)
    async def pki_init_ca(common_name: str = "HASS-MCP CA",
                            days: int = 3650) -> Any:
        """§54 Initialise an internal Root CA in /data/pki."""
        os.makedirs(_PKI_DIR, exist_ok=True)
        ca_key = f"{_PKI_DIR}/ca.key"; ca_crt = f"{_PKI_DIR}/ca.crt"
        if os.path.exists(ca_key) and os.path.exists(ca_crt):
            return {"already_exists": True, "ca_crt": ca_crt}
        await _shell.shell_exec(
            f"openssl genrsa -out {ca_key} 4096", timeout=60.0)
        await _shell.shell_exec(
            f"openssl req -x509 -new -nodes -key {ca_key} -sha256 -days {days} "
            f"-subj '/CN={common_name}' -out {ca_crt}", timeout=60.0)
        return {"ca_key": ca_key, "ca_crt": ca_crt}

    @tool(mcp)
    async def pki_issue_cert(common_name: str, sans: list[str] | None = None,
                               days: int = 365) -> Any:
        """§54 Issue a TLS cert signed by the internal CA."""
        os.makedirs(_PKI_DIR, exist_ok=True)
        slug = common_name.replace("*", "wildcard").replace(".", "_")
        key = f"{_PKI_DIR}/{slug}.key"; csr = f"{_PKI_DIR}/{slug}.csr"
        crt = f"{_PKI_DIR}/{slug}.crt"; ext = f"{_PKI_DIR}/{slug}.ext"
        with open(ext, "w") as f:
            f.write("subjectAltName = " + ", ".join(
                f"DNS:{s}" for s in (sans or [common_name])))
        await _shell.shell_exec(f"openssl genrsa -out {key} 2048", timeout=30.0)
        await _shell.shell_exec(
            f"openssl req -new -key {key} -subj '/CN={common_name}' -out {csr}",
            timeout=30.0)
        await _shell.shell_exec(
            f"openssl x509 -req -in {csr} -CA {_PKI_DIR}/ca.crt "
            f"-CAkey {_PKI_DIR}/ca.key -CAcreateserial -out {crt} "
            f"-days {days} -sha256 -extfile {ext}", timeout=30.0)
        return {"key": key, "crt": crt}

    # ---- OAuth impersonation (admin → user) ----
    @tool(mcp)
    async def oauth_impersonate_google(admin_access_token: str,
                                         target_user_email: str,
                                         scopes: list[str]) -> Any:
        """§54 Mint an access token impersonating a Workspace user (DWD)."""
        return await _hit("POST",
                           "https://oauth2.googleapis.com/token",
                           data={"grant_type":
                                  "urn:ietf:params:oauth:grant-type:jwt-bearer",
                                  "assertion": admin_access_token,
                                  "scope": " ".join(scopes),
                                  "subject": target_user_email})

    # ---- Email send / receive ----
    @tool(mcp)
    async def smtp_send(host: str, port: int, user: str, password: str,
                          to: list[str], subject: str, body: str,
                          from_addr: str | None = None,
                          starttls: bool = True) -> Any:
        """§54 Plain SMTP send."""
        import smtplib
        from email.message import EmailMessage
        msg = EmailMessage()
        msg["From"] = from_addr or user
        msg["To"] = ", ".join(to); msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(host, port, timeout=30) as s:
            if starttls: s.starttls()
            s.login(user, password); s.send_message(msg)
        return {"sent": True, "to": to}

    @tool(mcp)
    async def imap_fetch(host: str, port: int, user: str, password: str,
                           folder: str = "INBOX", limit: int = 20) -> Any:
        """§54 Fetch latest N message headers via IMAP."""
        import imaplib, email
        m = imaplib.IMAP4_SSL(host, port); m.login(user, password)
        m.select(folder)
        _, data = m.search(None, "ALL")
        ids = data[0].split()[-limit:]
        out = []
        for i in ids:
            _, msg = m.fetch(i, "(BODY.PEEK[HEADER])")
            parsed = email.message_from_bytes(msg[0][1])
            out.append({"id": i.decode(),
                         "from": parsed.get("From"),
                         "subject": parsed.get("Subject"),
                         "date": parsed.get("Date")})
        m.logout()
        return out

    # ---- TOTP ----
    @tool(mcp)
    async def totp_generate(secret_b32: str) -> dict:
        """§54 RFC6238 TOTP code from a base32 secret."""
        import hmac, hashlib, struct, time
        key = base64.b32decode(secret_b32.upper() + "=" * (-len(secret_b32) % 8))
        counter = int(time.time() // 30)
        h = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
        offset = h[-1] & 0x0F
        code = (struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF) % 1000000
        return {"code": f"{code:06d}",
                 "expires_in": 30 - int(time.time()) % 30}

    @tool(mcp)
    async def totp_store_secret(name: str, secret_b32: str) -> dict:
        """§54 Stash a TOTP seed in /data/totp.json."""
        path = "/data/totp.json"
        store = {}
        if os.path.exists(path):
            with open(path) as f: store = json.load(f)
        store[name] = secret_b32
        with open(path, "w") as f: json.dump(store, f)
        os.chmod(path, 0o600)
        return {"name": name, "stored": True}

    # ---- SMS / Voice gateway ----
    @tool(mcp)
    async def sms_send(provider: str, to: str, body: str,
                         account_sid: str | None = None,
                         auth_token: str | None = None,
                         api_key: str | None = None,
                         from_number: str | None = None) -> Any:
        """§54 Twilio / Vonage / Sipgate / generic SMS send."""
        if provider == "twilio":
            return await _hit("POST",
                f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
                auth=(account_sid, auth_token),
                data={"From": from_number, "To": to, "Body": body})
        if provider == "vonage":
            return await _hit("POST", "https://rest.nexmo.com/sms/json",
                               data={"api_key": account_sid, "api_secret": auth_token,
                                      "from": from_number, "to": to, "text": body})
        return {"error": f"unsupported provider {provider}"}

    @tool(mcp)
    async def sms_inbox(provider: str, **kw) -> Any:
        """§54 Twilio: fetch inbound messages (incl. 2FA codes)."""
        if provider == "twilio":
            return await _hit("GET",
                f"https://api.twilio.com/2010-04-01/Accounts/{kw['account_sid']}/Messages.json",
                auth=(kw["account_sid"], kw["auth_token"]),
                params={"To": kw.get("to"), "PageSize": kw.get("page_size", 20)})
        return {"error": f"unsupported provider {provider}"}

    @tool(mcp)
    async def voice_call_initiate(provider: str, to: str, twiml_url: str,
                                    account_sid: str, auth_token: str,
                                    from_number: str) -> Any:
        """§54 Twilio: place a voice call."""
        return await _hit("POST",
            f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json",
            auth=(account_sid, auth_token),
            data={"From": from_number, "To": to, "Url": twiml_url})

    # ---- E-sign ----
    @tool(mcp)
    async def esign_request(provider: str, method: str, url: str,
                              api_key: str | None = None,
                              json_body: dict | None = None) -> Any:
        """§54 DocuSign / Adobe Sign / Dropbox Sign API pass-through."""
        h = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        return await _hit(method, url, headers=h, json=json_body)

    return 15
