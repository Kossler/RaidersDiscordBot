import os
import logging
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from msn_scraper import fetch_articles, peek_latest_article, posted_articles

load_dotenv(".env")
TOKEN = os.getenv("DISCORD_TOKEN")

CHANNEL_IDS = [int(cid.strip()) for cid in os.getenv("DISCORD_CHANNEL_ID", "").split(",") if cid.strip()]

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
            logger.info("No new articles found")
            return
        for channel_id in CHANNEL_IDS:
            channel = bot.get_channel(channel_id)
            if not channel:
                logger.error(f"Could not find channel with ID {channel_id}")
                continue
            for title, url, thumb in articles:
                embed = discord.Embed(
                    title=title,
                    url=url,
                    color=discord.Color.blue()
                )
                if thumb:
                    embed.set_thumbnail(url=thumb)
                embed.set_footer(text="MSN Article")
                await channel.send(embed=embed)
    except Exception as e:
        logger.exception(f"Error fetching or posting articles: {e}")

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command(name="test")
async def test(ctx):
    try:
        article = await peek_latest_article()
        if not article:
            await ctx.send("Could not retrieve the latest article.")
            return

        title, url, thumb = article
        embed = discord.Embed(
            title=title,
            url=url,
            color=discord.Color.green()
        )
        if thumb:
            embed.set_thumbnail(url=thumb)
        embed.set_footer(text="Latest MSN Article")
        await ctx.send(embed=embed)

    except Exception as e:
        logger.exception(f"Error fetching latest article in !test: {e}")
        await ctx.send("An error occurred while fetching the latest article.")



bot.run(TOKEN)
