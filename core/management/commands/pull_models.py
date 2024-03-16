import ollama
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Pull ollama models"

    def handle(self, *args, **options):
        client = ollama.Client(host=settings.MODEL_SERVER_ENDPOINT)

        for model_name in settings.AVAILABLE_MODELS:
            self.stdout.write(f"Pulling {model_name} model.")
            client.pull(model_name)
