from django.contrib import admin
from .models import Contact, Requete


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('nom_complet', 'adresse_email', 'telephone_mobile')
    search_fields = ('nom_complet', 'adresse_email')


@admin.register(Requete)
class RequeteAdmin(admin.ModelAdmin):
    list_display = ('numero', 'objet', 'statut', 'priorite', 'contact', 'date_ouverture')
    list_filter = ('statut', 'priorite')
    search_fields = ('numero', 'objet', 'description')
    raw_id_fields = ('contact',)
    date_hierarchy = 'date_ouverture'
    readonly_fields = ('created_at', 'updated_at')
