import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime
import asyncio
import io
import requests
from dotenv import load_dotenv
from collections import deque

load_dotenv()

# --- CONFIGURACIÓN DE ÉLITE ---
TOKEN = os.getenv("TOKEN")
PREFIX = "$"
THEME_COLOR = 0x2b2d31  # Dark Grey (Discord Developer Mode Color)

intents = discord.Intents.all()

class NexusBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=PREFIX,
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        # Memoria temporal avanzada (deque limita el tamaño automáticamente)
        self.snipes = {} 
        self.edit_snipes = {}

    async def setup_hook(self):
        await self.add_cog(SysAdmin(self))
        await self.add_cog(NetworkTools(self))
        await self.add_cog(UserIntelligence(self))
        await self.tree.sync()
        print(f">> SYSTEM ONLINE: {self.user} | ID: {self.user.id}")

    async def on_message_delete(self, message):
        if message.author.bot: return
        self.snipes[message.channel.id] = message

    async def on_message_edit(self, before, after):
        if before.author.bot: return
        self.edit_snipes[before.channel.id] = (before, after)

bot = NexusBot()

# --- UTILIDAD VISUAL ---
def build_embed(title, description=None, fields=None):
    embed = discord.Embed(title=title, description=description, color=THEME_COLOR)
    embed.timestamp = datetime.datetime.now()
    if fields:
        for name, value in fields.items():
            embed.add_field(name=name, value=value, inline=True)
    return embed

# --- COMANDO HELP (REQUERIDO) ---
@bot.command(name="help")
async def help_command(ctx):
    msg = (
        "**Prefijo:** `$`\n"
        "**Slash:** `/`\n\n"
        "**Comandos:**\n"
        "$ping, $avatar, $say\n"
        "$ban, $kick, $help\n\n"
        "_Usa / para ver el menú completo._"
    )
    await ctx.send(msg)

# ====================================================
# MODULO 1: SYSADMIN (MODERACIÓN DE ALTO NIVEL)
# ====================================================
class SysAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="purge_match", description="Borra mensajes que contengan una palabra específica.")
    @commands.has_permissions(manage_messages=True)
    async def purge_match(self, ctx, limit: int, *, word: str):
        def check(m): return word.lower() in m.content.lower()
        deleted = await ctx.channel.purge(limit=limit, check=check)
        await ctx.send(embed=build_embed("Purge Match", f"Eliminados {len(deleted)} mensajes conteniendo: `{word}`"), delete_after=5)

    @commands.hybrid_command(name="jail", description="Aísla a un usuario en un rol de castigo.")
    @commands.has_permissions(administrator=True)
    async def jail(self, ctx, member: discord.Member):
        jail_role = discord.utils.get(ctx.guild.roles, name="Jailed")
        if not jail_role:
            jail_role = await ctx.guild.create_role(name="Jailed", color=discord.Color.from_rgb(1, 1, 1))
            for channel in ctx.guild.channels:
                await channel.set_permissions(jail_role, send_messages=False, read_messages=False)
        
        # Guardar roles anteriores (Lógica simplificada para ejemplo)
        await member.edit(roles=[jail_role])
        await ctx.send(embed=build_embed("Usuario Encarcelado", f"{member.mention} ha sido aislado del servidor."))

    @commands.hybrid_command(name="unjail", description="Libera al usuario.")
    @commands.has_permissions(administrator=True)
    async def unjail(self, ctx, member: discord.Member):
        jail_role = discord.utils.get(ctx.guild.roles, name="Jailed")
        if jail_role in member.roles:
            await member.remove_roles(jail_role)
            await ctx.send(embed=build_embed("Usuario Liberado", f"{member.mention} ya no está encarcelado."))

    @commands.hybrid_command(name="roleall", description="Da un rol a TODOS los humanos (PELIGROSO).")
    @commands.has_permissions(administrator=True)
    async def roleall(self, ctx, role: discord.Role):
        msg = await ctx.send(embed=build_embed("Procesando...", "Esto puede tardar. No apagues el bot."))
        count = 0
        for member in ctx.guild.members:
            if not member.bot and role not in member.roles:
                try:
                    await member.add_roles(role)
                    count += 1
                    await asyncio.sleep(0.5) # Evitar rate limits
                except: pass
        await msg.edit(embed=build_embed("Operación Finalizada", f"Rol {role.name} añadido a {count} usuarios."))

    @commands.hybrid_command(name="nuke", description="Clona el canal y borra el antiguo (Reset completo).")
    @commands.has_permissions(administrator=True)
    async def nuke(self, ctx):
        pos = ctx.channel.position
        new_channel = await ctx.channel.clone(reason="Nuke Protocol")
        await ctx.channel.delete()
        await new_channel.edit(position=pos)
        await new_channel.send(embed=build_embed("Canal Nukeado", "Historial de chat eliminado permanentemente."))

    @commands.hybrid_command(name="ban", description="Ban estándar.")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="N/A"):
        await member.ban(reason=reason)
        await ctx.send(embed=build_embed("Ban Executed", f"Target: {member}\nID: {member.id}"))

    @commands.hybrid_command(name="kick", description="Kick estándar.")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="N/A"):
        await member.kick(reason=reason)
        await ctx.send(embed=build_embed("Kick Executed", f"Target: {member}"))

