import abc

import ollama
from django.conf import settings
from django.db import connection, transaction


TABLE_SCHEMA = """
--
-- Create model TeslaStockData
--
CREATE TABLE "core_teslastockdata" ("id" bigint NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY, "date" date NOT NULL, "open" double precision NOT NULL, "high" double precision NOT NULL, "low" double precision NOT NULL, "close" double precision NOT NULL, "volume" bigint NOT NULL, "rsi_7" double precision NOT NULL, "rsi_14" double precision NOT NULL, "cci_7" double precision NOT NULL, "cci_14" double precision NOT NULL, "sma_50" double precision NOT NULL, "ema_50" double precision NOT NULL, "sma_100" double precision NOT NULL, "ema_100" double precision NOT NULL, "macd" double precision NOT NULL, "bollinger" double precision NOT NULL, "TrueRange" double precision NOT NULL, "atr_7" double precision NOT NULL, "atr_14" double precision NOT NULL, "next_day_close" double precision NOT NULL);
"""


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


class OllamaSqlGenerator(AbstractSqlGenerator):

    def __init__(self) -> None:
        super().__init__()
        self.ollama = ollama.Client(host=settings.MODEL_SERVER_ENDPOINT)

    def _chat(self, message: str) -> str:
        response = self.ollama.chat(
            model="llama2",
            options={
                "seed": 123,
                "temperature": 0
            },
            messages=[
                {
                    "role": "user",
                    "content": message,
                },
            ],
        )
        return response["message"]["content"]

    def _get_message(self, query: str) -> str:
        return f"""Given the following SQL table,
            your job is to write queries given a user's request.

            {TABLE_SCHEMA}

            Write a SQL query that returns - {query}
            response only with the SQL query with no other text.
            """

    def generate_sql(self, query: str) -> str:
        message = self._get_message(query)
        sql = self._chat(message)
        return sql


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
