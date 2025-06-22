from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin


def scrape(driver):
    try:
        with open("assets/link_log.json", "r", encoding="utf-8") as f:
            existing_links = json.load(f)
    except FileNotFoundError:
        existing_links = []

    url = "https://www.avto.net/Ads/results_100.asp"
    driver.get(url)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    car_cards = soup.select("div.GO-Results-Row")

    scraped_items = []
    new_links = []
    print("Starting scrape...")

    for car in car_cards:
        link_el = car.select_one(".stretched-link")
        link = urljoin(url, link_el["href"]) if link_el and "href" in link_el.attrs else None
        new_links.append(link)
        
        if link in existing_links:
            continue

        title_el = car.select_one(".GO-Results-Naziv")
        #if not title_el:
            #print("ERROR: no title", url)
            #continue
        title = title_el.get_text(strip=True)

        # Price logic
        if car.select_one(".GO-Results-Price-Akcija-TXT"):
            price = car.select_one(".GO-Results-Price-TXT-AkcijaCena").get_text(strip=True)
        elif car.select_one(".GO-Results-Top-BadgeTop"):
            if car.select_one(".GO-Results-Top-Price-TXT-Regular"):
                price = car.select_one(".GO-Results-Top-Price-TXT-Regular").get_text(strip=True)
            elif car.select_one(".GO-Results-Top-Price-TXT-AkcijaCena"):
                price = car.select_one(".GO-Results-Top-Price-TXT-AkcijaCena").get_text(strip=True)
            else:
                price = "/"
        else:
            price = car.select_one(".GO-Results-Price-TXT-Regular").get_text(strip=True)

        price = -1 if price == "/" else int(price.replace(".", "").replace(" €", ""))
        
        img_el = car.select_one("img")
        img_link = urljoin(url, img_el["src"]) if img_el and "src" in img_el.attrs else None

        broken = bool(car.select_one(".fa-exclamation-triangle"))
        if broken:
            print("broken")
            continue

        oldtimer = bool(car.select_one(".fa-institution"))

        data_cells = car.select_one(".GO-Results-Data-Top") or car.select_one(".GO-Results-Top-Data-Top")
        if not data_cells:
            print(f"data ERROR at {url}")
            continue

        td_elements = data_cells.find_all("td")
        raw = [td.get_text(strip=True) for td in td_elements]
        raw_data = dict(zip(raw[::2], raw[1::2]))

        key_renames = {
            "1.registracija": "1.reg",
            "Prevoženih": "mileage",
            "Gorivo": "fuel",
            "Menjalnik": "transmission",
            "Motor": "engine"
        }

        data = {key_renames.get(k, k): v for k, v in raw_data.items()}
        data["oldtimer"] = oldtimer

        scraped_items.append({
            "id": 0,
            "title": title,
            "price": price,
            "data": data,
            "link": link,
            "img_link": img_link
        })

    combined_links = existing_links + new_links
    combined_links = combined_links[-100:]

    with open("assets/link_log.json", "w", encoding="utf-8") as f:
        json.dump(combined_links, f, ensure_ascii=False, indent=2)

    if not scraped_items:
        print("Scraped 0 wanted items.")
    else:
        print(f"Scraped {len(scraped_items)} wanted items.")
        
    return scraped_items


def old_scrape(driver):
    try:
        with open("assets/link_log.json", "r", encoding="utf-8") as f:
            log_items = json.load(f)
    except FileNotFoundError:
        log_items = []

    existing_links = set(item["link"] for item in log_items)

    url = "https://www.avto.net/Ads/results_100.asp"
    driver.get(url)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    car_cards = soup.select("div.GO-Results-Row")

    scraped_items = []
    print("Starting scrape...")

    for car in car_cards:
        title_el = car.select_one(".GO-Results-Naziv")
        if not title_el:
            print("ERROR: no title" + url)
            continue
        title = title_el.get_text(strip=True)

        if car.select_one(".GO-Results-Price-Akcija-TXT"):
            price = car.select_one(".GO-Results-Price-TXT-AkcijaCena").get_text(strip=True)
        elif car.select_one(".GO-Results-Top-BadgeTop"):
            if car.select_one(".GO-Results-Top-Price-TXT-Regular"):
                price = car.select_one(".GO-Results-Top-Price-TXT-Regular").get_text(strip=True)
            elif car.select_one(".GO-Results-Top-Price-TXT-AkcijaCena"):
                price = car.select_one(".GO-Results-Top-Price-TXT-AkcijaCena").get_text(strip=True)
            else:
                price = "/"
        else:
            price = car.select_one(".GO-Results-Price-TXT-Regular").get_text(strip=True)

        if price == "/":
            price = -1
        else:
            price = int(price.replace(".", "").replace(" €", ""))

        link_el = car.select_one(".stretched-link")
        link = link_el["href"] if link_el and "href" in link_el.attrs else None
        link = urljoin(url, link) if link else None

        img_el = car.select_one("img")
        img_link = img_el["src"] if img_el and "src" in img_el.attrs else None
        img_link = urljoin(url, img_link) if img_link else None

        if link in existing_links:
            print("Already in log.json, skipping:", link)
            continue

        broken = bool(car.select_one(".fa-exclamation-triangle"))
        if broken:
            print("broken")
            continue

        oldtimer = bool(car.select_one(".fa-institution"))
        #if oldtimer: print("OLDTIMER")

        data_cells = car.select_one(".GO-Results-Data-Top") or car.select_one(".GO-Results-Top-Data-Top")
        if not data_cells:
            print(f"data ERROR at {url}")
            continue

        td_elements = data_cells.find_all("td")
        raw = [td.get_text(strip=True) for td in td_elements]

        raw_data = dict(zip(raw[::2], raw[1::2]))

        key_renames = {
            "1.registracija": "1.reg",
            "Prevoženih": "mileage",
            "Gorivo": "fuel",
            "Menjalnik": "transmission",
            "Motor": "engine"
        }

        data = {key_renames.get(k, k): v for k, v in raw_data.items()}
        data["oldtimer"] = oldtimer

        scraped_items.append({
            "id": 0,
            "title": title,
            "price": price,
            "data": data,
            "link": link,
            "img_link": img_link
        })

    print("Items scraped.")
    return scraped_items