# ====================================================
# MODULO 2: NETWORK TOOLS (UTILIDAD TÉCNICA)
# ====================================================
class NetworkTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="archive", description="Descarga el chat actual en un archivo .txt")
    @commands.has_permissions(administrator=True)
    async def archive(self, ctx, limit: int = 1000):
        buffer = io.StringIO()
        messages = [message async for message in ctx.channel.history(limit=limit)]
        messages.reverse()
        
        buffer.write(f"ARCHIVO DE CHAT: {ctx.channel.name} | {datetime.datetime.now()}\n\n")
        for msg in messages:
            buffer.write(f"[{msg.created_at.strftime('%Y-%m-%d %H:%M')}] {msg.author}: {msg.content}\n")
        
        buffer.seek(0)
        await ctx.send(file=discord.File(io.BytesIO(buffer.getvalue().encode()), filename=f"archive-{ctx.channel.name}.txt"))

    @commands.hybrid_command(name="steal", description="Roba un emoji y lo agrega al servidor.")
    @commands.has_permissions(manage_emojis=True)
    async def steal(self, ctx, emoji: discord.PartialEmoji, name: str = None):
        try:
            name = name or emoji.name
            response = requests.get(emoji.url)
            new_emoji = await ctx.guild.create_custom_emoji(name=name, image=response.content)
            await ctx.send(embed=build_embed("Emoji Robado", f"Emoji agregado: {new_emoji}"))
        except:
            await ctx.send("Error: No puedo acceder a ese emoji.")

    @commands.hybrid_command(name="snipe", description="Recupera el último mensaje borrado.")
    async def snipe(self, ctx):
        msg = self.bot.snipes.get(ctx.channel.id)
        if not msg:
            return await ctx.send(embed=build_embed("Error", "No hay registros recientes."))
        
        embed = build_embed("Snipe", msg.content)
        embed.set_author(name=str(msg.author), icon_url=msg.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="editsnipe", description="Muestra el contenido antes de ser editado.")
    async def editsnipe(self, ctx):
        data = self.bot.edit_snipes.get(ctx.channel.id)
        if not data:
            return await ctx.send(embed=build_embed("Error", "No hay ediciones recientes."))
        
        before, after = data
        embed = build_embed("Edit Snipe", f"**Antes:**\n{before.content}\n\n**Ahora:**\n{after.content}")
        embed.set_author(name=str(before.author), icon_url=before.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="firstmsg", description="Genera link al primer mensaje del canal.")
    async def firstmsg(self, ctx):
        msg = [m async for m in ctx.channel.history(limit=1, oldest_first=True)][0]
        await ctx.send(embed=build_embed("Primer Mensaje", f"[Click para saltar]({msg.jump_url})"))

    @commands.hybrid_command(name="source", description="Muestra el código interno de un comando.")
    async def source(self, ctx, command: str):
        cmd = self.bot.get_command(command)
        if not cmd: return await ctx.send("Comando desconocido.")
        await ctx.send(f"Comando `{command}` pertenece al módulo: `{cmd.cog_name}`")

    @commands.hybrid_command(name="servericon", description="Descarga el icono del servidor.")
    async def servericon(self, ctx):
        if ctx.guild.icon:
            await ctx.send(embed=build_embed("Server Icon", "").set_image(url=ctx.guild.icon.url))
        else:
            await ctx.send("Este servidor no tiene icono.")

