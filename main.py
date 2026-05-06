import discord
import aiohttp
import asyncio
import random
import os
import edge_tts
from datetime import datetime

TOKEN = os.environ.get("DISCORD_TOKEN")
WEBHOOK = os.environ.get("DISCORD_WEBHOOK")

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
intents.message_content = True  # necessário para comandos de texto

bot = discord.Client(intents=intents)

# >>> CONFIGURAÇÃO DE VOZ <<<
VOICE = "pt-BR-AntonioNeural"  # voz estável e suportada
CANAL_ID = 1501006139125534860  # substitua pelo ID do canal de voz

# Mensagens de entrada
entradas = [
    "⚠ FREQUÊNCIA DESCONHECIDA DETECTADA.",
    "█ alguém entrou na transmissão █",
    "ERRO_0x98 :: presença detectada",
    "[SISTEMA] conexão estabelecida",
    "voz detectada na escuridão",
    "█ USUÁRIO INVÁLIDO CONECTADO █",
    "anomalia detectada no canal",
    "algo entrou na call",
]

# Mensagens de saída
saidas = [
    "⛔ conexão encerrada",
    "sinal perdido",
    "█ transmissão interrompida █",
    "presença removida do sistema",
    "eco finalizado",
    "o silêncio voltou",
    "ERRO :: usuário desconectado",
]

# Frases de voz sombrias
frases_voz = [
    "Você não deveria estar aqui.",
    "Eu posso te ver.",
    "Bora brincar?",
    "Eu amo brincar.",
]

# Mensagens de erro/detecção
erros_deteccao = [
    "ERRO. ERRO. ERRO. 0 x 9 8. FALHA NO SISTEMA. INTRUSO DETECTADO. ALERTA VERMELHO."
]

fila_frases = []


# Funções de áudio
async def gerar_audio(texto, arquivo="voz.mp3"):
    print(f"[DEBUG] Gerando áudio: {texto[:50]}... -> {arquivo}")
    try:
        communicate = edge_tts.Communicate(texto, VOICE)
        await communicate.save(arquivo)
        print(f"[DEBUG] Áudio salvo em {arquivo}")
    except Exception as e:
        print(f"[DEBUG] Erro ao gerar áudio: {e}")

async def tocar_audio(voice, arquivo="voz.mp3"):
    print(f"[DEBUG] Tentando tocar: {arquivo}")
    if not os.path.exists(arquivo):
        print(f"[DEBUG] Arquivo {arquivo} não encontrado")
        return
    if not voice or not voice.is_connected():
        print("[DEBUG] Voice client não conectado")
        return

    source = discord.FFmpegPCMAudio(
        arquivo,
        options="-f mp3 -af aecho=0.8:0.9:1000:0.3,atempo=0.8"
    )
    voice.play(source)
    print("[DEBUG] Playback iniciado")
    while voice.is_playing():
        await asyncio.sleep(0.5)
    print("[DEBUG] Playback finalizado")


# Sequência de erros ao entrar
async def sequencia_deteccao(voice):
    for _ in range(2):
        frase = random.choice(erros_deteccao)
        await gerar_audio(frase, "erro.mp3")
        await tocar_audio(voice, "erro.mp3")
        await asyncio.sleep(2)


# Loop de frases sombrias
async def loop_frases_aleatorias(guild):
    global fila_frases
    while True:
        await asyncio.sleep(random.randint(300, 900))  # 5–15 minutos
        try:
            voice = guild.voice_client
            if voice and voice.is_connected() and not voice.is_playing():
                humanos = [m for m in voice.channel.members if not m.bot]
                if humanos:
                    if not fila_frases:
                        fila_frases = frases_voz.copy()
                        random.shuffle(fila_frases)
                    frase = fila_frases.pop()
                    await gerar_audio(frase)
                    await tocar_audio(voice)
        except Exception as e:
            print(f"Erro no loop de frases: {e}")


# Webhook para logs
async def enviar_webhook(msg):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"content": msg, "username": "SYSTEM_ERROR"}
            await session.post(WEBHOOK, json=payload)
    except Exception as e:
        print(f"Erro ao enviar webhook: {e}")


# Mantém o bot conectado ao canal fixo
async def manter_canal_fixo():
    await bot.wait_until_ready()
    while True:
        canal = bot.get_channel(CANAL_ID)
        if canal:
            guild = canal.guild
            voice = guild.voice_client
            if voice is None or not voice.is_connected():
                try:
                    await canal.connect()
                    print("[DEBUG] Reconectado ao canal fixo")
                except Exception as e:
                    print(f"Erro ao reconectar: {e}")
        await asyncio.sleep(120)  # intervalo maior para evitar desconexões


# Eventos
@bot.event
async def on_ready():
    print(f"Bot online como {bot.user}")
    for guild in bot.guilds:
        asyncio.create_task(loop_frases_aleatorias(guild))
    asyncio.create_task(manter_canal_fixo())


@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    hora = datetime.now().strftime("%H:%M:%S")

    # Entrou no canal fixo
    if before.channel is None and after.channel is not None:
        if after.channel.id == CANAL_ID:
            print(f"[DEBUG] {member.name} entrou no canal {after.channel.name}")
            guild = after.channel.guild
            voice = guild.voice_client
            try:
                if voice and voice.is_connected():
                    print("[DEBUG] Chamando sequencia_deteccao()")
                    await sequencia_deteccao(voice)
            except Exception as e:
                print(f"[DEBUG] Erro na sequência: {e}")

            frase = random.choice(entradas)
            msg = f"[{hora}] {frase} - USUÁRIO: {member.name}"
            print(f"[DEBUG] Enviando webhook: {msg}")
            await enviar_webhook(msg)

    # Saiu do canal fixo
    elif before.channel is not None and after.channel is None:
        if before.channel.id == CANAL_ID:
            print(f"[DEBUG] {member.name} saiu do canal {before.channel.name}")
            frase = random.choice(saidas)
            msg = f"[{hora}] {frase} - USUÁRIO: {member.name}"
            print(f"[DEBUG] Enviando webhook: {msg}")
            await enviar_webhook(msg)


# Comando manual de teste
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.lower().startswith("!testarvoz"):
        canal = bot.get_channel(CANAL_ID)
        if canal:
            voice = canal.guild.voice_client
            if voice and voice.is_connected():
                frase = "Este é um teste de voz."
                await gerar_audio(frase, "teste.mp3")
                await tocar_audio(voice, "teste.mp3")
                await message.channel.send("🎤 Teste de voz executado.")
            else:
                await message.channel.send("❌ Bot não está conectado ao canal de voz.")


bot.run(TOKEN)
