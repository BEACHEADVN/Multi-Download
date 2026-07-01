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
    m = re.search(r"OS(\d+)\.(\d+)\.(\d+)\.(\d+)", version or "")
    if not m:
        return (0, 0, 0, 0)
    return tuple(map(int, m.groups()))

# ==========================
# MAIN
# ==========================
async def main():
    entity = await client.get_entity(CHANNEL)
    
    # Tạo danh sách riêng cho từng vùng miền
    cn_posts = []
    eu_posts = []

    # Giữ nguyên cấu trúc tìm kiếm ngon lành của bạn
    async for msg in client.iter_messages(entity, search="myron", limit=30):
        text = msg.text or ""
        version = find(r"(OS\d+\.\d+\.\d+\.\d+\.[A-Z0-9]+)", text)

        if version:
            suffix = version.split('.')[-1] if '.' in version else ""
            if len(suffix) >= 6:
                region = suffix[4:6] # Lấy mã CN hoặc EU
                post_data = {
                    "version": version,
                    "msg": msg,
                    "key": version_key(version)
                }
                if region == "CN":
                    cn_posts.append(post_data)
                elif region == "EU":
                    eu_posts.append(post_data)

    # Cấu hình phân tách xử lý cho từng vùng
    targets = []
    if cn_posts:
        targets.append(("cn", max(cn_posts, key=lambda x: x["key"]), "redmik90promax"))
    if eu_posts:
        targets.append(("eu", max(eu_posts, key=lambda x: x["key"]), "pocof8ultra"))

    if not targets:
        print("Không tìm thấy ROM.")
        return

    # Duyệt và xuất file cho từng vùng được tìm thấy
    for region_code, newest, default_device in targets:
        msg = newest["msg"]
        text = msg.text or ""

        data = {
            "device": default_device, # Tên mặc định chuẩn theo vùng miền bạn muốn
            "codename": "myron",
            "version": newest["version"],
            "android": find(r"Android:\s*(\d+)", text),
            "status": find(r"Status:\s*(.+)", text),
            "security_patch": find(r"Security Patch:\s*(.+)", text),
            "release": find(r"Release:\s*(.+)", text),
            "size": find(r"Update package size:\s*([0-9.]+\s*[MG]B)", text),
            "telegram_post": f"https://t.me/{CHANNEL}/{msg.id}",
            "telegram_id": msg.id,
            "date": str(msg.date)
        }

        # Bỏ markdown & bóc hashtag giống hệt code gốc của bạn
        clean = text.replace("**", "").replace("__", "").replace("`", "")
        hashtags = re.findall(r"#([A-Za-z0-9]+)", clean)
        ignore = {"HyperOS", "HyperOS2", "HyperOS3", "China", "India", "Europe", "EEA", "Global", "Update", "Released", "Release", "Full", "MiPilot", "Myron"}

        for tag in hashtags:
            if tag not in ignore:
                # Nếu bóc được hashtag chuẩn thì ưu tiên dùng, không thì giữ nguyên mặc định ở trên
                data["device"] = tag
                break

        # Ép chữ thường cho tên thiết bị đầu ra JSON theo đúng yêu cầu
        if region_code == "cn":
            data["device"] = "redmik90promax"
        elif region_code == "eu":
            data["device"] = "pocof8ultra"

        # Bóc tách URLs URLs
        urls = []
        if msg.entities:
            for entity in msg.entities:
                url = None
                if isinstance(entity, MessageEntityTextUrl):
                    url = entity.url
                elif isinstance(entity, MessageEntityUrl):
                    url = clean[entity.offset: entity.offset + entity.length]
                if url:
                    urls.append(url)

        rom_urls = [u for u in urls if any(x in u for x in ("cdnorg", "cdnor", "bigota", "miui"))]

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

        # Xuất riêng file: myron_cn.json và myron_eu.json
        filename = f"myron_{region_code}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print(f"Saved -> {filename}")

with client:
    client.loop.run_until_complete(main())
