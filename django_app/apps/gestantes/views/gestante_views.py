# ======================================
# Importações principais do Django
# ======================================
from datetime import date

from django.shortcuts import render, redirect
from django.contrib import messages

# ======================================
# Importações de apps locais
# ======================================
from apps.gestantes.forms import GestanteForms
from apps.usuarios.decorator import login_required_message

# ======================================
# Importações de microserviços
# ======================================
from microservices.clients import gestantes_client

EXT_PESO = "https://integrai.ufma.br/fhir/StructureDefinition/gestante-peso-pre"
EXT_ALTURA = "https://integrai.ufma.br/fhir/StructureDefinition/gestante-altura"
EXT_VULNERABILIDADE = "https://integrai.ufma.br/fhir/StructureDefinition/gestante-vulnerabilidade-social"
EXT_USUARIO_ID = "https://integrai.ufma.br/fhir/StructureDefinition/gestante-usuario-id"


def _fhir_extension(patient, url, value_key):
    for extension in patient.get("extension", []) or []:
        if extension.get("url") == url:
            return extension.get(value_key)
    return None


def _calcular_idade(data_nascimento):
    if not data_nascimento:
        return None
    if isinstance(data_nascimento, str):
        data_nascimento = date.fromisoformat(data_nascimento)
    hoje = date.today()
    return hoje.year - data_nascimento.year - (
        (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day)
    )


def _classificar_imc(imc):
    if imc is None:
        return "Altura ou peso invalidos"
    if imc < 18.5:
        return "Baixo peso"
    if imc <= 24.9:
        return "Adequado"
    return "Excesso de peso"


def _consentimento_ativo(gestante_id):
    consentimentos = gestantes_client.list_consentimentos(params={"gestante_id": gestante_id, "limit": 1})
    if not consentimentos:
        return True
    return consentimentos[0].get("status") == "aceito"


def _patient_to_gestante(patient):
    nome = ""
    names = patient.get("name") or []
    if names:
        nome = names[0].get("text") or " ".join(names[0].get("given") or [])
        if names[0].get("family") and names[0].get("family") not in nome:
            nome = f"{nome} {names[0].get('family')}".strip()

    telefone = None
    for item in patient.get("telecom", []) or []:
        if item.get("system") == "phone":
            telefone = item.get("value")
            break

    peso = _fhir_extension(patient, EXT_PESO, "valueInteger")
    altura = _fhir_extension(patient, EXT_ALTURA, "valueDecimal")
    vulnerabilidade_social = _fhir_extension(patient, EXT_VULNERABILIDADE, "valueBoolean")
    usuario_id = _fhir_extension(patient, EXT_USUARIO_ID, "valueInteger")
    data_nascimento = patient.get("birthDate")

    imc = round(float(peso) / (float(altura) ** 2), 2) if peso and altura else None
    gestante_id = int(patient["id"])

    return {
        "id": gestante_id,
        "nome": nome,
        "data_nascimento": data_nascimento,
        "peso": peso,
        "altura": altura,
        "telefone": telefone,
        "vulnerabilidade_social": bool(vulnerabilidade_social),
        "usuario_id": usuario_id,
        "foto": None,
        "idade": _calcular_idade(data_nascimento),
        "imc": imc,
        "imc_classificacao": _classificar_imc(imc),
        "telefone_whatsapp": telefone,
        "consentimento_ativo": _consentimento_ativo(gestante_id),
    }


def _gestante_form_to_fhir_patient(cleaned_data, usuario_id=None):
    extensions = [
        {"url": EXT_PESO, "valueInteger": cleaned_data["peso"]},
        {"url": EXT_ALTURA, "valueDecimal": cleaned_data["altura"]},
        {"url": EXT_VULNERABILIDADE, "valueBoolean": cleaned_data.get("vulnerabilidade_social", False)},
    ]
    if usuario_id is not None:
        extensions.append({"url": EXT_USUARIO_ID, "valueInteger": usuario_id})

    patient = {
        "resourceType": "Patient",
        "active": True,
        "gender": "female",
        "name": [{"use": "official", "text": cleaned_data["nome"]}],
        "birthDate": cleaned_data["data_nascimento"].isoformat(),
        "extension": extensions,
    }
    if cleaned_data.get("telefone"):
        patient["telecom"] = [{"system": "phone", "value": cleaned_data["telefone"], "use": "mobile"}]
    return patient


def _list_gestantes_fhir(usuario_id, nome=None):
    params = {"_count": 200}
    if nome:
        params["name"] = nome

    bundle = gestantes_client._request("GET", "/fhir/Patient", params=params)
    entries = (bundle or {}).get("entry", [])
    gestantes = [_patient_to_gestante(entry["resource"]) for entry in entries if entry.get("resource")]
    return [gestante for gestante in gestantes if gestante.get("usuario_id") == usuario_id]


def _get_gestante_fhir(gestante_id):
    patient = gestantes_client._request("GET", f"/fhir/Patient/{gestante_id}")
    if not patient or patient.get("resourceType") == "OperationOutcome":
        return None
    return _patient_to_gestante(patient)


def _create_gestante_fhir(cleaned_data, usuario_id):
    patient = _gestante_form_to_fhir_patient(cleaned_data, usuario_id=usuario_id)
    created = gestantes_client._request("POST", "/fhir/Patient", data=patient)
    if not created or created.get("resourceType") == "OperationOutcome":
        return None
    return _patient_to_gestante(created)


