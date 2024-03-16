
from django.db import connection, transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


def get_sql_for_query(query):
    sql = """
    SELECT date, close
    FROM core_teslastockdata
    ORDER BY date ASC
    LIMIT 1
    """
    return sql


class CodeExecuted(Exception):
    pass


def execute_sql(sql):
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(sql)
                columns = [col[0] for col in cursor.description]
                data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            raise CodeExecuted()  # Raising an exception - abort the savepoint
    except CodeExecuted:
        return data


@require_http_methods('GET')
def resolve_query(request):
    query: str = request.GET.get('q')

    if not query:
        return JsonResponse({'error': 'No query provided.'}, status=400)

    sql = get_sql_for_query(query)
    response = execute_sql(sql)

    return JsonResponse({'response': response})
