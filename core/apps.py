from django.apps import AppConfig

from django.conf import settings
import ollama


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        client = ollama.Client(host=settings.MODEL_SERVER_ENDPOINT)
        for model in settings.DOWNLOAD_MODELS_ON_FLY:
            client.pull(model)