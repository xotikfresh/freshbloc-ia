# Dago

App Streamlit para crear contenido de Instagram y WhatsApp para negocios pequeños usando Groq para texto y Recraft para editar fotos reales de productos o locales.

## Ejecutar localmente

1. Instala dependencias:

```bash
pip install -r requirements.txt
```

2. Crea `.streamlit/secrets.toml` usando `.streamlit/secrets.example.toml` como referencia.

3. Inicia la app:

```bash
streamlit run app.py
```

## Desplegar en Streamlit Community Cloud

1. Entra a Streamlit Community Cloud y crea una app nueva desde GitHub.
2. Selecciona el repositorio `xotikfresh/freshbloc-ia`.
3. Usa la rama `main` y el archivo principal `app.py`.
4. En "Advanced settings" agrega los secretos:

```toml
GROQ_API_KEY = "tu_clave_de_groq"
RECRAFT_API_KEY = "tu_clave_de_recraft"
```

5. Guarda y despliega.

## Archivos importantes

- `app.py`: app principal.
- `data/perfil_negocio.json`: perfil local del negocio.
- `data/historial.json`: historial local de piezas creadas.
- `data/usuarios.json`: cuentas locales con contraseñas hasheadas.
- `data/cuentas/`: perfil e historial separados por usuario.
- `.streamlit/secrets.toml`: claves locales `GROQ_API_KEY` y `RECRAFT_API_KEY`.

## Para masificar

La version actual funciona bien para uso local o una demo con un negocio. Para usarla con muchos negocios conviene separar:

- Usuarios y sesiones: login por negocio o administrador.
- Base de datos: reemplazar los JSON locales por SQLite, Supabase, Firebase o Postgres.
- Historial por negocio: cada cuenta debe tener su propio perfil e historial.
- Limites de uso: controlar generaciones por dia para cuidar costos de IA.
- Exportacion: guardar fotos editadas por Recraft y captions por cliente.
- Despliegue: Streamlit Community Cloud sirve para demo; para producto real conviene un hosting con base de datos persistente.
