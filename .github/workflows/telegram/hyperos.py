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

def find(pattern, text, flags=0):
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None

def version_key(version):
    m = re.search(r"OS(\d+)\.(\d+)\.(\d+)\.(\d+)", version or "")
    return tuple(map(int, m.groups())) if m else (0, 0, 0, 0)

async def main():
    entity = await client.get_entity(CHANNEL)
    
    # Tạo dictionary lưu bài viết mới nhất của riêng từng vùng
    regions_data = {
        "EU": {"version_tuple": (0, 0, 0, 0), "data": None, "msg": None, "version": None},
        "CN": {"version_tuple": (0, 0, 0, 0), "data": None, "msg": None, "version": None}
    }

    async for msg in client.iter_messages(entity, search="myron", limit=20):
        text = msg.text or ""
        version = find(r"(OS\d+\.\d+\.\d+\.\d+\.[A-Z0-9]+)", text)
        
        if not version:
            continue
            
        # Tách mã vùng (Ví dụ: WPMEUXM -> EU, WPMCNXM -> CN)
        suffix = version.split('.')[-1] if '.' in version else ""
        if len(suffix) < 6:
            continue
            
        region = suffix[4:6] # Lấy ký tự thứ 5 và 6
        
        if region in regions_data:
            v_tuple = version_key(version)
            # So sánh để lấy phiên bản cao nhất/mới nhất của vùng đó
            if v_tuple > regions_data[region]["version_tuple"]:
                regions_data[region]["version_tuple"] = v_tuple
                regions_data[region]["msg"] = msg
                regions_data[region]["version"] = version

    # Tiến hành trích xuất dữ liệu và xuất file JSON riêng cho từng dòng
    for region, item in regions_data.items():
        if not item["msg"]:
            print(f"Không tìm thấy ROM cho vùng {region}")
            continue
            
        msg = item["msg"]
        text = msg.text or ""
        version_str = item["version"]
        
        # Gán tên thiết bị chuẩn xác theo vùng miền xuất ra JSON
        if region == "EU":
            device_name = "POCOF8Ultra"
        elif region == "CN":
            device_name = "RedmiK90ProMax"
        else:
            device_name = "Unknown"

        data = {
            "device": device_name,
            "codename": "myron",
            "region": region,
            "version": version_str,
            "android": find(r"Android:\s*(\d+)", text),
            "status": find(r"Status:\s*(.+)", text),
            "security_patch": find(r"Security Patch:\s*(.+)", text),
            "release": find(r"Release:\s*(.+)", text),
            "size": find(r"Update package size:\s*([0-9.]+\s*[MG]B)", text),
            "telegram_post": f"https://t.me/{CHANNEL}/{msg.id}",
            "telegram_id": msg.id,
            "date": str(msg.date)
        }

        # Trích xuất URL từ bài đăng Telegram
        urls = []
        if msg.entities:
            for entity in msg.entities:
                url = None
                if isinstance(entity, MessageEntityTextUrl):
                    url = entity.url
                elif isinstance(entity, MessageEntityUrl):
                    url = text[entity.offset: entity.offset + entity.length]
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

        # Tạo file JSON riêng biệt tương ứng với từng thiết bị
        filename = f"myron_{region.lower()}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"Đã xuất file thành công -> {filename} (Thiết bị: {device_name})")

with client:
    client.loop.run_until_complete(main())