# ====================================================
# MODULO 3: USER INTELLIGENCE (OSINT & PERFIL)
# ====================================================
class UserIntelligence(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="spotify", description="Muestra qué está escuchando el usuario.")
    async def spotify(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        spotify_activity = next((a for a in member.activities if isinstance(a, discord.Spotify)), None)
        
        if not spotify_activity:
            return await ctx.send(embed=build_embed("Error", f"{member.name} no está escuchando Spotify."))
        
        embed = discord.Embed(title=f"Spotify: {member.name}", color=0x1DB954)
        embed.add_field(name="Canción", value=spotify_activity.title, inline=False)
        embed.add_field(name="Artista", value=spotify_activity.artist, inline=True)
        embed.add_field(name="Álbum", value=spotify_activity.album, inline=True)
        embed.set_thumbnail(url=spotify_activity.album_cover_url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="banner", description="Extrae el banner del perfil.")
    async def banner(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user = await self.bot.fetch_user(member.id)
        if user.banner:
            await ctx.send(embed=build_embed(f"Banner de {user.name}").set_image(url=user.banner.url))
        else:
            await ctx.send(embed=build_embed("Info", "Usuario sin banner."))

    @commands.hybrid_command(name="devices", description="Verifica dispositivos conectados.")
    async def devices(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        devs = []
        if member.desktop_status != discord.Status.offline: devs.append("Desktop 🖥️")
        if member.mobile_status != discord.Status.offline: devs.append("Mobile 📱")
        if member.web_status != discord.Status.offline: devs.append("Web 🌐")
        
        await ctx.send(embed=build_embed(f"Sesiones de {member.name}", " | ".join(devs) if devs else "Offline"))

    @commands.hybrid_command(name="shared", description="Muestra en cuántos servidores coincidimos.")
    async def shared(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        count = 0
        guilds = []
        for g in self.bot.guilds:
            if g.get_member(member.id):
                count += 1
                if count <= 5: guilds.append(g.name)
        
        desc = f"Coincidimos en **{count}** servidores."
        if count > 5: desc += f"\nEjemplos: {', '.join(guilds)}..."
        await ctx.send(embed=build_embed("Rastreo Mutuo", desc))

    @commands.hybrid_command(name="say", description="Repite el mensaje.")
    async def say(self, ctx, *, message):
        await ctx.send(message)

    @commands.hybrid_command(name="avatar", description="Muestra el avatar.")
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        await ctx.send(embed=build_embed(f"Avatar: {member.name}").set_image(url=member.display_avatar.url))

    @commands.hybrid_command(name="ping", description="Latencia.")
    async def ping(self, ctx):
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms")

# --- CONTROL DE ERRORES GLOBAL ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=build_embed("Acceso Denegado", "No tienes permisos suficientes."), delete_after=5)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=build_embed("Error de Sintaxis", f"Faltan argumentos. Usa `{PREFIX}help`."), delete_after=5)
    elif isinstance(error, commands.CommandNotFound):
        pass # Ignorar comandos inexistentes
    else:
        print(f"Error Sistema: {error}")

if __name__ == "__main__":
    bot.run(TOKEN)
