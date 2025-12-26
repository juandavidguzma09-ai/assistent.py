import discord
import datetime

THEME_COLOR = 0x2b2d31  # gris oscuro tipo Discord

def base_embed(title: str, description: str | None = None):
    embed = discord.Embed(
        title=title,
        description=description,
        color=THEME_COLOR
    )
    embed.timestamp = datetime.datetime.utcnow()
    return embed

def error_embed(message: str):
    return base_embed("❌ Error", message)

def success_embed(message: str):
    return base_embed("✅ Éxito", message)

def info_embed(title: str, message: str):
    return base_embed(title, message)
