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


class QueryResolver:
    sql_generator: AbstractSqlGenerator
    query_executor: AbstractQueryExecutor

    def __init__(
        self,
        *,
        sql_generator: AbstractSqlGenerator | None = None,
        query_executor: AbstractQueryExecutor | None = None
    ) -> None:
        if sql_generator is None:
            self.sql_generator = DummySqlGenerator()
        else:
            self.sql_generator = sql_generator

        if query_executor is None:
            self.query_executor = DjangoQueryExecutor()
        else:
            self.query_executor = query_executor

    def resolve(self, query: str) -> dict:
        sql = self.sql_generator.generate_sql(query)
        try:
            query_response = self.query_executor.execute(sql)
            response = {"response": query_response}
        except Exception as e:
            response = {"error": str(e), "attempted_query": sql}
        return response
