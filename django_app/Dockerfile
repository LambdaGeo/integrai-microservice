# Dockerfile OTIMIZADO para Django (Desenvolvimento)
FROM python:3.10.12-slim

# 1. Variáveis de Ambiente (Boas Práticas)
# Evita a criação de arquivos .pyc e garante que os logs saiam direto
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 2. Configuração de Locale e Timezone (Mantido do seu)
ENV LANG=pt_BR.UTF-8 \
    LANGUAGE=pt_BR:pt \
    LC_ALL=pt_BR.UTF-8 \
    TZ=America/Sao_Paulo

# 3. Instalação de Dependências do Sistema (com limpeza)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libpq-dev \
       gcc \
       locales \
       postgresql-client \
    # Configura o locale
    && echo "pt_BR.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen pt_BR.UTF-8 \
    && update-locale LANG=pt_BR.UTF-8 \
    # Limpa o cache do apt para reduzir o tamanho da imagem
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 4. Define o diretório de trabalho
WORKDIR /app

# 5. Atualiza o pip
# É bom fazer isso em uma camada separada
RUN pip install --upgrade pip

# 6. Otimização de Cache (A MÁGICA ACONTECE AQUI)
# Copia APENAS o requirements.txt primeiro
COPY requirements.txt /app/requirements.txt

# Instala as dependências. Esta camada só será refeita
# se o requirements.txt mudar.
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copia o Resto do Projeto
# Agora sim, copiamos o código da aplicação.
# Se você mudar um .py, o Docker começa daqui,
# pulando o 'pip install' (que é lento).
COPY . /app/

# 8. Expõe a porta e Roda o Servidor
EXPOSE 8001

# Copia o entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Usa o entrypoint customizado
#ENTRYPOINT ["/app/entrypoint.sh"]

# Define o comando padrão (pode ser sobrescrito no docker-compose)
#CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]