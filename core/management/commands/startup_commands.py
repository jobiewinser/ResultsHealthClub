from django.core.management.base import BaseCommand
random_name = []
class Command(BaseCommand):
    def handle(self, *args, **options):
        from core.startup import run_debug_startup, run_demo_startup, run_startup
        run_startup()
        run_debug_startup()
        run_demo_startup()