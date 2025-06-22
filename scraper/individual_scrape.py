from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

def individual_scrape(driver, link):
    driver.get(link)
    #print("CURR PAGE:", driver.title)

    if "Attention Required!" in driver.title or "Cloudflare" in  driver.title:
        print("I LOVE CLOUDFLARE")
        return {}

    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    title_el = soup.select_one("div.col-12.mt-3.pt-1")
    title = title_el.get_text(separator=' ', strip=True).replace("\xa0", " ") if title_el else "/"
    #title = title_el.get_text(strip=True).replace("\xa0", " ") if title_el else "/"

    price_el = soup.select_one("p.h2.font-weight-bold.align-middle.py-4.mb-0")
    price = int(price_el.get_text(strip=True).replace("€","").replace(".","")) if price_el else -1

    name_el = soup.select_one("li.list-group-item.py-3.h5.font-weight-bold")
    name = name_el.get_text(strip=True) if name_el else "/"
    name = name[0] + name[1::1].lower()

    phone_el = soup.select_one("p.h4.font-weight-bold.m-0")
    phone = phone_el.get_text(strip=True) if phone_el else "/"

    reg_since_el = soup.select_one("li.list-group-item.pt-2.text-muted")
    reg_since = str.split(reg_since_el.get_text(strip=True))[-1] if reg_since_el else "/"

    post_time_el = soup.select_one("div.col-12.col-lg-6.p-0.pl-1.text-center.text-lg-left")
    post_time_raw = post_time_el.get_text(strip=True) if post_time_el else "/"
    if post_time_raw == "/":
        post_date = "/"
        post_time = "/"
    else:
        post_time = str.split(post_time_raw)[-1]
        post_date = str.split(post_time_raw)[-2]

    # DATA TABLES
    tables = soup.select("table.table.table-sm")

    if not tables:
        print("ERROR NO TABLES")
        return {}
    
    #TECHNICAL DATA
    first_table = tables[0]
    rows = first_table.select("tbody tr")

    raw_technical_data = {}
    for row in rows:
        key = row.find("th").get_text(strip=True).rstrip(":")
        value = row.find("td").get_text(" ", strip=True).replace("\xa0", " ")
        raw_technical_data[key] = value
    
    raw_technical_data.pop('')
    oldtimer = raw_technical_data["Starost"] == "rabljeno (vozilo ima oldtimer certifikat)"
    raw_technical_data.pop('Starost')


    ul = soup.find('ul', class_='list-group list-group-flush bg-white p-0 pb-1 GO-Rounded-B text-center')

    private_seller = False
    if ul:
        #img_li = ul.find('li', class_='list-group-item py-3')
        #is_seller = img_li.find('img') if img_li else None

        telefon_li = ul.find('li', class_='list-group-item p-0 font-weight-bold text-muted border-bottom-0')
        is_private = telefon_li and 'TELEFON' in telefon_li.get_text(strip=True).upper()

        #if is_seller:
        #    print("is seller")
        #else:
        #    print("idk if seller")
        #
        if is_private:
            #print("is private")
            private_seller = True
        else:
            private_seller = False
            #print("not private")
    else:
        print("Target seller <ul> not found.")


    technical_data = {}
    key_renames = {
        "Prva registracija": "1.reg",
        "Leto proizvodnje": "year_of_manufacture",
        "Interna številka": "internal_id",
        "VIN / številka šasije": "chasis_id",
        "Prevoženi km": "mileage",
        "Tehnični pregled velja do": "inspection_exp",
        "Motor": "engine",
        "Gorivo": "fuel",
        "Menjalnik": "transmission",
        "Oblika": "shape",
        "Št.vrat": "doors",
        "Barva": "color",
        "Notranjost": "interior",
        "Kraj ogleda": "location"
    }

    for key, value in raw_technical_data.items():
        new_key = key_renames.get(key, key)
        technical_data[new_key] = value
    
    #manual fixes
    technical_data["doors"] = str.split(technical_data["doors"])[0]
    technical_data["1.reg"] = int(technical_data["1.reg"][:4])
    
    try:
        technical_data["mileage"] = int(technical_data.get("mileage", ""))
    except (ValueError, TypeError):
        technical_data["mileage"] = -1

    technical_data["engine"] = str.split(technical_data["engine"].replace("(", ""))
     
    technical_data["engine"] = {
      "kW": int(technical_data["engine"][0]),
      "KM": int(technical_data["engine"][2]),
      "ccm": int(technical_data["engine"][-2])
    }

    # IF SOME LISTING DONT HAVE one of tables BRUH
    found_enviromental = any(
        thead.find("th") and thead.find("th").get_text(strip=True) == "Poraba goriva in emisije (NEDC)"
        for thead in soup.find_all("thead")
    )
    found_history = any(
        thead.find("th") and thead.find("th").get_text(strip=True) == "Zgodovina vozila"
        for thead in soup.find_all("thead")
    )

    enviromental = []
    if found_enviromental:
        env_table = tables[1 + found_history]

        enviromental = [td.get_text(strip=True) for td in env_table.find_all("td")] if env_table else []
        if enviromental:
            enviromental.pop(0)
            enviromental = dict(zip(["consumption", "emission_standard", "co2_emissions"], enviromental))
    else:
        print("enviromental data not found")
    
    #MISC DATA
    categories = [th.get_text(strip=True) for th in soup.select("th.font-weight-bold")]

    misc_data = []
    if categories:
        i = 0
        uls = soup.select("ul.list.font-weight-normal.mb-0")
        for ul in uls:
            data = [li.get_text(strip=True) for li in ul.find_all("li")] if ul else []
            #misc_data[categories[i]] = data
            misc_data.append(data)
            i += 1

    replace_dict = {
      "ABS zavorni sistem": "ABS", 
      "aktivo vzmetenje": "active_suspension", 
      "samodejna zapora diferenciala (ASD / EDS ...)": "diff_lock", 
      "zračno vzmetenje": "air_suspension", 
      "štirikolesni pogon 4x4 / 4WD": "AWD", 
      "10 x zračna vreča / Airbag": "airbag", 
      "rezervno kolo normalnih dimenzij": "spare_wheel", 
      "alarmna naprava": "alarm", 
      "leseni dodatki v notranjosti": "wood_interior", 
      "usnje": "leather", 
      "12V vtičnica": "12V", 
      "centralno zaklepanje": "central_locking", 
      "gretje mirujočega vozila (Webasto)": "heating", 
      "klimatska naprava": "AC", 
      "panorama sončna streha": "sunroof", 
      "servo volan": "power_steering", 
      "tempomat": "cruise_control", 
      "zatemnjena / tonirana stekla": "tinted_windows", 
      "Bluetooth vmesnik": "bluetooth", 
      "avtoradio": "radio", 
      "navigacijski sistem": "GPS", 
      "bočne stopnice": "side_rails", 
      "strešne sani": "roof_rails", 
      "vlečna kljuka": "tow_hook", 
      "vzvratna kamera": "parking_camera", 
      "servisna knjiga": "service_log", 
      "servisna knjiga / potrjena": "service_log_approved", 
      "vozilo je bilo garažirano": "garaged", 
      "vozilo ni bilo karambolirano": "accident_free"
    }

    flat = [item for sublist in misc_data for item in sublist]
    misc_data = [replace_dict[item] for item in flat if item in replace_dict]

    description_el = soup.find(id="StareOpombe")
    description = description_el.get_text(strip=True) if description_el else "/"

    img = soup.select_one("div.GO-OglasThumb img")
    img_link = img["src"].replace("_small", "_160") if img else ""

    data = {
        "id": 0,#AUTO
        "title": title,
        "price": price,
        
        "mileage": technical_data["mileage"],
        "inspection_exp": technical_data.get("inspection_exp", "/"),

        "1.reg": technical_data["1.reg"],
        "oldtimer": oldtimer,
        
        "engine": technical_data["engine"],
        
        "fuel": technical_data["fuel"],
        "transmission": technical_data["transmission"],

        "seller": {
          "name": name,
          "phone": phone.replace(" ", "").replace("/", "").replace("-", ""),
          "private_seller": private_seller,
          "reg_since": reg_since
        },

        "location": technical_data["location"],
        "chasis_id": technical_data.get("chasis_id", "/"),

        "misc_data": misc_data,
        
        #sometimes inside oldtimer data but whatever!
        #"manufacturer_data": {
        #  "year_of_manufacture": technical_data["year_of_manufacture"], 
        #  "internal_id": technical_data["internal_id"],
        #  "chasis_id": technical_data["chasis_id"],
        #},        

        "enviromental": enviromental,
        "description": description,

        "visuals": {
          "shape": technical_data["shape"],
          "doors": int(technical_data["doors"]),
          "color": technical_data["color"],
          "interior": technical_data["interior"],
        },

        "post_date": post_date,
        "post_time": post_time,
        "link": link,
        "img_link": img_link
    }

    return data

