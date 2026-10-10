# Modelo y resultados: alcance verificable

## Objetivo y arquitectura

Localizar intensidad relativa de reportes de inundación del cantón Quito.
La red residual propia estima `f(x) = beta*x + B*tanh(g(x))`, con ancla loglineal
congelada y `g` de capas 16/8, activación SiLU y dropout 0.10. El ensamble usa
tres semillas. El fondo numérico de integración no son casos negativos.

Cuatro variantes: base, vías, vías + escorrentía Copernicus y vías + escorrentía
FABDEM. Dos particiones: temporal y espacial. Se incluyen los 48 pesos
residuales y resultados de todas las variantes, no sólo los favorables.

Universo temporal de 331 reportes de inundación entre 2010 y septiembre 2025;
191 reportes son elegibles después de la reserva espacial y de borde.
Por reporte se marginalizan 25 posiciones en radio de 100 m. Test temporal:
100 reportes, 36 bloques. Test espacial: 58 reportes, 13 bloques. Fechas y
particiones exactas se preservan en el código histórico y las máscaras.

## Selección y aplicación

La cota B pertenece a {0.25, 1.0} y se elige por log-densidad media de
calibración. No se usa test para elegir B ni la parada. Las variantes se
desarrollaron después de conocer versiones anteriores; no es una validación
prospectiva ciega. La aplicación social previamente fijada usa
`temporal__vias_fabdem`, B=0.25 y semillas 5101/5102/5103, epoch seleccionado 20.
Es la versión integrada más completa, no un ganador universal por test.

El caso temporal de esa aplicación obtiene log-densidad relativa 1.963446 y
captura de soporte 0.8676 en el 10 % del territorio, frente a 1.948581 y 0.8784
de la red libre. La mejoría en log-densidad no implica mejora en captura.
En espacial, la red residual FABDEM obtiene 1.069634, frente a 1.107781 del
loglineal y -1.297376 de la red libre. Se conserva esta limitación de transferencia.

El decil del mapa sobre **construido** usa un denominador diferente del
benchmark territorial. No se confunden sus umbrales o métricas. La prioridad
parroquial incorpora lluvia estacional y cuatro objetivos sociales por separado.
Optimizar un índice NBI aumenta ese mismo índice por construcción; no es prueba
independiente de mejor predicción ni beneficio causal.

## Límites y usos

Uso adecuado: reproducción académica, auditoría de transferencia y exploración
de prioridades con sus coberturas. No usar para decisiones individuales de
crédito, seguros, vivienda, evacuación o declarar un domicilio seguro.

- No segmenta agua SAR ni mide profundidad, mortalidad o pérdidas monetarias.
- No está validado como pronóstico de inundación futura por píxel.
- Fuentes de cobertura 2021 y condiciones actuales se aplican retrospectivamente;
  el ensayo no prueba disponibilidad histórica de cada predictor.
- Relieve nativo 30 m, grilla 10 m. No equivale a un LiDAR de 10 m.
- Subregistro y geocodificación pueden reflejar acceso a reporte, además de amenaza.
- NBI 2022 permanece parroquial. No identifica hogares pobres de cada píxel.
- Hay diferencias entre universos censales municipales y cantonales. No se
  calculan personas afectadas a partir de estos porcentajes.
- La rama ENEMDU económica no mostró efectos primarios robustos después de
  corrección múltiple y no se incorpora como pérdidas o causalidad al mapa.

Microsoft SAR (Misra et al., 2025, DOI 10.1038/s41467-025-60973-1) segmenta agua
con pares Sentinel-1 y máscaras de referencia. Sus F1/IoU no se comparan con
la captura de soporte de reportes de esta red. No se afirma superarlo.
