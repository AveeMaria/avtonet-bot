from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import json

def item_filter(scraped_items):
    with open("settings.json", "r", encoding="utf-8") as f:
          settings = json.load(f)

    filtered_items = []

    for item in scraped_items:
        if "mileage" in item["data"]:
            item["data"]["mileage"] = int(item["data"]["mileage"].replace(" km", "").replace(".", "").strip())
        else:
            item["data"]["mileage"] = -1
        if "1.reg" in item["data"]:
            item["data"]["1.reg"] = int(item["data"]["1.reg"])
        else:
            item["data"]["1.reg"] = -1

        if item["price"] >= settings["max_price"]:
            continue
        if item["data"]["fuel"] != "diesel motor":
            continue

        if "1.reg" in item["data"]:
            item["data"]["1.reg"] = int(item["data"]["1.reg"])
        else:
            item["data"]["1.reg"] = -1
            print(f"1.REG ERROR at {item['title']}!")

        if item["data"]["1.reg"] <= settings["min_year"] or item["data"]["1.reg"] >= settings["max_year"]:
            #exit
            continue

        if not item["data"]["oldtimer"]:
            manufacturer = item["title"].split()[0]
            if manufacturer in settings["blacklist"]:
                continue
            if manufacturer not in settings["whitelist"] and item["price"] >= settings["random_brand_max_price"]:
                continue
            if manufacturer == "Mercedes-Benz":
                if item["title"].split()[1] == "A-Razred":
                    continue

        filtered_items.append(item)

    print("Items filtered.")
    return filtered_items