def _update_gestante_fhir(gestante_id, cleaned_data, usuario_id):
    patient = _gestante_form_to_fhir_patient(cleaned_data, usuario_id=usuario_id)
    updated = gestantes_client._request("PUT", f"/fhir/Patient/{gestante_id}", data=patient)
    if not updated or updated.get("resourceType") == "OperationOutcome":
        return None
    return _patient_to_gestante(updated)


def _delete_gestante_fhir(gestante_id):
    response = gestantes_client.session.delete(f"{gestantes_client.base_url}/fhir/Patient/{gestante_id}")
    return response.status_code == 204

# =========================================================
# Função: Revogar Consentimento
# Cria um registro de consentimento com status "revogado"
# =========================================================
@login_required_message
def revogar_consentimento(request, gestante_id):
    # Verificar se gestante existe via FHIR Patient
    gestante = _get_gestante_fhir(gestante_id)
    if not gestante:
        messages.error(request, "Gestante não encontrada.")
        return redirect('index')

    if request.method == 'POST':
        # Criar consentimento revogado via microserviço
        consentimento_data = {
            'gestante_id': gestante_id,
            'usuario_id': request.user.id,
            'status': 'revogado'
        }
        gestantes_client.create_consentimento(consentimento_data)
    return redirect('index')  # Redireciona para a página principal


# =========================================================
# Função: Index
# Lista gestantes do usuário logado e mostra cards
# =========================================================
def index(request):
    if not request.user.is_authenticated:
        return redirect('home')

    show_welcome = request.session.pop('show_welcome', False)
    # Usar FHIR Patient para listar gestantes
    gestantes = _list_gestantes_fhir(request.user.id)
    # Nao filtrar por consentimento ativo - mostrar todas as gestantes com status correto

    return render(request, 'gestantes/crud/painel.html', {
        "cards": gestantes,
        "show_welcome": show_welcome,
    })

# =========================================================
# Função: Buscar Gestantes
# Filtra gestantes pelo nome
# =========================================================
@login_required_message
def buscar(request):
    # Usar FHIR Patient para listar gestantes
    gestantes = _list_gestantes_fhir(request.user.id, nome=request.GET.get('buscar') or None)

    return render(request, 'gestantes/crud/painel.html', {"cards": gestantes})


# =========================================================
# Função: Nova Gestante
# Cria gestante e registra consentimento inicial
# =========================================================
@login_required_message
def nova_gestante(request):
    form = GestanteForms()

    if request.method == 'POST':
        form = GestanteForms(request.POST, request.FILES)
        consentimento_aceito = request.POST.get('consentimento_aceito') == 'true'

        if not consentimento_aceito:
            messages.error(request, 'Você precisa aceitar o consentimento para registrar a gestante.')
            # Retorna o form para não perder dados digitados
            return render(request, 'gestantes/crud/acolher.html', {'form': form, 'consentimento_erro': True})

        if form.is_valid():
            gestante = _create_gestante_fhir(form.cleaned_data, request.user.id)
            if gestante:
                # Criar consentimento via microserviço
                consentimento_data = {
                    'gestante_id': gestante['id'],
                    'usuario_id': request.user.id,
                    'status': 'aceito'
                }
                gestantes_client.create_consentimento(consentimento_data)

                messages.success(request, 'Nova gestante cadastrada!')
                return redirect('index')
            else:
                messages.error(request, 'Erro ao cadastrar gestante.')

    return render(request, 'gestantes/crud/acolher.html', {'form': form})


# =========================================================
# Função: Editar Gestante
# Permite atualização de dados com consentimento ativo
# =========================================================
@login_required_message
def editar_gestante(request, gestante_id):
    # Usar FHIR Patient para buscar gestante
    gestante = _get_gestante_fhir(gestante_id)
    if not gestante:
        messages.error(request, "Gestante não encontrada.")
        return redirect('index')

    if not gestante.get('consentimento_ativo', True):
        messages.error(request, "Não é possível editar uma gestante com consentimento revogado.")
        return redirect('index')

    form = GestanteForms(initial=gestante)

    if request.method == 'POST':
        form = GestanteForms(request.POST, request.FILES)
        if form.is_valid():
            updated = _update_gestante_fhir(gestante_id, form.cleaned_data, request.user.id)
            if updated:
                messages.success(request, 'Gestante editada com sucesso')
                return redirect('index')
            else:
                messages.error(request, 'Erro ao editar gestante.')

    # MUDANÇA AQUI: Passe o objeto 'gestante' completo para o template
    context = {
        'form': form,
        'gestante_id': gestante_id, # Pode manter, mas 'gestante' é melhor
        'gestante': gestante       # <-- ADICIONE ISSO
    }
    # DE: return render(request, 'gestantes/editar.html', {'form': form, 'gestante_id': gestante_id})
    return render(request, 'gestantes/crud/editar.html', context) # Use o novo caminho do template

# =========================================================
# Função: Deletar Gestante
# Remove registro de gestante
# =========================================================
@login_required_message
def deletar_gestante(request, gestante_id):
    # Usar FHIR Patient para deletar
    deleted = _delete_gestante_fhir(gestante_id)
    if deleted:
        messages.success(request, 'Deleção feita com sucesso!')
    else:
        messages.error(request, 'Erro ao deletar gestante.')
    return redirect('index')
