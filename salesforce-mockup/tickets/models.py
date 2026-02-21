from django.db import models


class Requete(models.Model):
    """Requête / Case (ticket) – Only fields relevant for copilot."""

    numero = models.CharField(max_length=20, unique=True)
    claim_type = models.CharField(max_length=200, blank=True)
    damage_type = models.CharField(max_length=200, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    product_type = models.CharField(max_length=100, blank=True)
    manufacturer = models.CharField(max_length=200, blank=True)
    store_of_purchase = models.CharField(max_length=200, blank=True)
    product_code = models.CharField(max_length=50, blank=True)
    purchase_contract_number = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    claim_date = models.DateTimeField(null=True, blank=True)
    has_attachments = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.numero} | {self.claim_type[:50]}'

    class Meta:
        verbose_name = 'Requête'
        verbose_name_plural = 'Requêtes'
        ordering = ['-claim_date', '-created_at']
