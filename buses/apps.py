from django.apps import AppConfig


class BusesConfig(AppConfig):
    name = 'buses'
    
    def ready(self):
        import buses.signals