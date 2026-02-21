"""
Create sample Requetes for the mockup.
Usage: python manage.py load_sample_tickets
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from tickets.models import Requete


class Command(BaseCommand):
    help = 'Create sample requêtes (tickets) for the mockup.'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Delete existing requêtes before creating.')

    def handle(self, *args, **options):
        if options['clear']:
            Requete.objects.all().delete()
            self.stdout.write('Cleared existing data.')

        opened = timezone.now().replace(hour=12, minute=47, second=0, microsecond=0)

        requetes = [
            Requete(
                numero='00430578',
                claim_type='Defective or damaged product',
                damage_type='Mechanical',
                delivery_date=timezone.now().date(),
                product_type='Furniture',
                manufacturer='Other Manufacturer',
                store_of_purchase='02 - Sherbrooke',
                product_code='050534',
                purchase_contract_number='252228',
                description='Le divan fait un bruit (toc) lorsque je veux élever le fauteuil.',
                claim_date=opened,
                has_attachments=True,
            ),
            Requete(
                numero='00430579',
                claim_type='Delivery',
                damage_type='',
                delivery_date=timezone.now().date(),
                product_type='Appliance',
                manufacturer='Samsung',
                store_of_purchase='01 - Québec',
                product_code='892341',
                purchase_contract_number='789200',
                description='La livraison prévue le 15 janvier n\'a pas eu lieu.',
                claim_date=timezone.now().replace(day=1, hour=9, minute=0),
                has_attachments=False,
            ),
            Requete(
                numero='00430580',
                claim_type='Information',
                damage_type='',
                delivery_date=None,
                product_type='Furniture',
                manufacturer='La-Z-Boy',
                store_of_purchase='03 - Montréal',
                product_code='445522',
                purchase_contract_number='',
                description='Quelle est la durée de garantie pour un canapé acheté en 2024?',
                claim_date=timezone.now().replace(hour=14, minute=0),
                has_attachments=False,
            ),
        ]
        for r in requetes:
            r.save()
        self.stdout.write(self.style.SUCCESS(
            f'Created {len(requetes)} requêtes. Open / or /fr/ or /en/ to see the list.'
        ))
