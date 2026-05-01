# run_api.R
library(plumber)

# Carrega o arquivo da API Plumber
pr <- plumb("plumber.R")

# Roda a API na porta 8000, host 0.0.0.0
pr$run(host = "0.0.0.0", port = 8000)
