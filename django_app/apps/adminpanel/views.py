from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.usuarios.services import clear_microservice_session, is_token_expired
from microservices.clients import avaliacoes_client, gestantes_client, users_client


def staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "Acesso restrito a administradores.")
            return redirect("index")

        token = request.session.get("microservice_token") or getattr(request.user, "token", None)
        if is_token_expired(token):
            clear_microservice_session(request)
            messages.error(request, "Sessão expirada. Faça login novamente.")
            return redirect("login")

        return view_func(request, *args, **kwargs)

    return wrapper


def service_status(label, health_data):
    return {
        "label": label,
        "online": bool(health_data),
        "detail": "Online" if health_data else "Indisponível",
    }


def safe_call(callback, fallback):
    try:
        return callback()
    except Exception as exc:
        print(f"Erro no painel administrativo: {exc}")
        return fallback


def current_user_id(request):
    return getattr(request.user, "id", None)


def redirect_dashboard():
    return redirect("custom_admin:index")


def usuario_action_applied(action, updated_user):
    expected_values = {
        "activate": {"is_active": True},
        "deactivate": {"is_active": False},
        "make_staff": {"is_staff": True},
        "remove_staff": {"is_staff": False},
        "make_superuser": {"is_superuser": True, "is_staff": True},
        "remove_superuser": {"is_superuser": False},
    }
    expected = expected_values.get(action, {})
    return all(updated_user.get(field) is value for field, value in expected.items())


@staff_required
def dashboard(request):
    users = safe_call(lambda: users_client.list_usuarios({"limit": 200}), [])
    gestantes = safe_call(lambda: gestantes_client.list_gestantes({"limit": 200}), [])
    consentimentos = safe_call(lambda: gestantes_client.list_consentimentos({"limit": 200}), [])
    avaliacoes = safe_call(lambda: avaliacoes_client.list_avaliacoes({"_count": 200}), [])
    pilulas = safe_call(lambda: avaliacoes_client.list_pilulas(), [])
    audit_logs = safe_call(lambda: users_client.list_audit_logs({"limit": 50}), [])

    statuses = [
        service_status("Users", safe_call(users_client.health, None)),
        service_status("Gestantes", safe_call(gestantes_client.health, None)),
        service_status("Avaliações", safe_call(avaliacoes_client.health, None)),
    ]

    valid_avaliacoes = [item for item in avaliacoes if item]
    context = {
        "statuses": statuses,
        "counts": {
            "users": len(users),
            "gestantes": len(gestantes),
            "consentimentos": len(consentimentos),
            "avaliacoes": len(valid_avaliacoes),
            "pilulas": len(pilulas),
            "audit_logs": len(audit_logs),
        },
        "users": users,
        "gestantes": gestantes,
        "consentimentos": consentimentos[:50],
        "avaliacoes": valid_avaliacoes[:50],
        "pilulas": pilulas[:50],
        "audit_logs": audit_logs[:50],
    }
    return render(request, "adminpanel/dashboard.html", context)


@require_POST
@staff_required
def usuario_action(request, usuario_id, action):
    users = safe_call(lambda: users_client.list_usuarios({"limit": 200}), [])
    user = next((item for item in users if item.get("id") == usuario_id), None)
    if not user:
        messages.error(request, "Usuário não encontrado.")
        return redirect_dashboard()

    if usuario_id == current_user_id(request) and action in {"deactivate", "remove_staff", "remove_superuser"}:
        messages.error(request, "Você não pode remover o próprio acesso administrativo.")
        return redirect_dashboard()

    payload_by_action = {
        "activate": {"is_active": True},
        "deactivate": {"is_active": False},
        "make_staff": {"is_staff": True},
        "remove_staff": {"is_staff": False},
        "make_superuser": {"is_superuser": True, "is_staff": True},
        "remove_superuser": {"is_superuser": False},
    }
    payload = payload_by_action.get(action)
    if not payload:
        messages.error(request, "Ação de usuário inválida.")
        return redirect_dashboard()

    updated = users_client.update_usuario(usuario_id, payload)
    if updated and usuario_action_applied(action, updated):
        messages.success(request, "Usuário atualizado.")
    elif updated:
        messages.error(request, "A API respondeu, mas a permissão não foi alterada.")
    else:
        messages.error(request, users_client.last_error or "Não foi possível atualizar o usuário.")
    return redirect_dashboard()


@require_POST
@staff_required
def delete_gestante(request, gestante_id):
    gestantes_client.delete_gestante(gestante_id)
    if gestantes_client.last_error:
        messages.error(request, gestantes_client.last_error)
    else:
        messages.success(request, "Gestante removida.")
    return redirect_dashboard()


@require_POST
@staff_required
def set_consentimento(request, gestante_id, status):
    if status not in {"aceito", "revogado"}:
        messages.error(request, "Status de consentimento inválido.")
        return redirect_dashboard()

    payload = {
        "gestante_id": gestante_id,
        "usuario_id": current_user_id(request),
        "status": status,
    }
    if status == "revogado":
        payload["motivo_revogacao"] = request.POST.get("motivo_revogacao") or "Alterado pelo painel administrativo"

    created = gestantes_client.create_consentimento(payload)
    if created:
        messages.success(request, "Consentimento atualizado.")
    else:
        messages.error(request, gestantes_client.last_error or "Não foi possível atualizar o consentimento.")
    return redirect_dashboard()


@require_POST
@staff_required
def delete_avaliacao(request, avaliacao_id):
    avaliacoes_client.delete_avaliacao(avaliacao_id)
    if avaliacoes_client.last_error:
        messages.error(request, avaliacoes_client.last_error)
    else:
        messages.success(request, "Avaliação removida.")
    return redirect_dashboard()


@require_POST
@staff_required
def mark_pilula_sent(request, pilula_id):
    updated = avaliacoes_client.marcar_pilula_enviada(pilula_id)
    if updated:
        messages.success(request, "Pílula marcada como enviada.")
    else:
        messages.error(request, avaliacoes_client.last_error or "Não foi possível atualizar a pílula.")
    return redirect_dashboard()


@require_POST
@staff_required
def delete_pilula(request, pilula_id):
    avaliacoes_client.delete_pilula(pilula_id)
    if avaliacoes_client.last_error:
        messages.error(request, avaliacoes_client.last_error)
    else:
        messages.success(request, "Pílula removida.")
    return redirect_dashboard()
