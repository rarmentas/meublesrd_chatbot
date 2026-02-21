from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import Requete


@login_required
def ticket_list(request):
    """Liste des requêtes (tableau)."""
    tickets = Requete.objects.all()[:50]
    return render(request, 'tickets/list.html', {'tickets': tickets})


@login_required
def ticket_detail(request, numero):
    """Détail d'une requête (mockup complet)."""
    ticket = get_object_or_404(Requete, numero=numero)
    return render(request, 'tickets/detail.html', {'ticket': ticket})
