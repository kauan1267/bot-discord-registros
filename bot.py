import discord
from discord.ext import commands, tasks
import asyncio
from collections import defaultdict
from discord.ui import Button, View
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

CANAL_REGISTROS_ID = 1368748831272996924
CANAL_RELATORIOS_ID = 1368766789101817866

banimentos_count = defaultdict(int)
jails_count = defaultdict(int)

# Armazenar histórico semanal temporariamente
banimentos_usuarios = defaultdict(int)
jails_usuarios = defaultdict(int)

@tasks.loop(hours=168)  # A cada 7 dias
async def enviar_relatorio_semanal():
    canal = bot.get_channel(CANAL_RELATORIOS_ID)
    if not canal:
        return

    embed = discord.Embed(title="📊 Relatório Semanal de Ações", color=discord.Color.orange())
    if not banimentos_usuarios and not jails_usuarios:
        embed.description = "Nenhuma ação registrada nesta semana."
    else:
        for user_id, count in banimentos_usuarios.items():
            embed.add_field(name=f"<@{user_id}>", value=f"📛 Banimentos: {count}", inline=False)
        for user_id, count in jails_usuarios.items():
            embed.add_field(name=f"<@{user_id}>", value=f"⛓️ Jails: {count}", inline=False)

    await canal.send(embed=embed)
    banimentos_usuarios.clear()
    jails_usuarios.clear()

async def create_embed():
    embed = discord.Embed(
        title="📝 Registros de Ações",
        description="Selecione uma das opções abaixo para registrar uma ação (banimento ou jail).",
        color=discord.Color.green()
    )
    return embed

async def ban_button_callback(interaction):
    await interaction.response.send_message("Por favor, forneça o ID do player banido:", ephemeral=True)

    def check(msg):
        return msg.author == interaction.user and msg.channel == interaction.channel

    try:
        id_msg = await bot.wait_for("message", check=check, timeout=60)
        user_id = id_msg.content
        await id_msg.delete()

        motivo = "Hacker"  # Motivo automático

        autor_id = interaction.user.id
        banimentos_count[autor_id] += 1
        banimentos_usuarios[autor_id] += 1
        canal = bot.get_channel(CANAL_REGISTROS_ID)
        embed = discord.Embed(
            title="📛 Banimento Registrado",
            description=f"**ID do Player Banido**: {user_id}
**Motivo**: {motivo}
**Banido por**: <@{autor_id}>
**Número de banimentos**: {banimentos_count[autor_id]}",
            color=discord.Color.red()
        )
        await canal.send(embed=embed)
        await interaction.followup.send("Banimento registrado com sucesso!", ephemeral=True)
    except asyncio.TimeoutError:
        await interaction.followup.send("Tempo esgotado. Tente novamente.", ephemeral=True)

async def jail_button_callback(interaction):
    await interaction.response.send_message("Por favor, forneça o ID do player que quitou no jail:", ephemeral=True)

    def check(msg):
        return msg.author == interaction.user and msg.channel == interaction.channel

    try:
        id_msg = await bot.wait_for("message", check=check, timeout=60)
        user_id = id_msg.content
        await id_msg.delete()

        motivo = "Quitou no Jail!"

        autor_id = interaction.user.id
        jails_count[autor_id] += 1
        jails_usuarios[autor_id] += 1
        canal = bot.get_channel(CANAL_REGISTROS_ID)
        embed = discord.Embed(
            title="⛓️ Jail Registrado",
            description=f"**ID do Player**: {user_id}
**Motivo**: {motivo}
**Jail registrado por**: <@{autor_id}>
**Número de jails**: {jails_count[autor_id]}",
            color=discord.Color.blue()
        )
        await canal.send(embed=embed)
        await interaction.followup.send("Jail registrado com sucesso!", ephemeral=True)
    except asyncio.TimeoutError:
        await interaction.followup.send("Tempo esgotado. Tente novamente.", ephemeral=True)

@bot.command()
async def registrar(ctx):
    ban_button = Button(label="Registrar Banimento", style=discord.ButtonStyle.danger)
    jail_button = Button(label="Registrar Jail", style=discord.ButtonStyle.blurple)
    ban_button.callback = ban_button_callback
    jail_button.callback = jail_button_callback

    view = View()
    view.add_item(ban_button)
    view.add_item(jail_button)
    embed = await create_embed()
    await ctx.send(embed=embed, view=view)

@bot.event
async def on_ready():
    print(f'Bot {bot.user} está online!')
    enviar_relatorio_semanal.start()

bot.run('SEU_TOKEN_AQUI')
