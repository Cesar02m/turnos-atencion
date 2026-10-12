# Turnos de atención

Demo académica de una fila de atención con backend Flask y frontend Angular. La interfaz usa una identidad visual bancaria en azul, sin utilizar logotipos oficiales.

## Funciones

- Generar turnos secuenciales (`A01`, `A02`, …).
- Asignar el siguiente turno a cualquiera de las cuatro ventanillas disponibles.
- Marcar una ventanilla como ocupada durante la atención y liberarla al finalizar.
- Mostrar la fila y el turno llamado en una pantalla que se actualiza cada 2.5 segundos.
- Mostrar en una sola vista el turno llamado y su mesa asignada, la disponibilidad y ocupación de las cuatro mesas, la fila de espera, las esperas estimadas y los controles para llamar o finalizar turnos.
- Calcular la espera estimada usando un promedio inicial de 8 minutos por atención; el valor se puede ajustar en `frontend/src/app/app.ts`.
- Reproducir un tono cuando se llama a un turno (el navegador puede requerir una primera interacción para habilitar sonido).

## Ejecutar en local

1. Instala dependencias con `npm install` y `python -m pip install -r requirements.txt`.
2. Inicia la API Flask desde la raíz con `python -m flask --app api.index run --debug --port 5000`.
3. En otra terminal, inicia Angular con `npm start`.

Para desarrollo local, configura el proxy de Angular o cambia temporalmente las rutas de API para que apunten a `http://localhost:5000`. Los datos locales se guardan en `api/turnos.db`.

## Publicar

El proyecto incluye `vercel.json` para compilar Angular y enrutar `/api/*` al backend Flask como una función Python. En Vercel la base SQLite vive en `/tmp` y es efímera: sirve para una demostración, pero puede reiniciarse entre instancias o despliegues. Para operación compartida persistente, configura `QUEUE_DB_PATH` con un volumen persistente o adapta el almacenamiento a una base de datos administrada.

## Uso

Abre la página en una pantalla para observar el panel. Desde la misma interfaz puedes generar turnos y operar las cuatro ventanillas. El estado se comparte mediante la API mientras corre el mismo proceso con su base de datos.

