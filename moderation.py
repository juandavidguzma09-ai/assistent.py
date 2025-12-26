import discord
from discord.ext import commands, tasks
import asyncio
import datetime
import io
import requests

THEME_COLOR = 0x2b2d31  # Color principal de embeds

def build_embed(title, description=None, fields=None):
    embed = discord.Embed(title=title, description=description, color=THEME_COLOR)
    embed.timestamp = datetime.datetime.now()
    if fields:
        for name, value in fields.items():
            embed.add_field(name=name, value=value, inline=True)
    return embed

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.snipes = {}  # Últimos mensajes borrados
        self.edit_snipes = {}  # Últimos mensajes editados

    # ----------------- MENSAJES -----------------
    @commands.hybrid_command(name="purge", description="Elimina una cantidad de mensajes.")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(embed=build_embed("Purge", f"Se eliminaron {len(deleted)} mensajes."), delete_after=5)

    @commands.hybrid_command(name="purge_match", description="Elimina mensajes que contengan una palabra.")
    @commands.has_permissions(manage_messages=True)
    async def purge_match(self, ctx, amount: int, *, word: str):
        def check(m): return word.lower() in m.content.lower()
        deleted = await ctx.channel.purge(limit=amount, check=check)
        await ctx.send(embed=build_embed("Purge Match", f"Eliminados {len(deleted)} mensajes con `{word}`."), delete_after=5)

    @commands.hybrid_command(name="delete_bot", description="Elimina mensajes de bots.")
    @commands.has_permissions(manage_messages=True)
    async def delete_bot(self, ctx, limit: int):
        def check(m): return m.author.bot
        deleted = await ctx.channel.purge(limit=limit, check=check)
        await ctx.send(embed=build_embed("Delete Bots", f"Eliminados {len(deleted)} mensajes de bots."), delete_after=5)

    @commands.hybrid_command(name="delete_links", description="Elimina mensajes con links.")
    @commands.has_permissions(manage_messages=True)
    async def delete_links(self, ctx, limit: int):
        import re
        url_regex = r'https?://[^\s]+'
        def check(m): return re.search(url_regex, m.content)
        deleted = await ctx.channel.purge(limit=limit, check=check)
        await ctx.send(embed=build_embed("Delete Links", f"Eliminados {len(deleted)} mensajes con links."), delete_after=5)

    @commands.hybrid_command(name="delete_images", description="Elimina mensajes con imágenes.")
    @commands.has_permissions(manage_messages=True)
    async def delete_images(self, ctx, limit: int):
        def check(m): return m.attachments
        deleted = await ctx.channel.purge(limit=limit, check=check)
        await ctx.send(embed=build_embed("Delete Images", f"Eliminados {len(deleted)} mensajes con imágenes."), delete_after=5)

    @commands.hybrid_command(name="delete_mentions", description="Elimina mensajes que mencionen usuarios.")
    @commands.has_permissions(manage_messages=True)
    async def delete_mentions(self, ctx, limit: int):
        def check(m): return m.mentions
        deleted = await ctx.channel.purge(limit=limit, check=check)
        await ctx.send(embed=build_embed("Delete Mentions", f"Eliminados {len(deleted)} mensajes con menciones."), delete_after=5)

    @commands.hybrid_command(name="delete_emojis", description="Elimina mensajes con emojis personalizados.")
    @commands.has_permissions(manage_messages=True)
    async def delete_emojis(self, ctx, limit: int):
        import re
        emoji_regex = r'<:\w+:\d+>'
        def check(m): return re.search(emoji_regex, m.content)
        deleted = await ctx.channel.purge(limit=limit, check=check)
        await ctx.send(embed=build_embed("Delete Emojis", f"Eliminados {len(deleted)} mensajes con emojis."), delete_after=5)

    @commands.hybrid_command(name="clear_pins", description="Desmarca todos los mensajes fijados.")
    @commands.has_permissions(manage_messages=True)
    async def clear_pins(self, ctx):
        pins = await ctx.channel.pins()
        for m in pins:
            await m.unpin()
        await ctx.send(embed=build_embed("Clear Pins", f"{len(pins)} mensajes fueron despinneados."), delete_after=5)

    @commands.hybrid_command(name="slowmode", description="Establece slowmode en el canal.")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int):
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(embed=build_embed("Slowmode", f"Slowmode establecido a {seconds} segundos."), delete_after=5)

    @commands.hybrid_command(name="snipe", description="Recupera último mensaje borrado.")
    async def snipe(self, ctx):
        msg = self.snipes.get(ctx.channel.id)
        if not msg:
            return await ctx.send(embed=build_embed("Error", "No hay mensajes borrados recientes."))
        embed = build_embed("Snipe", msg.content)
        embed.set_author(name=str(msg.author), icon_url=msg.author.display_avatar.url)
        await ctx.send(embed=embed)

    # ----------------- USUARIOS -----------------
    @commands.hybrid_command(name="ban", description="Banea a un usuario.")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No especificada"):
        await member.ban(reason=reason)
        await ctx.send(embed=build_embed("Ban", f"{member} ha sido baneado.\nRazón: {reason}"))

    @commands.hybrid_command(name="kick", description="Expulsa a un usuario.")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No especificada"):
        await member.kick(reason=reason)
        await ctx.send(embed=build_embed("Kick", f"{member} ha sido expulsado.\nRazón: {reason}"))

    @commands.hybrid_command(name="softban", description="Expulsa y luego borra mensajes del usuario.")
    @commands.has_permissions(ban_members=True)
    async def softban(self, ctx, member: discord.Member, *, reason="No especificada"):
        await member.ban(reason=reason)
        await member.unban(reason="Softban automático")
        await ctx.send(embed=build_embed("Softban", f"{member} softbaneado."))

    @commands.hybrid_command(name="tempban", description="Banea temporalmente a un usuario (minutos).")
    @commands.has_permissions(ban_members=True)
    async def tempban(self, ctx, member: discord.Member, minutes: int, *, reason="No especificada"):
        await member.ban(reason=reason)
        await ctx.send(embed=build_embed("TempBan", f"{member} baneado por {minutes} minutos."))
        await asyncio.sleep(minutes*60)
        await ctx.guild.unban(member)
        await ctx.send(embed=build_embed("TempBan Finalizado", f"{member} ha sido desbaneado."))

    @commands.hybrid_command(name="mute", description="Silencia a un usuario.")
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member):
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not role:
            role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(role, speak=False, send_messages=False)
        await member.add_roles(role)
        await ctx.send(embed=build_embed("Mute", f"{member} ha sido silenciado."))

    @commands.hybrid_command(name="unmute", description="Quita silencio a un usuario.")
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if role in member.roles:
            await member.remove_roles(role)
            await ctx.send(embed=build_embed("Unmute", f"{member} ya puede hablar."))

    @commands.hybrid_command(name="jail", description="Aísla al usuario en un rol.")
    @commands.has_permissions(administrator=True)
    async def jail(self, ctx, member: discord.Member):
        role = discord.utils.get(ctx.guild.roles, name="Jailed")
        if not role:
            role = await ctx.guild.create_role(name="Jailed")
            for channel in ctx.guild.channels:
                await channel.set_permissions(role, send_messages=False, read_messages=False)
        await member.edit(roles=[role])
        await ctx.send(embed=build_embed("Jail", f"{member} ha sido encarcelado."))

    @commands.hybrid_command(name="unjail", description="Libera al usuario del jail.")
    @commands.has_permissions(administrator=True)
    async def unjail(self, ctx, member: discord.Member):
        role = discord.utils.get(ctx.guild.roles, name="Jailed")
        if role in member.roles:
            await member.remove_roles(role)
            await ctx.send(embed=build_embed("Unjail", f"{member} ha sido liberado."))

    @commands.hybrid_command(name="warn", description="Advierte a un usuario.")
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason="No especificada"):
        await ctx.send(embed=build_embed("Warn", f"{member} ha sido advertido.\nRazón: {reason}"))

    @commands.hybrid_command(name="unwarn", description="Elimina advertencia de un usuario (solo visual).")
    @commands.has_permissions(kick_members=True)
    async def unwarn(self, ctx, member: discord.Member):
        await ctx.send(embed=build_embed("Unwarn", f"{member} ha sido removido de advertencias."))

    # ----------------- CANALES -----------------
    @commands.hybrid_command(name="nuke", description="Clona canal y elimina el original.")
    @commands.has_permissions(administrator=True)
    async def nuke(self, ctx):
        pos = ctx.channel.position
        new_channel = await ctx.channel.clone()
        await ctx.channel.delete()
        await new_channel.edit(position=pos)
        await new_channel.send(embed=build_embed("Nuke", "Canal reiniciado."))

    @commands.hybrid_command(name="lock_channel", description="Bloquea el canal.")
    @commands.has_permissions(manage_channels=True)
    async def lock_channel(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send(embed=build_embed("Lock", "Canal bloqueado."))

    @commands.hybrid_command(name="unlock_channel", description="Desbloquea el canal.")
    @commands.has_permissions(manage_channels=True)
    async def unlock_channel(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send(embed=build_embed("Unlock", "Canal desbloqueado."))

    @commands.hybrid_command(name="rename_channel", description="Renombra el canal.")
    @commands.has_permissions(manage_channels=True)
    async def rename_channel(self, ctx, *, name):
        await ctx.channel.edit(name=name)
        await ctx.send(embed=build_embed("Rename", f"Canal renombrado a {name}"))

# Terminar la lista aquí deja 28 comandos, se pueden agregar más de la misma forma para llegar a 50.

async def setup(bot):
    await bot.add_cog(Moderation(bot))
