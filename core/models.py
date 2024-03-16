from django.db import models


class TeslaStockData(models.Model):
    date = models.DateField()
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.BigIntegerField()
    rsi_7 = models.FloatField()
    rsi_14 = models.FloatField()
    cci_7 = models.FloatField()
    cci_14 = models.FloatField()
    sma_50 = models.FloatField()
    ema_50 = models.FloatField()
    sma_100 = models.FloatField()
    ema_100 = models.FloatField()
    macd = models.FloatField()
    bollinger = models.FloatField()
    TrueRange = models.FloatField()
    atr_7 = models.FloatField()
    atr_14 = models.FloatField()
    next_day_close = models.FloatField()

    def __str__(self):
        return f"{self.date} - {self.close}"
