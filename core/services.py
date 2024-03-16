import abc
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
