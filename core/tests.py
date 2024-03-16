from unittest import mock
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

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

