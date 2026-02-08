from django.db import models


class Contact(models.Model):
    """Contact associé aux requêtes."""
    nom_complet = models.CharField(max_length=200)
    nom_du_compte = models.CharField(max_length=200, blank=True)
    adresse_email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    telephone_mobile = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.nom_complet

    class Meta:
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'


class Requete(models.Model):
    """Requête / Case (ticket)."""
    STATUT_CHOICES = [
        ('nouveau', 'Nouveau'),
        ('en_traitement', 'En traitement'),
        ('en_attente_client', 'En attente du client'),
        ('en_suspens', 'En suspens'),
        ('ferme', 'Fermé'),
    ]
    PRIORITE_CHOICES = [
        ('bas', 'Bas'),
        ('moyen', 'Moyen'),
        ('haut', 'Haut'),
    ]

    numero = models.CharField(max_length=20, unique=True)
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='requetes')
    proprietaire = models.CharField(max_length=200, default='')
    statut = models.CharField(max_length=30, choices=STATUT_CHOICES, default='nouveau')
    priorite = models.CharField(max_length=20, choices=PRIORITE_CHOICES, default='moyen')
    objet = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    date_ouverture = models.DateTimeField(null=True, blank=True)
    date_fermeture = models.DateTimeField(null=True, blank=True)

    # Case Information
    magasin = models.CharField(max_length=200, blank=True)
    requete_principale = models.CharField(max_length=100, blank=True)
    lead_id = models.CharField(max_length=100, blank=True)
    origine = models.CharField(max_length=100, blank=True)
    origine_requete = models.CharField(max_length=100, blank=True)
    suiveur = models.CharField(max_length=200, blank=True)
    cc_courriel = models.CharField(max_length=200, blank=True)

    # Champs clés / Category
    classification = models.CharField(max_length=200, blank=True)
    sous_sujet = models.CharField(max_length=200, blank=True)
    type_requete_client_interne = models.CharField(max_length=200, blank=True)
    sujet_livraison_interne = models.CharField(max_length=200, blank=True)
    sujet_ads_interne = models.CharField(max_length=200, blank=True)
    avis_formel = models.CharField(max_length=200, blank=True)
    numero_contrat_achat = models.CharField(max_length=50, blank=True)
    manufacturier = models.CharField(max_length=200, blank=True)
    code_produit = models.CharField(max_length=50, blank=True)
    type_produit = models.CharField(max_length=100, blank=True)
    no_serie_appareil = models.CharField(max_length=100, blank=True)
    type_achat = models.CharField(max_length=100, blank=True)
    no_requete_a_suivre = models.CharField(max_length=50, blank=True)
    ads_need_type = models.CharField(max_length=100, blank=True)

    # Description Information
    envoyer_courriel_contact = models.BooleanField(default=False)
    commentaires_internes = models.TextField(blank=True)
    modification_sms = models.TextField(blank=True)

    # Delivery Information
    type_reception = models.CharField(max_length=100, blank=True)
    region_livraison = models.CharField(max_length=200, blank=True)
    no_compte_client_meublex = models.CharField(max_length=100, blank=True)
    date_livraison = models.DateField(null=True, blank=True)
    ajustement_contrat = models.CharField(max_length=50, blank=True)
    capacite_cubage = models.CharField(max_length=100, blank=True)
    plage_horaire_desiree = models.CharField(max_length=200, blank=True)
    changement_contrat_bloque = models.CharField(max_length=100, blank=True)
    instructions_speciales = models.TextField(blank=True)

    # ADS Information
    numero_ads = models.CharField(max_length=50, blank=True)
    solution = models.TextField(blank=True)
    information_additionnelle = models.TextField(blank=True)
    type_dommage = models.CharField(max_length=200, blank=True)
    type_compensation = models.CharField(max_length=100, blank=True)
    montant_dedommagement = models.CharField(max_length=50, blank=True)
    numero_lot = models.CharField(max_length=50, blank=True)
    code_production = models.CharField(max_length=50, blank=True)

    # Web-to-case
    preference_communication = models.CharField(max_length=200, blank=True)
    contrat_livraison_interne = models.BooleanField(default=False)

    # Web Information
    nom_web = models.CharField(max_length=200, blank=True)
    telephone_web = models.CharField(max_length=50, blank=True)
    prenom_client = models.CharField(max_length=100, blank=True)
    nom_client = models.CharField(max_length=100, blank=True)
    nom_complet_client = models.CharField(max_length=200, blank=True)
    courriel_client = models.EmailField(blank=True)
    telephone_client = models.CharField(max_length=50, blank=True)

    # SLA
    arrete = models.BooleanField(default=False)
    arrete_depuis = models.CharField(max_length=100, blank=True)
    nom_autorisation_sla = models.CharField(max_length=200, blank=True)

    # System Information
    nombre_total_produits_defectueux = models.PositiveIntegerField(default=0)
    solution_derniere_modification_par = models.CharField(max_length=300, blank=True)
    courriel_envoye_a = models.CharField(max_length=300, blank=True)
    cree_par = models.CharField(max_length=200, blank=True)
    type_besoin = models.CharField(max_length=100, blank=True)
    derniere_file_attente = models.CharField(max_length=200, blank=True)
    nombre_produits_defectueux_ouverts = models.PositiveIntegerField(default=0)
    depuis_le_web = models.BooleanField(default=False)
    fermeture_lors_creation = models.BooleanField(default=False)
    langue = models.CharField(max_length=50, default='Français')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.numero} | {self.objet[:50]}'

    class Meta:
        verbose_name = 'Requête'
        verbose_name_plural = 'Requêtes'
        ordering = ['-date_ouverture', '-created_at']
