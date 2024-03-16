from io import StringIO
from unittest import mock

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.urls import reverse
from model_bakery import baker

from core import services
from core.models import TeslaStockData


@pytest.fixture
def mock_csv_file():
    csv_data = """date,open,high,low,close,volume,rsi_7,rsi_14,cci_7,cci_14,sma_50,ema_50,sma_100,ema_100,macd,bollinger,TrueRange,atr_7,atr_14,next_day_close
2014-01-02,9.986667,10.165333,9.77,10.006667,92826000,55.34407089342224,54.440117846652825,-37.373644058492644,15.213422424213173,9.68210666,9.820166824312885,10.49423998,9.67428441991791,0.16947161056263305,9.74079995,0.3953330000000008,0.4026411651229593,0.4475496484415416,9.970667
2014-01-03,10.0,10.146,9.906667,9.970667,70425000,53.74262870999453,53.82152101490924,-81.30447088739595,17.48112987448799,9.6528,9.826069020017528,10.49569332,9.68019010852561,0.1626230229475354,9.776166649999999,0.23933300000000024,0.37931142724825084,0.4326770305962963,9.8"""
    mock_open = mock.mock_open(read_data=csv_data)
    with mock.patch("core.management.commands.load_data.open", mock_open) as m:
        yield m


class TestLoadData:

    @mock.patch("core.management.commands.load_data.os.path.exists")
    def test_file_does_not_exist(self, mock_path_exists):
        out = StringIO()
        mock_path_exists.return_value = False
        with pytest.raises(CommandError) as exc_info:
            call_command("load_data", "test.csv", stdout=out)

        assert 'File "test.csv" does not exist.' in str(exc_info.value)

    @pytest.mark.django_db
    @mock.patch("core.management.commands.load_data.os.path.exists")
    def test_read_data(self, mock_path_exists, mock_csv_file):
        out = StringIO()
        call_command("load_data", "test.csv", stdout=out)
        assert "Data loaded successfully." in out.getvalue()

        assert (
            TeslaStockData.objects.filter(date__in=["2014-01-02", "2014-01-03"]).count()
            == 2
        )

    @pytest.mark.django_db
    @mock.patch("core.management.commands.load_data.os.path.exists")
    def test_overwrite_data(self, mock_path_exists, mock_csv_file):
        call_command("load_data", "test.csv")
        # ensure data is different to what is in the csv.
        TeslaStockData.objects.all().update(open=0)
        old_stock_data = dict(TeslaStockData.objects.all().values_list("date", "open"))

        call_command("load_data", "test.csv")
        new_stock_data = dict(TeslaStockData.objects.all().values_list("date", "open"))

        assert old_stock_data != new_stock_data


class TestResolveQueryView:

    def test_params_no_provided(self, client):
        response = client.get(reverse("resolve_query"))

        assert response.status_code == 400
        assert response.json() == {"error": "No query provided."}

    def test_url(self):
        url = reverse("resolve_query")
        assert url == "/api/v1/resolve_query/"

    @pytest.mark.django_db
    def test_happy_path(self, client):
        baker.make("core.TeslaStockData", _quantity=3)

        oldest_data = TeslaStockData.objects.order_by("-date").first()
        expected_response = {
            "response": [{"date": str(oldest_data.date), "close": oldest_data.close}]
        }

        response = client.get(
            reverse("resolve_query"),
            {"q": "Please give only the date and close price of the record with the oldest date."},
        )

        assert response.status_code == 200
        assert response.json() == expected_response

    @mock.patch("core.services.QueryResolver")
    def test_query_resolver_is_used(self, mock_query_resolver, client):

        mock_query_resolver.return_value.resolve.return_value = {"random": "data"}

        response = client.get(
            reverse("resolve_query"),
            {"q": "Please give me the oldest data, include date and close fields."},
        )

        assert response.json() == mock_query_resolver.return_value.resolve.return_value


