import json

def enumerate_items(data):
    if not data:
        return []

    last_id_path = "assets/last_id.json"

    try:
        with open(last_id_path, "r", encoding="utf-8") as f:
            last_id_data = json.load(f)
            last_id = last_id_data.get("last_id", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        last_id = 0
        print("FILE NOT FOUND")

    for item in data:
        last_id += 1
        item["id"] = last_id

    with open(last_id_path, "w", encoding="utf-8") as f:
        json.dump({"last_id": last_id}, f, ensure_ascii=False, indent=2)

    return data