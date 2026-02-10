# Fix 001: BASE_DIR no definido en settings.py

## Problema

Al ejecutar `python manage.py runserver` se producía:

```
NameError: name 'BASE_DIR' is not defined
```

En `mueblesrd_api/settings.py` se usaba `BASE_DIR` en las llamadas a `load_dotenv()` (líneas 10-14) **antes** de definir la variable, lo que provocaba el error al cargar la configuración de Django.

## Causa

`BASE_DIR` es la variable estándar en Django para la ruta base del proyecto. En este archivo se había dejado el comentario típico ("Build paths inside the project like this: BASE_DIR / 'subdir'") pero la definición de `BASE_DIR` no estaba presente, y además `load_dotenv()` necesitaba esa ruta para cargar el `.env`.

## Solución

Se definió `BASE_DIR` **antes** de cualquier uso, justo después de los imports:

```python
BASE_DIR = Path(__file__).resolve().parent.parent
```

- `Path(__file__).resolve()` → ruta absoluta de `settings.py`
- `.parent` → carpeta del archivo (`mueblesrd_api`)
- `.parent.parent` → carpeta del proyecto Django (`backend`)

Con esto, `load_dotenv(BASE_DIR / '.env')` y `load_dotenv(BASE_DIR.parent / '.env')` pueden ejecutarse correctamente.

## Archivos modificados

- `backend/mueblesrd_api/settings.py`: añadida la línea `BASE_DIR = Path(__file__).resolve().parent.parent` antes de las llamadas a `load_dotenv()`.

## Fecha

2026-02-08
