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

bot = discord.Client(intents=intents)

# >>> VOZ SOMBRIA CONFIGURADA <<<
VOICE = "pt-BR-FrancisNeural"  # voz masculina
RATE = "-20%"  # fala mais lenta e grave

CANAL_ID = 1501006139125534860

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

saidas = [
    "⛔ conexão encerrada",
    "sinal perdido",
    "█ transmissão interrompida █",
    "presença removida do sistema",
    "eco finalizado",
    "o silêncio voltou",
    "ERRO :: usuário desconectado",
]

frases_voz = [
    "Eu consigo te ver.",
    "Você não deveria estar aqui.",
    "Eu estava te esperando.",
    "Não olha pra trás.",
    "Tem algo errado com esse lugar.",
    "Eu estou sempre de olho.",
    "Você não consegue se esconder de mim.",
    "Ouviu isso?",
    "Eu sei que você está aí.",
    "Sinal encontrado.",
    "Conexão estabelecida.",
    "Você não está sozinho.",
    "Eu vou te encontrar.",
    "Erro. Presença detectada.",
    "Corre.",
    "Eles estão vindo.",
    "Esse lugar não é seguro.",
    "Quanto tempo você acha que tem?",
    "Já é tarde demais.",
    "Estou bem aqui do seu lado.",
]

erros_deteccao = [
    "ERRO. ERRO. ERRO. 0 x 9 8. FALHA NO SISTEMA. INTRUSO DETECTADO. CÓDIGO 4 1 3. ACESSO NEGADO. CORROMPIDO. "
    "SISTEMA FALHOU. 0 1 0 1 0 1. CONEXÃO INSTÁVEL. ALERTA. ALERTA. PRESENÇA IDENTIFICADA. ERRO CRÍTICO. "
    "REINICIANDO. FALHA. FALHA. FALHA. USUÁRIO INVÁLIDO. ANOMALIA DETECTADA. CÓDIGO VERMELHO.",
]

fila_frases = []


async def gerar_audio(texto, arquivo="voz.mp3"):
    communicate = edge_tts.Communicate(texto, VOICE, rate=RATE)
    await communicate.save(arquivo)


async def tocar_audio(voice, arquivo="voz.mp3"):
    if os.path.exists(arquivo) and voice.is_connected():
        # Adicionando eco e voz grave
        voice.play(discord.FFmpegPCMAudio(arquivo, options="-af aecho=0.8:0.9:1000:0.3,atempo=0.8"))
        while voice.is_playing():
            await asyncio.sleep(0.5)


async def sequencia_deteccao(voice):
    texto = random.choice(erros_deteccao)
    await gerar_audio(texto, "deteccao.mp3")
    await tocar_audio(voice, "deteccao.mp3")


async def loop_frases_aleatorias(guild):
    global fila_frases
    while True:
        await asyncio.sleep(random.randint(300, 900))
        try:
            voice = guild.voice_client
            if voice and voice.is_connected() and not voice.is_playing():
                humanos = [m for m in voice.channel.members if not m.bot]
                if humanos:
                    if not fila_frases:
                        fila_frases = frases_voz.copy()
                        random.shuffle(fila_frases)
                    frase = fila_frases.pop()
                    print(f"Falando frase aleatória: {frase}")
                    await gerar_audio(frase)
                    await tocar_audio(voice)
        except Exception as e:
            print(f"Erro no loop de frases: {e}")


async def enviar_webhook(msg):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"content": msg, "username": "SYSTEM_ERROR"}
            async with session.post(WEBHOOK, json=payload) as resp:
                print(f"Webhook enviado - status: {resp.status}")
    except Exception as e:
        print(f"Erro ao enviar webhook: {e}")


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
                    print(f"Conectado ao canal fixo: {canal.name}")
                except Exception as e:
                    print(f"Erro ao reconectar: {e}")
        await asyncio.sleep(30)


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
            guild = after.channel.guild
            voice = guild.voice_client
            print(f"[{hora}] {member.name} entrou no canal fixo")

            try:
                if voice and voice.is_connected():
                    await sequencia_deteccao(voice)
            except Exception as e:
                print(f"Erro na sequência: {e}")

            frase = random.choice(entradas)
            msg = f"```ansi\n[{hora}]\n{frase}\nUSUÁRIO: {member.name}\nCANAL: {after.channel.name}\n```"
            await enviar_webhook(msg)

    # Saiu do canal fixo
    elif before.channel is not None and after.channel is None:
        if before.channel.id == CANAL_ID:
            frase = random.choice(saidas)
            msg = f"```ansi\n[{hora}]\n{frase}\nUSUÁRIO: {member.name}\n```"
            await enviar_webhook(msg)


bot.run(TOKEN)
