import re
import json
from telethon import TelegramClient
from telethon.tl.types import MessageEntityTextUrl, MessageEntityUrl

# ==========================
# CONFIG
# ==========================

api_id = 33413032
api_hash = "88a4ee92ce485b73acd6c10db41be4d0"

CHANNEL = "TECH_MUKUL"

client = TelegramClient("telegram_session", api_id, api_hash)


# ==========================
# FUNCTIONS
# ==========================

def find(pattern, text, flags=0):
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None


def version_key(version):
    m = re.search(
        r"OS(\d+)\.(\d+)\.(\d+)\.(\d+)",
        version or ""
    )

    if not m:
        return (0, 0, 0, 0)

    return tuple(map(int, m.groups()))


# ==========================
# MAIN
# ==========================

async def main():

    entity = await client.get_entity(CHANNEL)

    posts = []

    async for msg in client.iter_messages(
        entity,
        search="myron",
        limit=20
    ):

        text = msg.text or ""

        version = find(
            r"(OS\d+\.\d+\.\d+\.\d+\.[A-Z0-9]+)",
            text
        )

        if version:
            posts.append({
                "version": version,
                "msg": msg,
                "key": version_key(version)
            })

    if not posts:
        print("Không tìm thấy ROM.")
        return

    newest = max(posts, key=lambda x: x["key"])

    msg = newest["msg"]
    text = msg.text or ""

    data = {
        "device": None,
        "codename": "myron",
        "version": newest["version"],
        "android": find(r"Android:\s*(\d+)", text),
        "status": find(r"Status:\s*(.+)", text),
        "security_patch": find(r"Security Patch:\s*(.+)", text),
        "release": find(r"Release:\s*(.+)", text),
        "size": find(
            r"Update package size:\s*([0-9.]+\s*[MG]B)",
            text
        ),
        "telegram_post": f"https://t.me/{CHANNEL}/{msg.id}",
        "telegram_id": msg.id,
        "date": str(msg.date)
    }

    # ==========================
    # DEVICE
    # ==========================

    clean = text

    # bỏ markdown
    clean = clean.replace("**", "")
    clean = clean.replace("__", "")
    clean = clean.replace("`", "")

    hashtags = re.findall(r"#([A-Za-z0-9]+)", clean)

    ignore = {
        "HyperOS",
        "HyperOS2",
        "HyperOS3",
        "China",
        "India",
        "Europe",
        "EEA",
        "Global",
        "Update",
        "Released",
        "Release",
        "Full",
        "MiPilot",
        "Myron"
    }

    for tag in hashtags:
        if tag not in ignore:
            data["device"] = tag
            break

    # ==========================
    # URLS
    # ==========================

    urls = []

    if msg.entities:

        for entity in msg.entities:

            url = None

            if isinstance(entity, MessageEntityTextUrl):
                url = entity.url

            elif isinstance(entity, MessageEntityUrl):
                url = clean[
                    entity.offset:
                    entity.offset + entity.length
                ]

            if url:
                urls.append(url)

    rom_urls = [
        u for u in urls
        if any(x in u for x in (
            "cdnorg",
            "cdnor",
            "bigota",
            "miui"
        ))
    ]

    data["downloads"] = {
        "recovery": {
            "official": rom_urls[0] if len(rom_urls) > 0 else None,
            "mirror": rom_urls[1] if len(rom_urls) > 1 else None
        },
        "fastboot": {
            "official": rom_urls[2] if len(rom_urls) > 2 else None,
            "mirror": rom_urls[3] if len(rom_urls) > 3 else None
        }
    }

    print(json.dumps(
        data,
        indent=4,
        ensure_ascii=False
    ))

    with open(
        "myron.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )

    print()
    print("Saved -> myron.json")


with client:
    client.loop.run_until_complete(main())
