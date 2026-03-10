# Dashboard · Operaciones Comercio Exterior

Backends de persistencia disponibles (prioridad automática):

| Prioridad | Backend | Cuándo activa |
|-----------|---------|---------------|
| 1 | **Supabase** (PostgreSQL) | secrets `[supabase]` presentes |
| 2 | **GitHub** (pickle en repo) | secrets `[github]` presentes |
| 3 | **Local** (disco) | sin secrets (desarrollo) |

---

## Correr localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

El histórico se guarda en `data/historico.pkl`.

---

## Despliegue en Streamlit Cloud + Supabase (recomendado)

### PASO 1 — Crear proyecto en Supabase

1. Ve a https://supabase.com → **New project**
2. Elige nombre (ej. `ops-ce`) y región más cercana (US East o similar)
3. Guarda la contraseña de la DB (no la necesitarás directamente)
4. Espera ~2 minutos a que provisione

### PASO 2 — Crear el esquema de tablas

1. En tu proyecto de Supabase → **SQL Editor** → **New query**
2. Copia y pega el contenido de `supabase_schema.sql`
3. Clic en **Run** (debe decir "Success. No rows returned")

### PASO 3 — Obtener las credenciales

1. En Supabase → **Project Settings** → **API**
2. Copia:
   - **Project URL**: `https://xxxxxxxxxxxx.supabase.co`
   - **anon/public key**: `eyJhbGciOiJIUzI1NiIs...` (la larga)

### PASO 4 — Subir a GitHub y desplegar

```bash
git init && git add . && git commit -m "init"
git remote add origin https://github.com/TU_USUARIO/ops-ce-dashboard.git
git push -u origin main
```

En https://share.streamlit.io → New app → Advanced settings → **Secrets**:

```toml
[supabase]
url = "https://xxxxxxxxxxxx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIs..."
```

→ **Deploy**. Tu histórico ahora vive en PostgreSQL permanentemente.

---

## Estructura del proyecto

```
proyecto/
├── app.py                  ← App principal Streamlit
├── core.py                 ← Extracción + backends (Supabase / GitHub / local)
├── supabase_schema.sql     ← Ejecutar una vez en Supabase SQL Editor
├── requirements.txt
├── .streamlit/config.toml
└── data/
    ├── .gitkeep
    └── equipos.json        ← Generado automáticamente (backup local)
```

---

## Vistas SQL útiles (ya incluidas en el schema)

```sql
-- Resumen por periodo
SELECT * FROM v_resumen_periodos;

-- Lead time por ejecutivo
SELECT * FROM v_lt_ejecutivo WHERE periodo = '2026-01';

-- Top clientes
SELECT * FROM v_top_clientes LIMIT 20;
```

---

## Formato esperado del Excel

- Fila 10: encabezados (UDN, # Importador, Ejecutivo, TO, Pedimento, fechas…)
- Filas 11+: pedimentos
- Después del detalle: `EJECUTIVO IMPORTACION` (equipos), luego individual, luego exportación
- Encabezado con periodo: `"DEL 01 DE ENERO DEL 2026 AL 31 DE ENERO DEL 2026"`
