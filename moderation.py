import discord
from discord.ext import commands
from core.embeds import base_embed, success_embed, error_embed, info_embed
import asyncio

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------------------
    # PURGE POR PALABRA
    # ----------------------
    @commands.hybrid_command(name="purge_match", description="Borra mensajes que contengan una palabra específica.")
    @commands.has_permissions(manage_messages=True)
    async def purge_match(self, ctx, limit: int, *, word: str):
        def check(m): return word.lower() in m.content.lower()
        deleted = await ctx.channel.purge(limit=limit, check=check)
        await ctx.send(embed=success_embed(f"Eliminados {len(deleted)} mensajes con `{word}`"), delete_after=5)

    # ----------------------
    # JAIL (AISLAMIENTO)
    # ----------------------
    @commands.hybrid_command(name="jail", description="Aísla a un usuario en un rol de castigo.")
    @commands.has_permissions(administrator=True)
    async def jail(self, ctx, member: discord.Member):
        jail_role = discord.utils.get(ctx.guild.roles, name="Jailed")
        if not jail_role:
            jail_role = await ctx.guild.create_role(name="Jailed", color=discord.Color.dark_grey())
            for channel in ctx.guild.channels:
                await channel.set_permissions(jail_role, send_messages=False, read_messages=False)

        await member.edit(roles=[jail_role])
        await ctx.send(embed=success_embed(f"{member.mention} ha sido encarcelado."))

    # ----------------------
    # UNJAIL (LIBERACIÓN)
    # ----------------------
    @commands.hybrid_command(name="unjail", description="Libera a un usuario encarcelado.")
    @commands.has_permissions(administrator=True)
    async def unjail(self, ctx, member: discord.Member):
        jail_role = discord.utils.get(ctx.guild.roles, name="Jailed")
        if jail_role in member.roles:
            await member.remove_roles(jail_role)
            await ctx.send(embed=success_embed(f"{member.mention} ya no está encarcelado."))
        else:
            await ctx.send(embed=info_embed("Info", f"{member.mention} no estaba encarcelado."))

    # ----------------------
    # DAR ROL A TODOS
    # ----------------------
    @commands.hybrid_command(name="roleall", description="Asigna un rol a todos los miembros (PELIGROSO).")
    @commands.has_permissions(administrator=True)
    async def roleall(self, ctx, role: discord.Role):
        msg = await ctx.send(embed=info_embed("Procesando...", "Esto puede tardar."))
        count = 0
        for member in ctx.guild.members:
            if not member.bot and role not in member.roles:
                try:
                    await member.add_roles(role)
                    count += 1
                    await asyncio.sleep(0.5)  # Evitar rate limit
                except: pass
        await msg.edit(embed=success_embed(f"Rol {role.name} asignado a {count} usuarios."))

    # ----------------------
    # NUKE (RESETEO DE CANAL)
    # ----------------------
    @commands.hybrid_command(name="nuke", description="Clona y borra el canal actual (reset completo).")
    @commands.has_permissions(administrator=True)
    async def nuke(self, ctx):
        pos = ctx.channel.position
        new_channel = await ctx.channel.clone(reason="Nuke Protocol")
        await ctx.channel.delete()
        await new_channel.edit(position=pos)
        await new_channel.send(embed=success_embed("Canal nukeado. Historial eliminado."))

    # ----------------------
    # BAN
    # ----------------------
    @commands.hybrid_command(name="ban", description="Banea a un usuario del servidor.")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="N/A"):
        await member.ban(reason=reason)
        await ctx.send(embed=success_embed(f"{member} ha sido baneado.\nMotivo: {reason}"))

    # ----------------------
    # KICK
    # ----------------------
    @commands.hybrid_command(name="kick", description="Expulsa a un usuario del servidor.")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="N/A"):
        await member.kick(reason=reason)
        await ctx.send(embed=success_embed(f"{member} ha sido expulsado.\nMotivo: {reason}"))

async def setup(bot):
    await bot.add_cog(Moderation(bot))
