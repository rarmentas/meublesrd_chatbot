# MeublesRD — AI QA Copilot (demo)

Este repositorio contiene artefactos y fuentes para un **copiloto de aseguramiento de calidad (QA) asistido por IA** que guía a agentes en **procesamiento de reclamos (claims)** —en el alcance del demo para **Meubles RD**— sin requerir integraciones profundas con sistemas como Salesforce.

## Contexto (resumen)
Gravitas, Acumen & Co (GAC) opera mandatos de customer experience y claims para retailers e-commerce. Se detectó un riesgo operativo importante: **errores humanos** (especialmente en agentes recién incorporados) que provocan:

- Campos obligatorios faltantes o mal formateados (p. ej. *product ID*, número de serie, fotos).
- Estados de ticket incorrectos (p. ej. “In treatment” vs “Suspended”).
- Pasos de SOP no cumplidos (p. ej. requisitos de cumplimiento como *Law 25*).
- Tono o redacción inadecuada en interacciones de fricción alta.

El objetivo del demo es mostrar un copiloto que, en tiempo real, **analiza lo visible del ticket** (campos, texto del cliente, comentarios, adjuntos) y lo cruza con **SOPs** y principios de comunicación para entregar **recordatorios y recomendaciones accionables**, sin modificar automáticamente el ticket; al mismo tiempo, realizar el desarrollo del producto bajo un marco de trabajo ágil.

## Qué hay en este repo
- `data/raw/`: **SOPs y documentos fuente** (PDF) usados como base de conocimiento para el demo.
- `data/interim/`: documentos intermedios (p. ej. versiones o extractos en DOCX) para preparación/ingesta.
- `docs/`: documentación interna del trabajo (p. ej. embeddings/ingesta/planeación del proyecto).
- `notebooks/`: notebooks de experimentación/ingesta.  
  - `notebooks/ingestion_politics_mueblesrd.ipynb`: ingesta de PDFs a un vector store en **Pinecone** usando **LangChain** + **OpenAI embeddings**.
- `reports/`: salidas/exportaciones del trabajo (p. ej. PDF exportado desde Colab del notebook).

> Nota: Este repo irá incorporando también componentes como **preprocesamiento**, desarrollo de la **extensión de Chrome**, y scripts de **build** conforme avance el proyecto.

## Alcance del demo (en pocas palabras)
- **En alcance**: reclamos por *damaged items* y *missing parts*, análisis *read-only* del contenido visible, guía y checklist de QA, validación final antes de cerrar/moverse al siguiente ticket.
- **Fuera de alcance (demo)**: integración completa por API con Salesforce, write-back automático al ticket, cobertura de todos los procesos.

## Quickstart — Ingesta de SOPs a Pinecone (Colab)
El notebook `notebooks/ingestion_politics_mueblesrd.ipynb` está pensado para ejecutarse en Google Colab.

1. Abre el notebook en Colab.
2. Instala dependencias (celda `pip install` del notebook).
3. Configura secretos/variables:
   - `OPENAI_API_KEY` (requerida)
   - `PINECONE_API_KEY` (requerida)
   - `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` (opcionales)
4. Crea/selecciona tu índice en Pinecone y ajusta `INDEX_NAME` en el notebook.
5. Sube el PDF y ejecuta la indexación.

## Consideraciones de datos
- Para el demo no se requiere persistir datos de clientes.
- Se agegarán ejemplos históricos, **anonimizados** antes de versionarse.

## Estado del proyecto
Este repositorio es **demo-first**: prioriza la claridad del flujo (SOP → ingesta → recuperación) y la demostración de valor del copiloto QA.

