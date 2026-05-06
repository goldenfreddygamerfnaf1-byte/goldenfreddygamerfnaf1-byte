# Usa imagem oficial do Python
FROM python:3.11-slim

# Define diretório de trabalho
WORKDIR /app

# Copia requirements e instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instala FFmpeg (necessário para tocar áudio no Discord)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Copia o código do bot
COPY . .

# Define comando padrão para rodar o bot
CMD ["python", "main.py"]
