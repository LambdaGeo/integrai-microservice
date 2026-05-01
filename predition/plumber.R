library(plumber)
library(jsonlite)

# Carrega a lógica de predição e modelos
source("predict_logic.R")

#* @apiTitle API de Risco Gestacional
#* @apiDescription API que calcula riscos gestacionais com base em dados de avaliação.
#* @tag Risco Gestacional

#* Calcula os riscos e os principais fatores contribuintes.
#* @post /predict
#* @serializer json list(auto_unbox = TRUE, na = "null") 
#* @param body:object The JSON object containing gestational data
#* @response 200 A successful response with the risk predictions and top factors
function(req, res){

  # Verifica se o corpo da requisição existe
  if (is.null(req$postBody) || req$postBody == "") {
    res$status <- 400
    return(list(error = "Request body is empty or not valid JSON."))
  }

  # Converte JSON para lista
  input_params <- tryCatch({
    fromJSON(req$postBody)
  }, error = function(e) {
    res$status <- 400
    return(list(error = "Invalid JSON format."))
  })

  # Se deu erro no fromJSON, retorna
  if (is.list(input_params) && "error" %in% names(input_params)) {
    return(input_params)
  }

  # Converte para data.frame (1 linha)
  input_data <- as.data.frame(input_params, stringsAsFactors = FALSE)

  # Gera predições
  predictions <- generate_risk_predictions(input_data)

  return(predictions)
}

# plumber.R
#* Health check endpoint
#* @get /health
function() {
  list(status = jsonlite::unbox("ok"))
}