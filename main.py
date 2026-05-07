import discord
import asyncio
import random
import edge_tts
import os
from discord.ext import commands
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()
TOKEN = os.getenv("TOKEN")

if TOKEN is None:
    raise ValueError("TOKEN não encontrado no .env. Verifique se está escrito corretamente.")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Lista de frases
frases_voz = [
    "Você não deveria estar aqui.",
    "Eu posso te ver.",
    "Bora brincar?",
    "Eu amo brincar.",
    "Vamos começar arrancando suas cabeças e depois comendo as suas tripas.",
    "Ora, ora, carne nova.",
    "Não tenha medo. Eu não mordo. Eu mato.",
    "Olha, novos brinquedos! Vocês não deveriam estar aqui. Mas estão, perfeito!",
    "Eu estava tão sozinho, agora eu tenho novos amigos, novas diversões, coisas boas.",
    "Cada grito de vocês é música para mim.",
    "Vocês são tão divertidos, principalmente quando têm medo.",
    "Vocês são meus novos amigos ou minhas novas vítimas.",
    "Vocês são tão frágeis e eu tão faminto.",
    "Vocês acham que estão seguros? Não estão.",
    "Como vocês estão, minhas vítimas... quero dizer, amigos."
]

# Função para falar uma frase aleatória
async def falar_frase(vc):
    frase = random.choice(frases_voz)
    arquivo = "voz.mp3"
    tts = edge_tts.Communicate(frase, voice="pt-BR-AntonioNeural")
    await tts.save(arquivo)
    source = discord.FFmpegPCMAudio(arquivo)
    vc.play(source)

# Comando para entrar na call do usuário
@bot.command()
async def entrar(ctx):
    if ctx.author.voice:
        canal = ctx.author.voice.channel
        try:
            vc = await canal.connect()
            await falar_frase(vc)
        except Exception as e:
            await ctx.send(f"Falha ao conectar: {e}")
            if "522" in str(e):
                await ctx.send("Erro 522 detectado, tentando reconectar em 10 segundos...")
                await asyncio.sleep(10)
                try:
                    vc = await canal.connect()
                    await falar_frase(vc)
                except Exception as e2:
                    await ctx.send(f"Reconexão falhou: {e2}")
    else:
        await ctx.send("Você não está em um canal de voz.")

# Comando para testar fala (entra e fala aleatória)
@bot.command()
async def testarfala(ctx):
    if ctx.author.voice:
        canal = ctx.author.voice.channel
        try:
            vc = await canal.connect()
            await falar_frase(vc)
        except Exception as e:
            await ctx.send(f"Falha ao conectar: {e}")
            if "522" in str(e):
                await ctx.send("Erro 522 detectado, tentando reconectar em 10 segundos...")
                await asyncio.sleep(10)
                try:
                    vc = await canal.connect()
                    await falar_frase(vc)
                except Exception as e2:
                    await ctx.send(f"Reconexão falhou: {e2}")
    else:
        await ctx.send("Você não está em um canal de voz.")

# Comando para falar sem reconectar (se já estiver na call)
@bot.command()
async def fala(ctx):
    if ctx.voice_client:
        await falar_frase(ctx.voice_client)
    else:
        await ctx.send("O bot não está conectado a nenhum canal de voz. Use !entrar ou !testarfala primeiro.")

@bot.event
async def on_ready():
    print(f"Bot online como {bot.user}")

bot.run(TOKEN)
