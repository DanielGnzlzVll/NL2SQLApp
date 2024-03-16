import abc
from django.db import connection, transaction

class CodeExecuted(Exception):
    pass


class AbstractSqlGenerator(abc.ABC):
    @abc.abstractmethod
    def generate_sql(self, query: str) -> str:
        pass


class DummySqlGenerator(AbstractSqlGenerator):
    def generate_sql(self, query: str) -> str:
        return """
            SELECT date, close
            FROM core_teslastockdata
            ORDER BY date ASC
            LIMIT 1
        """


class AbstractQueryExecutor(abc.ABC):
    @abc.abstractmethod
    def execute(self, sql: str) -> list[dict]:
        pass


class DjangoQueryExecutor(AbstractQueryExecutor):
    def execute(self, sql: str) -> list[dict]:
        data = []
        with transaction.atomic():
            try:
                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    if cursor.description is not None:
                        columns = [col[0] for col in cursor.description]
                        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
                    raise CodeExecuted()
            except CodeExecuted:
                return data

