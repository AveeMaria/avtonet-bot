import json

def log_data(data):
    if not data: return

    try:
        with open("log.json", "r", encoding="utf-8") as f:
            log_items = json.load(f)
    except FileNotFoundError:
        log_items = []

    log_items.extend(data)
    with open("log.json", "w", encoding="utf-8") as f:
        json.dump(log_items, f, ensure_ascii=False, indent=4)
