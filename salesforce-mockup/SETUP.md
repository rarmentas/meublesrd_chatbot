# Meubles RD – Mockup Salesforce (Django)

Mockup de la vista de requêtes (casos) con tabla de tickets, detalle completo por ticket e idiomas **Français** / **English**.

## Requisitos

- **Conda** (Anaconda o Miniconda) instalado en la máquina.
- No hace falta tener `python` en el PATH: se usa el entorno conda.

---

## 1. Crear el entorno Conda en el proyecto

Abre una terminal (PowerShell o CMD) y colócate en la carpeta del mockup:

```powershell
cd C:\Apps\meublesRD_chatbot\salesforce-mockup
```

Crea un entorno conda **dentro** de esta carpeta (prefix = carpeta `venv`):

```powershell
conda create --prefix .\venv python=3.11 -y
```

Si prefieres un entorno con nombre (en el directorio por defecto de conda):

```powershell
conda create -n meublesrd-mockup python=3.11 -y
```

---

## 2. Activar el entorno

**Si usaste `--prefix .\venv`:**

```powershell
conda activate C:\Apps\meublesRD_chatbot\salesforce-mockup\venv
```

**Si usaste `-n meublesrd-mockup`:**

```powershell
conda activate meublesrd-mockup
```

---

## 3. Instalar las dependencias

Siempre con el entorno activado:

```powershell
pip install -r requirements.txt
```

---

## 4. Migraciones y datos de prueba

```powershell
python manage.py migrate
python manage.py load_sample_tickets
```

Para regenerar los datos de demo (borra las requêtes/contactos existentes y vuelve a crear ejemplos):

```powershell
python manage.py load_sample_tickets --clear
```

---

## 5. Traducciones (FR/EN)

Por defecto las cadenas están en francés. Las traducciones al inglés están en `tickets/locale/en/LC_MESSAGES/django.po`. Para que el inglés se muestre bien, compila las traducciones (.po → .mo):

```powershell
python manage.py compilemessages
```

Sin este paso el sitio funciona en francés; en inglés, algunas etiquetas pueden seguir en francés hasta que ejecutes `compilemessages`.

---

## 6. Arrancar el servidor

```powershell
python manage.py runserver
```

Luego abre en el navegador:

- **Lista de tickets:** http://127.0.0.1:8000/ (o http://127.0.0.1:8000/fr/ / http://127.0.0.1:8000/en/)
- **Detalle de un ticket:** http://127.0.0.1:8000/00430578/ (después de cargar datos con `load_sample_tickets`)
- **Admin de Django (crear/editar tickets):** http://127.0.0.1:8000/admin/

Para crear un superusuario y acceder al admin:

```powershell
python manage.py createsuperuser
```

---

## Resumen de comandos (con conda activado)

| Acción              | Comando                                        |
|---------------------|------------------------------------------------|
| Crear env conda     | `conda create --prefix .\venv python=3.11 -y`  |
| Activar             | `conda activate .\venv` (o ruta completa)     |
| Instalar deps       | `pip install -r requirements.txt`             |
| Migraciones         | `python manage.py migrate`                    |
| Datos de demo       | `python manage.py load_sample_tickets`       |
| Traducciones        | `python manage.py compilemessages`           |
| Arrancar servidor   | `python manage.py runserver`                  |
