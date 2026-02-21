# 002 - Copiar tickets desde imágenes de Salesforce a la DB

## Contexto

El sistema salesforce-mockup simula una plataforma de Salesforce para almacenar tickets.
El modelo `Requete` contiene únicamente los campos relevantes para copilot, y el resto
de campos del formulario original muestra "Not used for copilot".

## Campos del modelo

| Campo en el modelo         | Label en el frontend           | Tipo       |
|----------------------------|--------------------------------|------------|
| `numero`                   | Case Number (identificador)    | CharField  |
| `claim_type`               | Classification                 | CharField  |
| `damage_type`              | Damage type                    | CharField  |
| `delivery_date`            | Delivery date                  | DateField  |
| `product_type`             | Product type                   | CharField  |
| `manufacturer`             | Manufacturer                   | CharField  |
| `store_of_purchase`        | Store                          | CharField  |
| `product_code`             | Product code                   | CharField  |
| `purchase_contract_number` | Purchase contract number       | CharField  |
| `description`              | Description                    | TextField  |
| `claim_date`               | Open date                      | DateTimeField |
| `has_attachments`          | Has attachments                | BooleanField |

## Proceso para copiar un ticket desde una imagen

### 1. Recibir la imagen

El usuario comparte una captura de pantalla de un ticket de Salesforce real.
La imagen se guarda automáticamente en el workspace y se lee para extraer los datos.

### 2. Identificar los campos en la imagen

Cada campo de interés se ubica visualmente en la captura:

| Campo              | Dónde se encuentra en la imagen de Salesforce          |
|--------------------|--------------------------------------------------------|
| Case Number        | Encabezado del caso / Case Information → Case Number   |
| Classification     | Category → Classification                              |
| Damage type        | ADS Information → Type de dommage                      |
| Delivery date      | Delivery Information → Date de livraison               |
| Product type       | Category → Type de produit                             |
| Manufacturer       | Category → Manufacturier                               |
| Store              | Case Information → Magasin                             |
| Product code       | Category → Code de produit                             |
| Purchase contract  | Category → Numéro du contrat d'achat                  |
| Description        | Description Information → Description                  |
| Open date          | System Information → Date/Heure d'ouverture            |
| Has attachments    | Panel derecho → Files (si hay archivos adjuntos)       |

### 3. Insertar el ticket en la base de datos

Se usa el Django shell con el venv del proyecto backend:

```bash
cd /home/rarme/meublesrd_chatbot/salesforce-mockup
/home/rarme/meublesrd_chatbot/backend/venv/bin/python manage.py shell -c "
from tickets.models import Requete
from datetime import datetime

Requete.objects.create(
    numero='XXXXXXXX',
    claim_type='Defective or damaged product',
    damage_type='Mechanical',
    delivery_date=datetime(2026, 1, 17).date(),
    product_type='Furniture',
    manufacturer='Other Manufacturer',
    store_of_purchase='DJ - Saint-Jérôme',
    product_code='10527F',
    purchase_contract_number='N62005',
    description='Le moteur du relevable pieds fait un bruit...',
    claim_date=datetime(2026, 1, 28, 10, 56),
    has_attachments=True,
)
"
```

### 4. Verificar

- Revisar en la vista tabular (`/`) que el ticket aparece con los datos correctos.
- Revisar en la vista detalle (`/<numero>/`) que los campos de interés muestran
  valores reales y el resto muestra "Not used for copilot".

### 5. Reiniciar el servicio (si es necesario)

```bash
sudo systemctl restart salesforce-mockup.service
```

## Notas

- Los campos del formulario que no son de interés se muestran con el texto
  "Not used for copilot" en gris itálico, manteniendo la apariencia original.
- El campo `numero` debe ser único; no se pueden crear dos tickets con el mismo número.
- El campo `has_attachments` es un booleano; se determina visualmente observando
  si la sección "Files" del panel derecho de Salesforce tiene archivos.
- Las etiquetas en la imagen de Salesforce pueden estar en francés o inglés;
  la tabla de mapeo de arriba cubre ambos idiomas.
