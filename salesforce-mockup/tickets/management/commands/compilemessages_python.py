"""
Compila archivos .po a .mo usando Babel (Python puro).
Usar este comando si compilemessages falla por no tener gettext/msgfmt instalado (p. ej. en Windows).

Uso: python manage.py compilemessages_python
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Compila traducciones .po → .mo con Babel (no requiere gettext/msgfmt).'

    def handle(self, *args, **options):
        try:
            from babel.messages.pofile import read_po
            from babel.messages.mofile import write_mo
        except ImportError:
            self.stderr.write(
                self.style.ERROR('Instala Babel: pip install Babel')
            )
            return

        locale_dirs = getattr(settings, 'LOCALE_PATHS', None) or []
        if not locale_dirs:
            self.stdout.write(self.style.WARNING('No hay LOCALE_PATHS en settings.'))
            return

        compiled = 0
        for locale_dir in locale_dirs:
            base = Path(locale_dir)
            if not base.exists():
                continue
            for po_path in base.rglob('LC_MESSAGES/*.po'):
                mo_path = po_path.with_suffix('.mo')
                locale = po_path.parent.parent.name
                with open(po_path, 'r', encoding='utf-8') as f:
                    catalog = read_po(f, locale=locale)
                with open(mo_path, 'wb') as f:
                    write_mo(f, catalog)
                self.stdout.write(f'Compilado: {po_path} → {mo_path}')
                compiled += 1

        if compiled:
            self.stdout.write(self.style.SUCCESS(f'Listo: {compiled} archivo(s) compilado(s).'))
        else:
            self.stdout.write(self.style.WARNING('No se encontraron archivos .po en LOCALE_PATHS.'))
