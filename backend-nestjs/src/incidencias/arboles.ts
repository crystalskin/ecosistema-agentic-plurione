export interface Opcion {
  texto: string;
  siguiente?: string;
  accion?: 'resolver' | 'escalar' | 'abandonar';
}

export interface Paso {
  mensaje: string;
  opciones: Opcion[];
}

export interface Arbol {
  nombre: string;
  trigger_intents: string[];   // Labels de M1 (BART) que activan este árbol
  pasos: Record<string, Paso>;
}

export const ARBOLES: Record<string, Arbol> = {

  tarjeta_bancaria: {
    nombre: 'Problema con tarjeta',
    trigger_intents: ['problema_tarjeta_bancaria'],
    pasos: {
      inicio: {
        mensaje: 'Puedo ayudarte con tu tarjeta. ¿Cuál es tu situación?',
        opciones: [
          { texto: 'Mi tarjeta está bloqueada', siguiente: 'bloqueada' },
          { texto: 'Perdí mi tarjeta o me la robaron', siguiente: 'perdida' },
          { texto: 'Quiero cancelar mi tarjeta', siguiente: 'cancelar' },
          { texto: 'Prefiero escribir libremente', accion: 'abandonar' },
        ],
      },
      bloqueada: {
        mensaje: '¿Sabes por qué fue bloqueada tu tarjeta?',
        opciones: [
          { texto: 'Intenté el PIN varias veces', siguiente: 'bloqueada_instrucciones' },
          { texto: 'Fue bloqueada por actividad sospechosa', siguiente: 'bloqueada_instrucciones' },
          { texto: 'No sé el motivo', siguiente: 'bloqueada_instrucciones' },
          { texto: 'Prefiero hablar con un agente', accion: 'escalar' },
        ],
      },
      bloqueada_instrucciones: {
        mensaje:
          'Para reactivar tu tarjeta bloqueada:\n' +
          '1. Llama al 800-123-4567 (24/7, sin costo)\n' +
          '2. O visita cualquier sucursal con tu identificación oficial\n' +
          '¿Pudiste resolver tu problema?',
        opciones: [
          { texto: 'Sí, mi problema fue resuelto', accion: 'resolver' },
          { texto: 'No, necesito más ayuda', accion: 'escalar' },
        ],
      },
      perdida: {
        mensaje:
          'Es importante bloquear tu tarjeta de inmediato para evitar cargos no reconocidos.\n' +
          'Llama ahora al 800-123-4567 para reportar la pérdida. ¿Pudiste hacer el reporte?',
        opciones: [
          { texto: 'Sí, ya la reporté y bloqueé', siguiente: 'perdida_reportada' },
          { texto: 'No puedo llamar ahora', accion: 'escalar' },
          { texto: 'Necesito otro método para reportar', accion: 'escalar' },
        ],
      },
      perdida_reportada: {
        mensaje:
          'Tu tarjeta fue bloqueada exitosamente. Recibirás una tarjeta de reemplazo en 5-7 días hábiles.\n' +
          '¿Hay algo más en lo que pueda ayudarte?',
        opciones: [
          { texto: 'No, era todo. Gracias', accion: 'resolver' },
          { texto: 'Sí, tengo otra consulta', accion: 'abandonar' },
        ],
      },
      cancelar: {
        mensaje:
          'Para cancelar tu tarjeta permanentemente debes comunicarte directamente con tu banco por seguridad:\n' +
          '• Llama al 800-123-4567\n' +
          '• O visita tu sucursal más cercana con tu INE\n' +
          '¿Puedo ayudarte con algo más?',
        opciones: [
          { texto: 'Entendido, gracias', accion: 'resolver' },
          { texto: 'Necesito asistencia adicional', accion: 'escalar' },
        ],
      },
    },
  },

  fallo_tecnico: {
    nombre: 'Fallo técnico en la aplicación',
    trigger_intents: ['fallo_tecnico'],
    pasos: {
      inicio: {
        mensaje: 'Entiendo que hay un problema técnico. ¿Qué está pasando exactamente?',
        opciones: [
          { texto: 'No puedo realizar un pago', siguiente: 'pago_fallido' },
          { texto: 'La aplicación no carga o se cierra', siguiente: 'app_caida' },
          { texto: 'No puedo iniciar sesión en mi cuenta', siguiente: 'sesion_cerrada' },
          { texto: 'Prefiero describir el problema', accion: 'abandonar' },
        ],
      },
      pago_fallido: {
        mensaje: '¿Con qué método de pago estás teniendo el problema?',
        opciones: [
          { texto: 'Tarjeta de débito o crédito', siguiente: 'pago_instrucciones' },
          { texto: 'Transferencia bancaria', siguiente: 'pago_instrucciones' },
          { texto: 'Pago en efectivo en tienda', siguiente: 'pago_efectivo' },
          { texto: 'Otro método', accion: 'escalar' },
        ],
      },
      pago_instrucciones: {
        mensaje:
          'Pasos para resolver el fallo de pago:\n' +
          '1. Verifica que los datos de tu tarjeta sean correctos\n' +
          '2. Confirma que tu tarjeta tiene fondos y no tiene restricciones para compras en línea\n' +
          '3. Intenta con otra red (WiFi / datos móviles)\n' +
          '4. Borra el caché de la app y reintenta\n' +
          '¿El problema fue resuelto?',
        opciones: [
          { texto: 'Sí, ya pude realizar el pago', accion: 'resolver' },
          { texto: 'El problema persiste', accion: 'escalar' },
        ],
      },
      pago_efectivo: {
        mensaje:
          'Para pagos en efectivo: genera un nuevo comprobante desde la app.\n' +
          'Preséntalo en cualquier tienda afiliada. El comprobante tiene validez de 24 horas.\n' +
          '¿Pudiste generar el comprobante?',
        opciones: [
          { texto: 'Sí, ya lo generé', accion: 'resolver' },
          { texto: 'No puedo generarlo desde la app', accion: 'escalar' },
        ],
      },
      app_caida: {
        mensaje:
          'Prueba estos pasos en orden:\n' +
          '1. Cierra completamente la app y vuelve a abrirla\n' +
          '2. Verifica tu conexión a internet\n' +
          '3. Actualiza la app desde la tienda si hay actualizaciones\n' +
          '4. Si nada funciona, desinstala y reinstala la app\n' +
          '¿Se resolvió el problema?',
        opciones: [
          { texto: 'Sí, la app ya funciona', accion: 'resolver' },
          { texto: 'El problema continúa después de los pasos', accion: 'escalar' },
        ],
      },
      sesion_cerrada: {
        mensaje:
          'Para recuperar acceso a tu cuenta:\n' +
          '1. En la pantalla de login, selecciona "¿Olvidaste tu contraseña?"\n' +
          '2. Ingresa tu correo registrado\n' +
          '3. Recibirás un enlace de recuperación en tu email\n' +
          '¿Pudiste recuperar el acceso?',
        opciones: [
          { texto: 'Sí, ya tengo acceso', accion: 'resolver' },
          { texto: 'No recibo el correo de recuperación', accion: 'escalar' },
          { texto: 'No recuerdo mi correo registrado', accion: 'escalar' },
        ],
      },
    },
  },

};
