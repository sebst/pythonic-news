from django.apps import AppConfig


class EmaildigestConfig(AppConfig):
    name = 'emaildigest'

    def ready(self):
        from . import receivers