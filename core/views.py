from django.conf import settings
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.views.decorators.http import require_http_methods

from core import services


@require_http_methods("GET")
def resolve_query(request):
    query: str = request.GET.get("q")
    model: str = request.GET.get("model")
    format: str = request.GET.get("format", "json")
    if not query:
        return JsonResponse({"error": "No query provided."}, status=400)

    response = services.QueryResolver(model=model).resolve(query)
    if format == "json":
        return JsonResponse(response)

    return TemplateResponse(request, "response.html", response)


@require_http_methods("GET")
def chat(request):
    return TemplateResponse(
        request, "chat.html", {"available_models": settings.AVAILABLE_MODELS}
    )
