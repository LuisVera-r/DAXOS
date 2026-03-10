-- ══════════════════════════════════════════════════════════════════
-- Schema: Dashboard Operaciones Comercio Exterior
-- Solo 2 tablas: ce_detalle (pedimentos) + ce_config (settings)
-- Ejecuta en Supabase → SQL Editor → Run
-- ══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS ce_detalle (
    id                  BIGSERIAL   PRIMARY KEY,
    periodo             TEXT        NOT NULL,
    aduana              TEXT,
    importador_id       TEXT,
    importador_nombre   TEXT,
    cliente             TEXT,
    ejecutivo           TEXT,
    tipo_op             TEXT,
    referencia          TEXT,
    pedimento           TEXT,
    f_generacion        TIMESTAMPTZ,
    f_llegada           TIMESTAMPTZ,
    f_revalida          TIMESTAMPTZ,
    f_previo            TIMESTAMPTZ,
    f_pago              TIMESTAMPTZ,
    f_despacho          TIMESTAMPTZ,
    f_contabilidad      TIMESTAMPTZ,
    f_facturacion       TIMESTAMPTZ,
    lt_total            FLOAT,
    lt_llegada_pago     FLOAT,
    lt_pago_despacho    FLOAT,
    lt_despacho_factura FLOAT,
    mes                 TEXT
);

CREATE INDEX IF NOT EXISTS idx_det_periodo   ON ce_detalle(periodo);
CREATE INDEX IF NOT EXISTS idx_det_ejecutivo ON ce_detalle(ejecutivo);
CREATE INDEX IF NOT EXISTS idx_det_aduana    ON ce_detalle(aduana);
CREATE INDEX IF NOT EXISTS idx_det_tipo_op   ON ce_detalle(tipo_op);
CREATE INDEX IF NOT EXISTS idx_det_cliente   ON ce_detalle(cliente);

-- Configuración (equipos JSON, etc.)
CREATE TABLE IF NOT EXISTS ce_config (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Sin RLS (app de un solo usuario vía anon key)
ALTER TABLE ce_detalle DISABLE ROW LEVEL SECURITY;
ALTER TABLE ce_config  DISABLE ROW LEVEL SECURITY;

-- ── Vistas analíticas útiles ──────────────────────────────────────

CREATE OR REPLACE VIEW v_resumen_periodos AS
SELECT
    periodo,
    COUNT(*)                                                              AS total_ops,
    SUM(CASE WHEN tipo_op ILIKE '%import%' THEN 1 ELSE 0 END)           AS importaciones,
    SUM(CASE WHEN tipo_op ILIKE '%export%' THEN 1 ELSE 0 END)           AS exportaciones,
    COUNT(DISTINCT ejecutivo)                                             AS ejecutivos,
    COUNT(DISTINCT cliente)                                               AS clientes,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY lt_total)::NUMERIC, 1) AS lt_mediana
FROM ce_detalle
GROUP BY periodo
ORDER BY periodo;

CREATE OR REPLACE VIEW v_lt_ejecutivo AS
SELECT
    periodo, ejecutivo,
    COUNT(*)                                                                   AS ops,
    ROUND(AVG(lt_total)::NUMERIC, 1)                                           AS lt_promedio,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY lt_total)::NUMERIC, 1)  AS lt_mediana,
    ROUND(PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY lt_total)::NUMERIC, 1)  AS lt_p90
FROM ce_detalle
WHERE lt_total IS NOT NULL
GROUP BY periodo, ejecutivo
ORDER BY periodo, lt_promedio DESC;

CREATE OR REPLACE VIEW v_top_clientes AS
SELECT cliente, periodo, COUNT(*) AS ops
FROM ce_detalle
GROUP BY cliente, periodo
ORDER BY ops DESC;
