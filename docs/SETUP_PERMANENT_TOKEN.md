# Configuración de Token Permanente de WhatsApp API

Este documento guía paso a paso cómo crear un **Usuario del Sistema** y generar un **Token de Acceso Permanente** para evitar que tu bot deje de funcionar cada 24 horas.

## 1. Acceder a la Configuración del Negocio
1. Ve a [Meta Business Suite](https://business.facebook.com/settings/).
2. Selecciona tu negocio en el menú desplegable (si tienes varios).

## 2. Crear un Usuario del Sistema
1. En el menú lateral izquierdo, ve a **Usuarios** > **Usuarios del sistema**.
2. Haz clic en el botón **Agregar**.
3. Asigna un nombre (Ej: `BotSistemaCorrelativo`).
4. En **Rol del usuario del sistema**, selecciona **Administrador**.
5. Haz clic en **Crear usuario del sistema**.
   > **Importante**: Guarda bien el token que se muestra, aunque generaremos uno nuevo a continuación.

## 3. Asignar Activos (Tu App de WhatsApp)
1. Con el nuevo usuario seleccionado, haz clic en **Agregar activos**.
2. Ve a la categoría **Apps**.
3. Selecciona tu aplicación (la que creaste en Meta for Developers).
4. Habilita el permiso **Administrar app** (Control total).
5. Haz clic en **Guardar cambios**.

## 4. Generar el Token Permanente
1. Asegúrate de estar en la vista de tu nuevo **Usuario del Sistema**.
2. Haz clic en el botón **Generar nuevo token**.
3. Selecciona tu **App**.
4. En **Vencimiento del token**, selecciona **Nunca** (o "Permanente").
5. En **Permisos**, debes seleccionar obligatoriamente:
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
6. Haz clic en **Generar token**.

## 5. Guardar y Configurar
1. **Copia el token generado**. Este es tu `WHATSAPP_ACCESS_TOKEN` permanente.
   > ⚠️ **Advertencia**: Meta no volverá a mostrarte este token. Guárdalo en un gestor de contraseñas.
2. Ve a tu dashboard de **Render**.
3. En la sección **Environment**, busca `WHATSAPP_ACCESS_TOKEN`.
4. Haz clic en **Edit** y pega el nuevo token.
5. Guarda los cambios. Render reiniciará tu servicio automáticamente.

## 6. Verificación
Una vez reiniciado el servicio, envía un mensaje de prueba a tu bot para confirmar que sigue respondiendo.
