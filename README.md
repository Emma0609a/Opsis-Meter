# Opsis Meter

Sistema de conteo de limones con inteligencia artificial para bandas
transportadoras. Forma parte de la Suite Agropecuaria y sigue una estrategia
**offline-first**: el conteo ocurre 100% en la máquina local y los resultados
se sincronizan con la nube cuando hay conexión.

## Arquitectura

El código está organizado por **dominios** (screaming architecture): cada
carpeta dice qué hace el sistema, no qué tecnología usa.

```
main.py                      # Punto de entrada
opsis_meter/
├── app.py                   # Arranque y composición de la aplicación
├── menu_principal/          # Pantalla de inicio y navegación
│   └── ventana.py
├── captura/                 # Adquisición de video (cámaras locales e IP)
│   ├── camara.py            # FlujoCamara: hilo de captura seguro
│   └── dispositivos.py      # Detección de cámaras disponibles
├── conteo/                  # Cerebro de IA (Proceso B)
│   ├── ventana.py           # UI de conteo: vista previa + contador en vivo
│   ├── detector.py          # YOLO sobre ONNX Runtime
│   ├── rastreador.py        # Seguimiento multi-objeto (ByteTrack)
│   ├── linea_conteo.py      # Línea virtual de conteo
│   ├── proceso_ia.py        # Proceso independiente (multiprocessing)
│   └── mensajes.py          # Mensajes entre el proceso de IA y la UI
├── historial/               # Consulta de sesiones registradas
│   └── ventana.py
└── compartido/              # Tema visual, configuración y utilidades
    ├── tema.py
    ├── configuracion.py
    └── ventanas.py
tests/                       # Pruebas de la lógica de conteo
models/                      # Modelos ONNX (no se versionan)
```

## Instalación

```bash
pip install -r requirements.txt
cp .env.example .env   # y completar credenciales / ruta del modelo
python main.py
```

Para habilitar el conteo con IA, coloca un modelo YOLO exportado a ONNX en
`models/` (o define `OPSIS_MODELO` en `.env`). Sin modelo, la aplicación
funciona en modo vista previa.

## Hoja de ruta (por bloques)

- [x] **Bloque 0** — Estructura por dominios, configuración y saneamiento de la UI.
- [x] **Bloque 1** — Captura de video desacoplada y segura (`captura/`).
- [x] **Bloque 2** — Cerebro de IA: detección + seguimiento + línea virtual (`conteo/`).
- [ ] **Bloque 3** — Persistencia local offline-first (SQLite).
- [ ] **Bloque 4** — Integración con la nube (Supabase Auth, heartbeats, cierre de lote).
- [ ] **Bloque 5** — Backend C# (.NET): ingesta, Channels, Dapper, rate limiting.
- [ ] **Bloque 6** — Configuración en UI, última sesión, exportación y pulido.

## Pruebas

```bash
python -m pytest tests/ -v
```
