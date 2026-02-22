from django.contrib import admin
from .models import Requete


@admin.register(Requete)
class RequeteAdmin(admin.ModelAdmin):
    list_display = (
        'numero', 'claim_type', 'damage_type', 'delivery_date', 'product_type',
        'manufacturer', 'store_of_purchase', 'product_code', 'purchase_contract_number',
        'short_description', 'claim_date', 'has_attachments'
    )

    @admin.display(description='Description')
    def short_description(self, obj):
        return (obj.description[:50] + '...') if obj.description and len(obj.description) > 50 else (obj.description or '—')
    list_filter = ('claim_type', 'product_type', 'has_attachments')
    search_fields = ('numero', 'claim_type', 'description', 'purchase_contract_number')
    date_hierarchy = 'claim_date'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('numero', 'claim_type', 'damage_type', 'description', 'claim_date', 'has_attachments')
        }),
        ('Produit', {
            'fields': ('product_type', 'manufacturer', 'store_of_purchase', 'product_code', 'purchase_contract_number')
        }),
        ('Livraison', {
            'fields': ('delivery_date',)
        }),
        ('Système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
