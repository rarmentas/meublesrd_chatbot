"""
Create sample Contacts and Requetes for the mockup.
Usage: python manage.py load_sample_tickets
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from tickets.models import Contact, Requete


class Command(BaseCommand):
    help = 'Create sample contacts and requêtes (tickets) for the mockup.'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Delete existing requêtes and contacts before creating.')

    def handle(self, *args, **options):
        if options['clear']:
            Requete.objects.all().delete()
            Contact.objects.all().delete()
            self.stdout.write('Cleared existing data.')

        contacts = [
            Contact(
                nom_complet='Alex Frechette',
                nom_du_compte='Alex Frechette',
                adresse_email='alexfrechette069@gmail.com',
                telephone='',
                telephone_mobile='(819) 588-7553',
            ),
            Contact(
                nom_complet='Marie Tremblay',
                nom_du_compte='Marie Tremblay',
                adresse_email='marie.t@example.com',
                telephone='(418) 555-1234',
                telephone_mobile='(418) 555-5678',
            ),
            Contact(
                nom_complet='Jean Dupont',
                nom_du_compte='Jean Dupont',
                adresse_email='jdupont@example.com',
                telephone='',
                telephone_mobile='(514) 555-9999',
            ),
        ]
        for c in contacts:
            c.save()
        self.stdout.write(f'Created {len(contacts)} contacts.')

        # Use first contact for main ticket
        contact1 = Contact.objects.get(nom_complet='Alex Frechette')
        contact2 = Contact.objects.get(nom_complet='Marie Tremblay')
        contact3 = Contact.objects.get(nom_complet='Jean Dupont')

        opened = timezone.now().replace(hour=12, minute=47, second=0, microsecond=0)

        requetes = [
            Requete(
                numero='00430578',
                contact=contact1,
                proprietaire='Rosalie Gouin',
                statut='nouveau',
                priorite='moyen',
                objet='Defective or damaged product - Case Number: 00430578',
                description='Le divan fait un bruit (toc) lorsque je veux élever le fauteuil.) aussi le divan ne veut pas rester stable lorsque les pieds sont élevés.',
                date_ouverture=opened,
                magasin='02 - Sherbrooke',
                classification='Produit défectueux ou endommagé',
                sous_sujet='Meubles',
                numero_contrat_achat='252228',
                type_produit='Meubles',
                manufacturier='Autre fabricant',
                code_produit='050534',
                origine_requete='Web',
                depuis_le_web=True,
                langue='Français',
                nombre_total_produits_defectueux=1,
                nombre_produits_defectueux_ouverts=1,
            ),
            Requete(
                numero='00430579',
                contact=contact2,
                proprietaire='Rosalie Gouin',
                statut='en_traitement',
                priorite='haut',
                objet='Livraison retardée - Commande 7892',
                description='La livraison prévue le 15 janvier na pas eu lieu.',
                date_ouverture=timezone.now().replace(day=1, hour=9, minute=0),
                magasin='01 - Québec',
                classification='Livraison',
                sous_sujet='Retard',
                statut='en_traitement',
            ),
            Requete(
                numero='00430580',
                contact=contact3,
                proprietaire='Pierre Martin',
                statut='nouveau',
                priorite='bas',
                objet='Demande dinformation sur la garantie',
                description='Quelle est la durée de garantie pour un canapé acheté en 2024?',
                date_ouverture=timezone.now().replace(hour=14, minute=0),
                classification='Information',
                sous_sujet='Garantie',
            ),
        ]
        for r in requetes:
            r.save()
        self.stdout.write(self.style.SUCCESS(f'Created {len(requetes)} requêtes. Open / or /fr/ or /en/ to see the list.'))
