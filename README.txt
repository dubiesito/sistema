# Base de Datos: BD_MODERNIZACION

## Descripción de Tablas

* **Organos:** Catálogo de dependencias, oficinas o áreas emisoras de resoluciones.
* **Usuario:** Registro de usuarios autorizados. Mapea el `usuario_red` de Windows para autenticación transparente.
* **Documento:** Tabla principal que almacena los metadatos del expediente (número de resolución, tipo, fecha, órgano emisor).
* **Documento_versiones:** Control de versiones e historial de archivos PDF vinculados mediante rutas de red UNC.
* **Bitacora:** Registro de auditoría que guarda cada inserción, modificación o eliminación realizada por los usuarios.
