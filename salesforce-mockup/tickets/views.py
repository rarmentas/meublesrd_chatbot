from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Requete


def ticket_list(request):
    """Liste des requêtes (tableau)."""
    tickets = Requete.objects.all()[:50]
    return render(request, 'tickets/list.html', {'tickets': tickets})


def ticket_detail(request, numero):
    """Détail d'une requête (mockup complet)."""
    ticket = get_object_or_404(Requete, numero=numero)
    return render(request, 'tickets/detail.html', {'ticket': ticket})
