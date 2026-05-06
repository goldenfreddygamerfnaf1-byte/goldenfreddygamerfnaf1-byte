# Usa imagem oficial do Python
FROM python:3.11-slim

# Instala FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Define diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . .

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Comando para rodar o bot
CMD ["python", "main.py"]
