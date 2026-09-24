import os
import sqlite3
from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands

# ==========================================
# 🗄️ CONFIGURAÇÃO DO BANCO DE DADOS
# ==========================================
def init_db():
    conn = sqlite3.connect("zaya.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            guild_id TEXT NOT NULL,
            clock_in TEXT NOT NULL,
            clock_out TEXT,
            status TEXT DEFAULT 'ativo'
        )
    """)
    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect("zaya.db")

# ==========================================
# 🧩 VIEWS E INTERFACES (BOTÕES)
# ==========================================
class PontoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Iniciar Ponto", style=discord.ButtonStyle.success, emoji="🟢", custom_id="ponto_iniciar")
    async def iniciar_ponto(self, interaction: discord.Interaction, button: discord.ui.Button):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM time_entries WHERE user_id = ? AND guild_id = ? AND status = 'ativo'", 
                       (str(interaction.user.id), str(interaction.guild_id)))
        ativo = cursor.fetchone()
        
        if ativo:
            await interaction.response.send_message("⚠️ Já tens um bate-ponto em aberto!", ephemeral=True)
            conn.close()
            return

        agora = datetime.now()
        data_str = agora.strftime("%d/%m/%Y às %H:%M")
        
        cursor.execute("INSERT INTO time_entries (user_id, guild_id, clock_in, status) VALUES (?, ?, ?, 'ativo')",
                       (str(interaction.user.id), str(interaction.guild_id), data_str))
        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="🟢 BATE-PONTO INICIADO",
            description=f"👤 **Membro:** {interaction.user.mention}\n🕐 **Entrada:** {agora.strftime('%H:%M')}\n📅 **Data:** {agora.strftime('%d/%m/%Y')}",
            color=0x2B2D31
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Encerrar Ponto", style=discord.ButtonStyle.danger, emoji="🔴", custom_id="ponto_encerrar")
    async def encerrar_ponto(self, interaction: discord.Interaction, button: discord.ui.Button):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, clock_in FROM time_entries WHERE user_id = ? AND guild_id = ? AND status = 'ativo'", 
                       (str(interaction.user.id), str(interaction.guild_id)))
        ativo = cursor.fetchone()
        
        if not ativo:
            await interaction.response.send_message("⚠️ Não tens nenhum bate-ponto em aberto!", ephemeral=True)
            conn.close()
            return

        entry_id, clock_in = ativo
        saida_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
        
        cursor.execute("UPDATE time_entries SET clock_out = ?, status = 'encerrado' WHERE id = ?", (saida_str, entry_id))
        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="🔴 BATE-PONTO ENCERRADO",
            description=f"👤 **Membro:** {interaction.user.mention}\n🕐 **Entrada:** {clock_in}\n🕐 **Saída:** {datetime.now().strftime('%H:%M')}",
            color=0x2B2D31
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class PainelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Bate-Ponto", style=discord.ButtonStyle.secondary, emoji="🕐", custom_id="btn_ponto")
    async def btn_ponto(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🕐 Utilize o comando `/ponto` para abrir o controlo de jornada.", ephemeral=True)

    @discord.ui.button(label="Minha Ficha", style=discord.ButtonStyle.secondary, emoji="👤", custom_id="btn_ficha")
    async def btn_ficha(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("👤 A carregar a sua ficha individual...", ephemeral=True)

    @discord.ui.button(label="Membros", style=discord.ButtonStyle.secondary, emoji="👥", custom_id="btn_membros")
    async def btn_membros(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("👥 A abrir a gestão de membros...", ephemeral=True)

    @discord.ui.button(label="Promoções", style=discord.ButtonStyle.secondary, emoji="📈", custom_id="btn_promocoes")
    async def btn_promocoes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("📈 A abrir o sistema de promoções...", ephemeral=True)

    @discord.ui.button(label="Advertências", style=discord.ButtonStyle.secondary, emoji="⚠️", custom_id="btn_advertencias")
    async def btn_advertencias(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⚠️ A abrir o painel de advertências...", ephemeral=True)

    @discord.ui.button(label="Relatórios", style=discord.ButtonStyle.secondary, emoji="📊", custom_id="btn_relatorios")
    async def btn_relatorios(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("📊 A gerar relatórios da organização...", ephemeral=True)

    @discord.ui.button(label="Administração", style=discord.ButtonStyle.danger, emoji="⚙️", custom_id="btn_admin")
    async def btn_admin(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⚙️ Painel restrito a administradores.", ephemeral=True)

# ==========================================
# 🤖 INICIALIZAÇÃO DO BOT
# ==========================================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    init_db()
    try:
        synced = await bot.tree.sync()
        print(f"📈 Sincronizados {len(synced)} comandos de barra.")
    except Exception as e:
        print(f"❌ Erro ao sincronizar comandos: {e}")
    print(f"🛡️ ZAYA conectado com sucesso como {bot.user} (ID: {bot.user.id})")

# Comando /ponto
@bot.tree.command(name="ponto", description="Abre o painel interativo de controlo de jornada.")
async def ponto(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛡️ CONTROLO DE JORNADA",
        description="Utilize os botões abaixo para iniciar ou encerrar o seu expediente atual.",
        color=0x2B2D31
    )
    await interaction.response.send_message(embed=embed, view=PontoView(), ephemeral=True)

# Comando /painel
@bot.tree.command(name="painel", description="Exibe o painel principal de gestão organizacional.")
async def painel(interaction: discord.Interaction):
    descricao = (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🟢 **Sistema operacional**\n\n"
        "👥 **Membros:** 87\n"
        "🟢 **Em serviço:** 14\n"
        "⚠️ **Advertências:** 23\n"
        "📈 **Promoções:** 31\n"
        "🕐 **Pontos hoje:** 42\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )

    embed = discord.Embed(
        title="🛡️ ZAYA — GESTÃO ORGANIZACIONAL",
        description=descricao,
        color=0x2B2D31
    )
    embed.set_footer(text="AEGIS — Sistema de Gestão GTA RP")

    # Responde primeiro à interação do slash command com ephemeral para evitar loading infinito, e envia o painel no canal
    await interaction.response.send_message("✅ Painel principal gerado com sucesso!", ephemeral=True)
    await interaction.channel.send(embed=embed, view=PainelView())

# Execução do Bot integrando com as variáveis de ambiente da Discloud
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("❌ Erro: A variável DISCORD_TOKEN não foi configurada na Discloud!")
    else:
        bot.run(TOKEN)
