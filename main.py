import os
import logging
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from msn_scraper import fetch_articles
from validate_url import is_valid_url

load_dotenv(".env")
TOKEN = os.getenv("DISCORD_TOKEN")

# Parse multiple channel IDs into a list of ints
CHANNEL_IDS = [int(cid.strip()) for cid in os.getenv("DISCORD_CHANNEL_ID", "").split(",") if cid.strip()]

print("Token from ENV:", TOKEN)
print("Channel IDs from ENV:", CHANNEL_IDS)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    post_msn_articles.start()

@tasks.loop(minutes=5)
async def post_msn_articles():
    try:
        articles = await fetch_articles()
        if not articles:
            return

        for channel_id in CHANNEL_IDS:
            channel = bot.get_channel(channel_id)
            if not channel:
                logger.warning(f"Channel {channel_id} not found.")
                continue

            for article in articles:
                embed = discord.Embed(
                    title=article["title"],
                    url=article["url"],
                    description=article["description"],
                    color=discord.Color.red()
                )
                embed.set_author(name=article["author"])
                if is_valid_url(article.get("image")):
                    embed.set_image(url=article["image"])
                else:
                    print(f"[WARN] Skipping invalid image URL: {article.get('image')}")

                embed.set_footer(text="Football Analysis")
                print(f"[DEBUG] Article URL (MSN): {article['url']!r}")
                image_url = article.get("image")
                print(f"[DEBUG] Image URL: {image_url!r}")

                await channel.send(embed=embed)

                    
    except Exception as e:
        logger.exception("Error posting articles")


@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong!")

bot.run(TOKEN)