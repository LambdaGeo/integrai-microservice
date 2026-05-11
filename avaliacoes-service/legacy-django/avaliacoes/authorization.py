"""Authorization helpers that delegate gestante access to gestantes-service."""
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings


def authorized_gestante_ids(access_token, count=200):
    if not access_token:
        return []

    query = urlencode({"_count": count})
    request = Request(
        f"{settings.GESTANTES_SERVICE_URL.rstrip('/')}/fhir/Patient?{query}",
        method="GET",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        with urlopen(request, timeout=10) as response:
            bundle = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return []

    ids = []
    for entry in bundle.get("entry", []) or []:
        resource_id = (entry.get("resource") or {}).get("id")
        try:
            ids.append(int(resource_id))
        except (TypeError, ValueError):
            continue
    return ids


def can_access_gestante(gestante_id, access_token):
    try:
        gestante_id = int(gestante_id)
    except (TypeError, ValueError):
        return False
    return gestante_id in authorized_gestante_ids(access_token)
