# Métodos y reproducción

1. Las fuentes públicas se proyectaron a EPSG:32717. La grilla de análisis es
   10 m, origen y dimensiones en GRILLA.json. Terreno y rutas D8 mantienen
   soporte 30 m. La construcción es clase 50 de WorldCover 2021.
2. Las covariables incluyen elevación, pendiente, posición topográfica, relieve
   local, distancias a río/quebrada/colector, densidad construida a 100/500 m,
   once clases de cobertura, distancia vial y cuatro indicadores de escorrentía.
   Las transformaciones y nombres están en PARAMETROS.json y código histórico.
   Una depresión DEM es un proxy, no un paso deprimido comprobado.
3. Las medias y desviaciones se fijaron en entrenamiento. Covariables continuas
   se acotaron a cuantiles 0.005/0.995 del fondo de entrenamiento; las clases
   categóricas no se recortaron. DATOS_*.npz contienen la transformación exacta.
4. La ancla se ajustó con penalización lambda en {0.001, 0.01, 0.1, 1} y
   temperado {0.25, 0.5, 0.75, 1, 1.25}, usando calibración. Esta distribución
   reentrena la corrección residual sobre el ancla congelada; no vuelve a
   estimar las anclas en la ejecución estándar.
5. La función objetivo es log integral de intensidad sobre cuadratura menos
   log intensidad marginal por reporte, más 0.10*media(residual²). AdamW:
   lr=0.002, weight_decay=0.05, clip gradiente=5, epochs 0–300. Cada 10 epochs
   se evalúa calibración, con tres semillas por cota. La iteración rotulada
   epoch 0 ya contiene una actualización, como el script histórico original.
6. En temporal se conserva el fondo territorial de 60000 puntos en las tres
   normalizaciones: la independencia de resultados se evalúa por reportes,
   no por puntos de fondo. En espacial se reserva dominio territorial y
   soporte de borde. Tras esa reserva hay 191 reportes elegibles en espacial;
   los 331 corresponden al protocolo temporal. Las máscaras incluidas son la
   definición operativa, no necesariamente el mismo número en ambos dominios.
7. Cada semilla se normaliza sobre el mismo fondo de evaluación y el ensamble
   promedia densidades. Log-densidad se marginaliza sobre posiciones válidas.
   Captura del 10 % trata empates fraccionalmente. Bootstrap emparejado:
   3000 réplicas por bloques de 5 km, semilla 11109, inferencia exploratoria.
8. La aplicación completa normaliza cada semilla en todos los 2993619 píxeles
   construidos válidos. Se retiran 28776 píxeles sin soporte; 84 no se asignan
   a parroquia. No se pinta el área omitida como libre de amenaza.
9. Los deciles de construido se cruzan con unidades de lluvia. Para parroquia p,
   A_p = sum_j(area prioritaria_pj * P_húmedo_j). Para objetivo social s,
   I_ps = A_p * tasa_ps/100. Son ha ponderadas, no personas o daños.
   Se conserva el mismo snapshot NDJ 2026–2027, tres modelos meteorológicos
   y dos territoriales. Las tasas sociales nunca se suman entre sí.

## Niveles de verificabilidad

`python reproducir.py` reconstruye inferencia residual, benchmark, mapa y
priorización. Los comparadores históricos se evalúan con predicciones
congeladas y los escenarios con probabilidades congeladas. No presenta esas
dos etapas como entrenamiento desde cero. El reentrenamiento opcional usa
las covariables procesadas y anclas congeladas. Las extracciones originales
requieren datos fuente y configuración geoespacial adicional, indicados en
FUENTES.json y CODIGO_HISTORICO.zip. Esta separación permite auditar qué se
recalculó y qué se reutilizó.

Los cuantiles del mapa se calculan en float64 para evitar que diferencias entre
versiones de NumPy en cuantiles float32 cambien un píxel de frontera. La
inferencia usa los pesos float32 originales y verifica una tolerancia de 2e-5
en log-score. Cualquier cambio clasificatorio debe permanecer dentro de esa
tolerancia y se registra; el decil primario requiere clasificación idéntica.
