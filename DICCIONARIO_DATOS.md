# Diccionario de datos

Todos los NPZ son arreglos numéricos, sin objetos pickle. Leer con
`np.load(..., allow_pickle=False)`. Los CSV usan UTF-8, punto decimal y
códigos parroquiales como texto.

| Archivo/campo | Unidad y significado |
| --- | --- |
| DATOS_*.npz / Xe | reportes × 25 posiciones × covariables, estandarizadas y acotadas |
| Xb | 60000 puntos de fondo × covariables, no hogares ni ausencia de inundación |
| valid_e | soporte geográfico válido por posición; no etiqueta agua/no agua |
| etrain/ecal/etest | máscaras disjuntas de reportes, específicas del protocolo |
| btrain/bcal/btest | fondo de integración por protocolo; en temporal se reutiliza el dominio |
| anchor, lo, hi | coeficientes y límites exactos de normalización, orden en PARAMETROS.json |
| block | identificador numérico de bloque de 5 km; no coordenadas originales de reportes |
| clipped_e/clipped_b | indicador de soporte recortado, no inundación |
| PIXELES_*.npz / X | covariables de construido válido, mismo orden de la aplicación FABDEM |
| flat | índice fila*ancho+columna en GRILLA.json, no parcela catastral |
| pid | id_censo 1–65; 0 no asignado a parroquia |
| wid | índice en weather_units de GRILLA.json |
| clipped/edge | soporte recortado e influencia de borde hidrológico |
| referencia_score | dos log-densidades de referencia: residual y ancla, para control numérico |
| PESOS.npz | pesos propios float32 de 48 redes; claves modelo/cota/semilla/capa |
| DATOS_PARROQUIAS.csv / pc_pnbi | % de personas en universo NBI del censo municipal 2022 |
| pc_SH, pc_FSA, pc_HAC | % saneamiento inadecuado, acceso limitado a agua segura y hacinamiento; cada universo propio |
| DATOS_LLUVIA_ESCENARIOS.csv / p_humedo | probabilidad de categoría húmeda, no probabilidad de inundación |
| area_prioritaria_ha | área construida en decil de score, 1 píxel=0.01 ha |
| area_prioritaria_ponderada_humedad_ha | índice de superficie ponderado por P_húmedo regional |
| indice_NBI_ha_ponderadas | índice anterior multiplicado por tasa NBI/100 |

No contiene ENEMDU, identificadores de personas, viviendas o UPM, titulares de
catastro, direcciones o coordenadas puntuales de reportes. Sólo flat de la
grilla física, geometría parroquial y contexto censal agregado son geolocalizados.
