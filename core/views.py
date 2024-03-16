
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from core import services


@require_http_methods('GET')
def resolve_query(request):
    query: str = request.GET.get('q')

    if not query:
        return JsonResponse({'error': 'No query provided.'}, status=400)

    response = services.QueryResolver().resolve(query)

    return JsonResponse(response)
