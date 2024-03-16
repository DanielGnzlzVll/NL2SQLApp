import csv
import os
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from core.models import TeslaStockData

from django.db import transaction


class Command(BaseCommand):
    help = "Loads data from a csv file"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str)

    def _read_data(self, file_path) -> list[dict]:
        data = []
        with open(file_path, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(row)
        return data

    def _ensure_file_exists(self, file_path) -> None:
        if not os.path.exists(file_path):
            raise CommandError(f'File "{file_path}" does not exist.')

    def _save_data(self, data: list[dict]) -> None:
        stock_data = [TeslaStockData(**row) for row in data]
        with transaction.atomic():
            TeslaStockData.objects.all().delete()
            TeslaStockData.objects.bulk_create(stock_data)

    def handle(self, file_path, *args, **options):
        self._ensure_file_exists(file_path)
        data = self._read_data(file_path)
        self._save_data(data)
        self.stdout.write(self.style.SUCCESS("Data loaded successfully."))
