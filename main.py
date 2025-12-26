import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

# ======================
# CARGA DE ENTORNO
# ======================
load_dotenv()
TOKEN = os.getenv("TOKEN")

PREFIX = "$"
INTENTS = discord.Intents.all()

# ======================
# BOT CORE
# ======================
class NexusBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=PREFIX,
            intents=INTENTS,
            help_command=None,
            case_insensitive=True
        )

    async def setup_hook(self):
        # ---- CARGA DE COGS ----
        await self.load_extension("cogs.moderation")
        await self.load_extension("cogs.utility")
        await self.load_extension("cogs.users")

        # ---- SYNC SLASH ----
        await self.tree.sync()
        print(f"[NEXUS] Online como {self.user} ({self.user.id})")

    async def on_ready(self):
        print("[NEXUS] Sistema listo")

# ======================
# MANEJO GLOBAL DE ERRORES
# ======================
@commands.Cog.listener()
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ No tienes permisos suficientes.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Faltan argumentos.")
    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        print(f"[ERROR] {error}")

# ======================
# START
# ======================
async def main():
    bot = NexusBot()
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