class TestDjangoQueryExecutor:

    @pytest.mark.django_db
    def test_execute(self):
        baker.make("core.TeslaStockData", _quantity=3)
        sql = "SELECT count(*) as my_count FROM core_teslastockdata"

        response = services.DjangoQueryExecutor().execute(sql)

        assert response == [{"my_count": 3}]

    @pytest.mark.xfail(
        reason="Django transactions do not work currently with raw queries."
    )
    @pytest.mark.django_db
    def test_transaction(self):
        baker.make("core.TeslaStockData", _quantity=3)
        sql = "DELETE FROM core_teslastockdata"

        response = services.DjangoQueryExecutor().execute(sql)

        assert response == []

        assert TeslaStockData.objects.count() == 3


class TestQueryResolver:

    @pytest.mark.parametrize(
        "sql_generator, query_executor, expected_sql_generator, expected_query_executor",
        [
            (
                None,
                None,
                services.OllamaSqlGenerator,
                services.DjangoQueryExecutor,
            ),
            (
                mock.Mock(spec=services.AbstractSqlGenerator),
                mock.Mock(spec=services.AbstractQueryExecutor),
                mock.Mock,
                mock.Mock,
            ),
        ],
    )
    def test_init(
        self,
        sql_generator,
        query_executor,
        expected_sql_generator,
        expected_query_executor,
    ):

        resolver = services.QueryResolver(
            sql_generator=sql_generator,
            query_executor=query_executor,
        )

        assert isinstance(resolver.sql_generator, expected_sql_generator)
        assert isinstance(resolver.query_executor, expected_query_executor)

    def test_resolve(self):
        mock_query = mock.Mock()
        mock_sql_generator = mock.Mock(spec=services.AbstractSqlGenerator)
        mock_query_executor = mock.Mock(spec=services.AbstractQueryExecutor)

        resolver = services.QueryResolver(
            sql_generator=mock_sql_generator,
            query_executor=mock_query_executor,
        )
        response = resolver.resolve(mock_query)

        assert response == {"response": mock_query_executor.execute.return_value}

        assert mock_sql_generator.generate_sql.call_once_with(mock_query)
        assert mock_query_executor.execute.call_once_with(
            mock_sql_generator.generate_sql.return_value
        )

    def test_resolve_with_error(self):
        mock_query = mock.Mock()
        mock_sql_generator = mock.Mock(spec=services.AbstractSqlGenerator)
        mock_query_executor = mock.Mock(spec=services.AbstractQueryExecutor)
        mock_query_executor.execute.side_effect = Exception("Test error")

        resolver = services.QueryResolver(
            sql_generator=mock_sql_generator,
            query_executor=mock_query_executor,
        )
        response = resolver.resolve(mock_query)

        assert response == {
            "error": "Test error",
            "attempted_query": mock_sql_generator.generate_sql.return_value,
        }


class TestOllamaSqlGenerator:

    @pytest.mark.parametrize(
        "query, expected_response",
        [
            (
                "give the maximum close price",
                ' SELECT MAX("core_teslastockdata".close)',
            ),
            (
                "give the minimum close price",
                " SELECT MIN(close) FROM core_teslastockdata;",
            ),
            (
                "I want the most recent date in the format YYYY-MM-DD",
                ' SELECT DATEADD(DAY, 0, "core_teslastockdata".date) AS most_recent_date;',
            ),
        ],
    )
    def test_happy(self, query, expected_response):

        generator = services.OllamaSqlGenerator()
        sql = generator.generate_sql(query)
        assert sql == expected_response

    @mock.patch("core.services.ollama.Client")
    def test_chat_args(self, mock_client):

        generator = services.OllamaSqlGenerator()
        response = generator._chat("test")

        mock_client.return_value.chat.assert_called_with(
            model="llama2",
            options={"seed": 123, "temperature": 0},
            messages=[
                {
                    "role": "user",
                    "content": "test",
                },
            ],
        )

        assert (
            response == mock_client.return_value.chat.return_value["message"]["content"]
        )

    @mock.patch("core.services.TABLE_SCHEMA")
    def test_get_message(self, mock_table_schema):
        mock_query = mock.Mock()
        generator = services.OllamaSqlGenerator()
        message = generator._get_message(mock_query)

        assert str(mock_table_schema) in message
        assert str(mock_query) in message