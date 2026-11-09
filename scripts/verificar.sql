-- Resumen del contenido de la base (lo usan scripts/verificar.ps1 y scripts/verificar.sh).
-- Solo lee: sirve para comprobar un respaldo, una restauración o una base recién vaciada.
\pset footer off

\echo '== Estudiantes'
SELECT count(*) AS estudiantes FROM estudiante;

\echo '== Cargas por momento de prediccion'
SELECT momento, count(*) AS cargas,
       sum(registros_validos) AS registros_validos,
       sum(registros_rechazados) AS registros_rechazados
FROM carga
GROUP BY momento
ORDER BY CASE momento WHEN 'inscripcion' THEN 1 WHEN 'cierre_1s' THEN 2 ELSE 3 END;

\echo '== Alertas por nivel de urgencia (prediccion vigente de cada alerta)'
SELECT coalesce(p.nivel, 'total') AS nivel, count(*) AS alertas
FROM alerta a JOIN prediccion p ON p.id_prediccion = a.id_prediccion
GROUP BY ROLLUP (p.nivel)
ORDER BY CASE p.nivel WHEN 'alto' THEN 1 WHEN 'medio' THEN 2 WHEN 'bajo' THEN 3 ELSE 4 END;

\echo '== Alertas por estado de seguimiento'
SELECT coalesce(estado, 'total') AS estado, count(*) AS alertas
FROM alerta
GROUP BY ROLLUP (estado)
ORDER BY CASE estado WHEN 'pendiente' THEN 1 WHEN 'contactado' THEN 2
                     WHEN 'en_acompanamiento' THEN 3 ELSE 4 END;

\echo '== Cambios de estado registrados (CAMBIO_ESTADO)'
SELECT count(*) AS cambios_de_estado FROM cambio_estado;

\echo '== Modelos (MODELO)'
SELECT momento, version, habilitado, auc_roc, umbral_alto, umbral_medio
FROM modelo
ORDER BY CASE momento WHEN 'inscripcion' THEN 1 WHEN 'cierre_1s' THEN 2 ELSE 3 END, version;

\echo '== Datos iniciales y totales'
SELECT (SELECT count(*) FROM rol) AS roles,
       (SELECT count(*) FROM usuario) AS usuarios_de_prueba,
       (SELECT count(*) FROM modelo WHERE habilitado) AS modelos_habilitados,
       (SELECT count(*) FROM prediccion) AS predicciones,
       (SELECT count(*) FROM prediccion WHERE vigente) AS predicciones_vigentes;

\echo 'Referencia con las tres cargas de data/cargas/: 885 estudiantes y 529 alertas (137 alto, 131 medio, 261 bajo).'
