# Verificación de la versión 1.0.0

La prueba local completa se ejecutó el 2026-10-10 con el punto único
`python reproducir.py`, sin cuentas externas. NumPy 2.3.5, Python del entorno
de prueba local. No accedió a carpetas anteriores en esta ejecución.

- Siete pruebas unitarias aprobaron: estabilidad numérica, empates, densidad
  uniforme, esquema público sin identificadores, particiones, selección por
  calibración y cota residual.
- Se reconstruyeron 48 comparaciones y 24 diferencias por bloques.
- Diferencia máxima de métricas frente a referencia: 0.0000006545621.
- Se infirieron 2993619 píxeles de construido válido.
- Diferencia máxima de log-score por píxel: 0.0000004768372.
- Todas las clasificaciones de los cortes 80/90/95 coincidieron después de
  fijar cuantiles en float64, para las dos representaciones territoriales.
- Los índices de seis escenarios y 65 parroquias coincidieron con las
  referencias incluidas, diferencia máxima en valores comprobados: 0.

Además se ejercitó la ruta de reentrenamiento en CPU con PyTorch 2.11.0.
Las seis redes de la aplicación se entrenaron hasta 300 y la calibración
seleccionó B=0.25; las tres semillas de B=0.25 seleccionaron epoch 20.
Las pequeñas diferencias de calibración frente al histórico se conservan en
VERIFICACION_REENTRENAMIENTO_CPU.json. Reentrenar no equivale a igualdad
bit a bit ni a reconstruir desde cero el procesamiento de datos originales.

MANIFEST.json permite comprobar el paquete completo. La revisión preventiva
de patrones de secretos no encontró los patrones evaluados; no es una
auditoría de seguridad certificada. Estas comprobaciones son de integridad
y reproducción computacional, no validación externa de inundación o daños.
