# Usa SUA imagem base com pacotes ML já compilados 🎯
FROM docker.io/profsergiocosta/r-ml-base:latest

WORKDIR /app

# Copia apenas os arquivos ESSENCIAIS para a API
# (evita copiar .RData, .Rhistory, etc. que estão no .dockerignore)
COPY run_api.R .
COPY plumber.R .
COPY predict_logic.R .
COPY modelo_*.rds ./
COPY x_all.rds ./

# (Opcional) Se precisar de algum pacote extra específico deste projeto:
# COPY install_packages_project.R .
# RUN Rscript -e "options(repos = c(CRAN = 'https://cloud.r-project.org')); source('install_packages_project.R')"

EXPOSE 8000

CMD ["Rscript", "run_api.R"]