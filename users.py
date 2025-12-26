import discord
from discord.ext import commands
from core.embeds import base_embed, success_embed, error_embed, info_embed

class UserCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------------------
    # AVATAR
    # ----------------------
    @commands.hybrid_command(name="avatar", description="Muestra el avatar de un usuario.")
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        await ctx.send(embed=base_embed(f"Avatar de {member}", "").set_image(url=member.display_avatar.url))

    # ----------------------
    # BANNER
    # ----------------------
    @commands.hybrid_command(name="banner", description="Muestra el banner de un usuario.")
    async def banner(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user = await self.bot.fetch_user(member.id)
        if user.banner:
            await ctx.send(embed=base_embed(f"Banner de {user.name}").set_image(url=user.banner.url))
        else:
            await ctx.send(embed=info_embed("Info", f"{member.name} no tiene banner."))

    # ----------------------
    # SPOTIFY
    # ----------------------
    @commands.hybrid_command(name="spotify", description="Muestra la canción de Spotify que está escuchando un usuario.")
    async def spotify(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        spotify_activity = next((a for a in member.activities if isinstance(a, discord.Spotify)), None)
        if not spotify_activity:
            return await ctx.send(embed=info_embed("Error", f"{member.name} no está escuchando Spotify."))
        embed = base_embed(f"Spotify - {member.name}")
        embed.add_field(name="Canción", value=spotify_activity.title, inline=False)
        embed.add_field(name="Artista", value=spotify_activity.artist, inline=True)
        embed.add_field(name="Álbum", value=spotify_activity.album, inline=True)
        embed.set_thumbnail(url=spotify_activity.album_cover_url)
        await ctx.send(embed=embed)

    # ----------------------
    # DISPOSITIVOS
    # ----------------------
    @commands.hybrid_command(name="devices", description="Muestra los dispositivos conectados de un usuario.")
    async def devices(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        devs = []
        if member.desktop_status != discord.Status.offline: devs.append("Desktop 🖥️")
        if member.mobile_status != discord.Status.offline: devs.append("Mobile 📱")
        if member.web_status != discord.Status.offline: devs.append("Web 🌐")
        await ctx.send(embed=base_embed(f"Sesiones de {member.name}", " | ".join(devs) if devs else "Offline"))

    # ----------------------
    # SERVIDORES COMPARTIDOS
    # ----------------------
    @commands.hybrid_command(name="shared", description="Muestra en cuántos servidores coincidimos con un usuario.")
    async def shared(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        count = 0
        guilds = []
        for g in self.bot.guilds:
            if g.get_member(member.id):
                count += 1
                if count <= 5:
                    guilds.append(g.name)
        desc = f"Coincidimos en **{count}** servidores."
        if count > 5:
            desc += f"\nEjemplos: {', '.join(guilds)}..."
        await ctx.send(embed=base_embed("Servidores Compartidos", desc))

    # ----------------------
    # SAY
    # ----------------------
    @commands.hybrid_command(name="say", description="Repite un mensaje.")
    async def say(self, ctx, *, message):
        await ctx.send(message)

    # ----------------------
    # PING
    # ----------------------
    @commands.hybrid_command(name="ping", description="Muestra la latencia del bot.")
    async def ping(self, ctx):
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms")

    # ----------------------
    # INFO DEL USUARIO
    # ----------------------
    @commands.hybrid_command(name="userinfo", description="Muestra información detallada del usuario.")
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = base_embed(f"Información de {member.name}")
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Nombre", value=member.name, inline=True)
        embed.add_field(name="Cuenta creada", value=member.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="Se unió al servidor", value=member.joined_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="Roles", value=", ".join([r.mention for r in member.roles if r.name != "@everyone"]), inline=False)
        await ctx.send(embed=embed)

    # ----------------------
    # TOP ROLES (PRÓXIMOS COMANDOS PARA EXTENDER)
    # ----------------------
    # Puedes agregar más comandos como: banner, mutual servers, stats, last messages, badges, achievements, etc.
    # Solo sigue la misma estructura de hybrid_command con embeds bonitos.

async def setup(bot):
    await bot.add_cog(UserCommands(bot))
