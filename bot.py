import discord
import asyncio
import json
import datetime

from scraper.init_driver import init_driver
from scraper.scrape import scrape
from scraper.items_filter import item_filter
from scraper.item_enumerator import enumerate_items
from scraper.log_data import log_data
from scraper.individual_scrape import individual_scrape

with open('bot_settings.json', 'r', encoding='utf-8') as f:
    bot_settings = json.load(f)
    TOKEN = bot_settings["discord_token"].strip()
    CHANNEL_ID = int(bot_settings["channel_id"])

with open('settings.json', 'r', encoding='utf-8') as f:
    settings = json.load(f)

intents = discord.Intents.default()
client = discord.Client(intents=intents)

driver = init_driver()

scrape_task_started = False


async def send_to_discord(car):
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print("Could not find the channel.")
        return

    manufacturer = car["title"].split()[0]
    if car["data"]["oldtimer"]:
        embed = discord.Embed(
            title=car["title"],
            url=car["link"],
            color=discord.Color.gold()
        )
    elif (car["price"] <= 1000 and manufacturer in settings["whitelist"]) or (car["price"] <= 500 and manufacturer not in settings["blacklist"]):
        embed = discord.Embed(
            title=car["title"],
            url=car["link"],
            color=discord.Color.green()
        )
    else:
        embed = discord.Embed(
            title=car["title"],
            url=car["link"],
            color=discord.Color.blue()
        )

    embed.set_image(url=car["img_link"])
    if car["data"]["oldtimer"]:
        embed.description = (
            f'**{car["price"]} €, {car["data"]["mileage"]} km**\n'
            f'_{car["data"]["1.reg"]}, {car["data"]["engine"]}_\n**OLDTIMER**'
        )
    else:
        embed.description = (
            f'**{car["price"]} €, {car["data"]["mileage"]} km**\n'
            f'_{car["data"]["1.reg"]}, {car["data"]["engine"]}_'
        )

    await channel.send(embed=embed)


async def sync_scrape_cycle():
    print("Starting scrape...")
    scraped = scrape(driver)
    filtered = enumerate_items(item_filter(scraped))

    data = []
    for car in filtered:
        print(f"Scraping detail: {car['link']}")
        data.append(await asyncio.to_thread(individual_scrape, driver, car["link"]))

    log_data(enumerate_items(data))
    return filtered


async def run_every_3_minutes():
    await client.wait_until_ready()

    while not client.is_closed():
        now = datetime.datetime.now()

        if bot_settings["start_hour"] <= now.hour < bot_settings["end_hour"]:
            print(f"[{now.replace(microsecond=0)}] Scraping started.")

            try:
                await client.change_presence(status=discord.Status.dnd, activity=discord.Game(name="Scraping..."))

                filtered_items = await sync_scrape_cycle()

                for car in filtered_items:
                    await send_to_discord(car)

                print(f"[{datetime.datetime.now().replace(microsecond=0)}] Cycle complete.")

            except Exception as e:
                print(f"Error during scraping cycle: {e}")

            finally:
                await client.change_presence(status=discord.Status.online, activity=discord.Game(name="Idle..."))


            now = datetime.datetime.now().replace(second=0, microsecond=0)
            minute = now.minute - (now.minute % 3) + 3
            if minute >= 60:
                next_run = now.replace(hour=(now.hour + 1) % 24, minute=0)
            else:
                next_run = now.replace(minute=minute)
            wait_time = (next_run - datetime.datetime.now()).total_seconds()
            print(f"Sleeping for {wait_time:.1f}s until {next_run.time()}")
            await asyncio.sleep(max(wait_time, 1))
        else:
            print("Outside working hours, sleeping 60s")
            await asyncio.sleep(60)


@client.event
async def on_ready():
    global scrape_task_started
    print(f"Logged in as {client.user}")
    if not scrape_task_started:
        client.loop.create_task(run_every_3_minutes())
        scrape_task_started = True


client.run(TOKEN)
