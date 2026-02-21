from django.contrib import admin
from .models import Requete


@admin.register(Requete)
class RequeteAdmin(admin.ModelAdmin):
    list_display = ('numero', 'claim_type', 'store_of_purchase', 'product_type', 'claim_date')
    list_filter = ('claim_type', 'product_type')
    search_fields = ('numero', 'claim_type', 'description', 'purchase_contract_number')
    date_hierarchy = 'claim_date'
    readonly_fields = ('created_at', 'updated_at')
