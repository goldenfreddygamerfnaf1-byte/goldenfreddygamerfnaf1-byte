import discord
import aiohttp
import asyncio
import random
import os
import edge_tts
from datetime import datetime

TOKEN = "MTUwMTAxMDA3MDI3NDcwMzQ5Mg.GG7-_q.KP_jGhNjhqrfBM96zhpvNIaMO1BgkM0CG87Yxs"
WEBHOOK = "https://discord.com/api/webhooks/1501007787923214497/u4kbGU7R5vYTK8qptkrcthS1KWLdd-SG3n3-q9uBp4-UrJsEcjfk-H1JdJPS_FJ2pCC1"
VOICE = "pt-BR-AntonioNeural"

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True

bot = discord.Client(intents=intents)

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
    "Eu posso te ver. Bora brincar?",
    "Eu amo brincar.",
    "Não tenha medo. Eu não mordo. Eu mato.",
    "Ora, ora, carne nova.",
    "Olha, novos brinquedos.",
    "Eu estava tão sozinho. Agora eu tenho novas diversões.",
    "Vamos começar do início, tá bom?",
    "Você veio até mim. Perfeito.",
    "Vamos começar arrancando sua cabeça e depois comer tuas tripas.",
    "Oi, meus amigos, como vocês estão? Tudo bem com vocês?",
    "E você, Bruno, como vai essa vida? É ótima?",
    "E a sua Golden, como está?",
    "Bruna, como você está, minha amiga? Vamos conversar um pouquinho, a sós?",
    "Golden, Golden, como você está, meu brother? Como vai a vida? Morta ou inexistente.",
    "Mas estão, perfeito! Eu estava tão sozinho, agora eu tenho novas diversões.",
]

erros_deteccao = [
    "ERRO. ERRO. ERRO. 0 x 9 8. FALHA NO SISTEMA. INTRUSO DETECTADO. CÓDIGO 4 1 3. ACESSO NEGADO. CORROMPIDO. "
    "SISTEMA FALHOU. 0 1 0 1 0 1. CONEXÃO INSTÁVEL. ALERTA. ALERTA. PRESENÇA IDENTIFICADA. ERRO CRÍTICO. "
    "REINICIANDO. FALHA. FALHA. FALHA. USUÁRIO INVÁLIDO. ANOMALIA DETECTADA. CÓDIGO VERMELHO.",
]

fila_frases = []
canal_fixo = {}
loop_ativo = {}

async def gerar_audio(texto, arquivo="voz.mp3"):
    communicate = edge_tts.Communicate(texto, VOICE, rate="+30%")
    await communicate.save(arquivo)

async def tocar_audio(voice, arquivo="voz.mp3"):
    if os.path.exists(arquivo) and voice.is_connected():
        voice.play(discord.FFmpegPCMAudio(arquivo))
        while voice.is_playing():
            await asyncio.sleep(0.5)

async def sequencia_deteccao(voice):
    texto = random.choice(erros_deteccao)
    await gerar_audio(texto, "deteccao.mp3")
    await tocar_audio(voice, "deteccao.mp3")

async def manter_no_canal(guild):
    while True:
        try:
            canal = canal_fixo.get(guild.id)
            if canal and (guild.voice_client is None or not guild.voice_client.is_connected()):
                print(f"Reconectando ao canal: {canal.name}")
                await canal.connect()
        except Exception as e:
            print(f"Erro ao reconectar: {e}")
        await asyncio.sleep(10)

async def loop_frases_aleatorias(guild):
    global fila_frases
    while True:
        await asyncio.sleep(random.randint(1200, 5400))
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

@bot.event
async def on_ready():
    print(f"Bot online como {bot.user}")
    for guild in bot.guilds:
        for vc in guild.voice_channels:
            try:
                voice = await vc.connect()
                canal_fixo[guild.id] = vc
                print(f"Conectado ao canal fixo: {vc.name}")
                break
            except Exception as e:
                print(f"Erro ao conectar: {e}")
        asyncio.create_task(manter_no_canal(guild))
        asyncio.create_task(loop_frases_aleatorias(guild))

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    hora = datetime.now().strftime("%H:%M:%S")

    if before.channel is None and after.channel is not None:
        guild = after.channel.guild
        voice = guild.voice_client

        if voice:
            try:
                if voice.channel != after.channel:
                    await voice.move_to(after.channel)
                canal_fixo[guild.id] = after.channel
            except Exception as e:
                print(f"Erro ao mover: {e}")

        try:
            if voice and voice.is_connected():
                await sequencia_deteccao(voice)
        except Exception as e:
            print(f"Erro na sequência: {e}")

        frase = random.choice(entradas)
        msg = f"```ansi\n[{hora}]\n{frase}\nUSUÁRIO: {member.name}\nCANAL: {after.channel.name}\n```"
        await enviar_webhook(msg)

    elif before.channel is not None and after.channel is None:
        hora_str = datetime.now().strftime("%H:%M:%S")
        frase = random.choice(saidas)
        msg = f"```ansi\n[{hora_str}]\n{frase}\nUSUÁRIO: {member.name}\n```"
        await enviar_webhook(msg)

bot.run(TOKEN)
