import os
import sys
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Run the WebSocket server using Daphne'

    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            default='0.0.0.0',
            help='The host to bind to',
        )
        parser.add_argument(
            '--port',
            type=int,
            default=8001,
            help='The port to bind to',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting WebSocket server...'))
        
        # This ensures Django is fully initialized
        from channels.routing import get_default_application
        
        try:
            # Trying to use daphne installed in the virtual environment
            from daphne.cli import CommandLineInterface
            
            # Use the same port that's in settings
            port = getattr(settings, 'WEBSOCKET_PORT', options['port'])
            
            # Create the daphne command line arguments
            daphne_args = [
                "-b", options['host'],
                "-p", str(port),
                "cabby.asgi:application"
            ]
            
            self.stdout.write(self.style.SUCCESS(
                f'Running Daphne WebSocket server on {options["host"]}:{port}'
            ))
            
            # Run Daphne with the proper arguments
            sys.argv = ["daphne"] + daphne_args
            CommandLineInterface().run(daphne_args)
            
        except ImportError:
            self.stdout.write(self.style.ERROR(
                'Daphne not installed. Please install it using "pip install daphne"'
            ))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error running WebSocket server: {e}'))
            return
