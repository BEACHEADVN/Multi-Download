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
    
    # Tạo 2 danh sách riêng biệt để chứa bài đăng của từng vùng
    cn_posts = []
    eu_posts = []

    # Danh sách từ khóa cần quét
    search_keywords = ["myron", "REDMIK90ProMax", "POCOF8Ultra"]
    
    print("🚀 Đang quét dữ liệu từ kênh Telegram theo danh sách từ khóa...")

    for kw in search_keywords:
        print(f"-> Quét từ khóa: {kw}")
        # Quét limit=100 cho mỗi từ khóa để đảm bảo vét sạch bài đăng cũ mới
        async for msg in client.iter_messages(entity, search=kw, limit=100):
            text = msg.text or ""
            version = find(r"(OS\d+\.\d+\.\d+\.\d+\.[A-Z0-9]+)", text)

            if version:
                suffix = version.split('.')[-1] if '.' in version else ""
                if len(suffix) >= 6:
                    region = suffix[4:6] # Cắt lấy chữ CN hoặc EU
                    
                    # Tránh trùng lặp bài viết đã quét ở từ khóa trước
                    post_id = msg.id
                    post_data = {
                        "id": post_id,
                        "version": version,
                        "msg": msg,
                        "key": version_key(version)
                    }
                    
                    if region == "CN" and post_id not in [p["id"] for p in cn_posts]:
                        cn_posts.append(post_data)
                    elif region == "EU" and post_id not in [p["id"] for p in eu_posts]:
                        eu_posts.append(post_data)

    # Lấy bài viết có build cao nhất cho từng vùng
    targets = []
    if cn_posts:
        targets.append(("cn", max(cn_posts, key=lambda x: x["key"])))
    if eu_posts:
        targets.append(("eu", max(eu_posts, key=lambda x: x["key"])))

    if not targets:
        print("Không tìm thấy ROM với tất cả các từ khóa trên.")
        return

    # Duyệt qua từng vùng để tạo file JSON tương ứng
    for region_code, newest in targets:
        msg = newest["msg"]
        text = msg.text or ""

        # Thiết lập tên thiết bị dạng chữ thường (lowercase) theo đúng yêu cầu của bạn
        device_name = "redmik90promax" if region_code == "cn" else "pocof8ultra"

        data = {
            "device": device_name,
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

        # Xử lý làm sạch Markdown
        clean = text.replace("**", "").replace("__", "").replace("`", "")

        # Trích xuất URLs
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

        # Xuất ra file tương ứng: myron_cn.json hoặc myron_eu.json
        filename = f"myron_{region_code}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print(json.dumps(data, indent=4, ensure_ascii=False))
        print(f"Saved -> {filename}\n")

with client:
    client.loop.run_until_complete(main())
