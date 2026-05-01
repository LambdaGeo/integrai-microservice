# Carregar as bibliotecas necessárias
library(caret)
library(fastshap)
library(shapviz)
#library(UBL)
library(dplyr)

# Limpar a memoria da sessao 
rm(list=ls())

# Carregar todos os modelos .rds
model_asma <- readRDS("modelo_asthma_c.rds")
model_obesidade <- readRDS("modelo_overweight_c.rds")
model_carie <- readRDS("modelo_Caries_Child.rds")
model_alergia <- readRDS("modelo_allergy.rds")
model_integralidade <- readRDS("modelo_all_outcome.rds")
x_all <- readRDS("x_all.rds")

dicionario <- data.frame(NOME_APP=c("corrimento_vaginal","periodontite_carie","hipertensao_gestacao",
                                    "diabetes_gestacao","estresse_gestacao","consumo_bebidas_adocadas",
                                    "historico_familiar_alergia","consumo_ultraprocessados","consumo_alcool",
                                    "fumante_gestacao","imc_pre_gestacional","idade_gestante")
                        )
row.names(dicionario) <- c("vagdischarge","periodontitis","hypertension_p",
              "diabetes_p","pssreduced","dailyssb_p",    
              "family_h","blockupf2","alcohol_p",
              "smoking_p","maternalage_p","maternalbmi_bp")

# 3. FUNÇÃO PRINCIPAL (continua a mesma, sem alterações)
generate_risk_predictions <- function(input_data) {
  
  # Seleciona as variaveis da calculadora, na ordem correta
  input_data <- input_data %>% select(dicionario$NOME_APP)
  
  # Renomeia as variveis da calculdora para os mesmos nomes das variaveis do modelo
  colnames(input_data) <- row.names(dicionario)
  print(input_data)
  
  mascara <- input_data
  mascara[c("maternalage_p","maternalbmi_bp")] <- TRUE

  # Para cada modelo, calcula a probabilidade do desfecho acontecer
  prob_asma <- predict(model_asma, newdata = input_data, type = "prob") * 100
  prob_obesidade <- predict(model_obesidade, newdata = input_data, type = "prob") * 100
  prob_carie <- predict(model_carie, newdata = input_data, type = "prob") * 100
  prob_alergia <- predict(model_alergia, newdata = input_data, type = "prob") * 100
  prob_integralidade <- predict(model_integralidade, newdata = input_data, type = "prob") * 100

  # Calcula o SHAP para extrair as top 5 fatores que mais impactaram o modelo de integralidade
  set.seed(123)
  p_function <- function(object, newdata)  caret::predict.train(object, newdata = newdata, type = "prob")[,"Sim"]
  shap_values <- fastshap::explain(model_integralidade, 
                                   X = x_all, 
                                   pred_wrapper = p_function, 
                                   nsim = 250,
                                   shap_only = F,
                                   newdata=as.data.frame(input_data))
  
  # Armazena os 5 top fatores
  top_fatores <- colnames(shap_values$shapley_values)[order(abs(shap_values$shapley_values),decreasing = T)][1:5]
  print(top_fatores)
  print(mascara)
  top_fatores <- top_fatores[which(mascara[top_fatores]==TRUE)]
  
  top_fatores <- dicionario[top_fatores,"NOME_APP"]
  # Cria a lista de retorno
  resposta <- list(
    prob_asma = as.numeric(prob_asma$Sim[1]),
    prob_obesidade = as.numeric(prob_obesidade$Sim[1]),
    prob_carie = as.numeric(prob_carie$Sim[1]),
    prob_alergia = as.numeric(prob_alergia$Sim[1]),
    prob_integralidade = as.numeric(prob_integralidade$Sim[1]),
    top_fatores = as.list(top_fatores)
  )

  return(resposta)
}
