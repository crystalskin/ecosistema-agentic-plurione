import {
  WebSocketGateway,
  WebSocketServer,
  SubscribeMessage,
  MessageBody,
  ConnectedSocket,
  OnGatewayInit,
  OnGatewayConnection,
  OnGatewayDisconnect,
} from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';
import { CognitiveService } from '../cognitive/cognitive.service';
import { EscalamientoService } from '../escalamiento/escalamiento.service';
import { IncidenciasService } from '../incidencias/incidencias.service';

@WebSocketGateway({ cors: { origin: '*' } })
export class ChatGateway implements OnGatewayInit, OnGatewayConnection, OnGatewayDisconnect {
  @WebSocketServer()
  server!: Server;

  private readonly sessionMap = new Map<string, string>(); // socketId → sessionId

  constructor(
    private readonly cognitiveService: CognitiveService,
    private readonly escalamientoService: EscalamientoService,
    private readonly incidenciasService: IncidenciasService,
  ) {}

  afterInit() {
    console.log('[ChatGateway] WebSocket Socket.io inicializado');
  }

  handleConnection(client: Socket) {
    console.log(`[ChatGateway] Cliente conectado: ${client.id}`);
  }

  handleDisconnect(client: Socket) {
    console.log(`[ChatGateway] Cliente desconectado: ${client.id}`);
    const sessionId = this.sessionMap.get(client.id);
    if (sessionId) {
      this.cognitiveService.limpiarSesion(sessionId).catch(() => {});
      this.sessionMap.delete(client.id);
    }
  }

  @SubscribeMessage('request_human')
  async handleRequestHuman(
    @MessageBody() body: { session_id: string; raw_text: string; sentiment_score?: number; emotion?: string },
    @ConnectedSocket() client: Socket,
  ) {
    console.log(`[ChatGateway] ESCALAMIENTO confirmado | session=${body.session_id}`);
    try {
      await this.escalamientoService.registrar(
        body.session_id,
        body.raw_text,
        body.sentiment_score,
        body.emotion,
      );
      console.log(`[ChatGateway] Escalamiento guardado en BD para session=${body.session_id}`);
    } catch (err) {
      console.error(`[ChatGateway] Error al guardar escalamiento:`, err);
    }
    client.emit('transfer_confirmed', {
      message: 'Tu solicitud fue recibida. Un agente humano se comunicará contigo pronto.',
    });
  }

  @SubscribeMessage('user_message')
  async handleUserMessage(
    @MessageBody() body: { text: string; session_id: string },
    @ConnectedSocket() client: Socket,
  ) {
    try {
      console.log(`[ChatGateway] Mensaje recibido de ${client.id}: "${body.text}"`);
      this.sessionMap.set(client.id, body.session_id);

      // M3: si hay flujo guiado activo y el usuario escribe texto libre → abandonar el flujo
      if (this.incidenciasService.tieneFlujActivo(body.session_id)) {
        this.incidenciasService.limpiarFlujo(body.session_id);
        client.emit('flujo_completado', {
          resultado: 'abandonado',
          mensaje: 'Flujo de guía cancelado. Puedes escribirme libremente.',
        });
      }

      const result = await this.cognitiveService.procesarYGuardar(body.text, body.session_id);
      client.emit('ai_response', { status: 'success', data: result });

      const intent = result?.payload?.intent?.label;
      const confidence: number = result?.payload?.intent?.confidence ?? 0;
      const sentiment = result?.payload?.sentiment;

      // M3: intentar iniciar flujo guiado si hay árbol para este intent
      let inicioFlujo = false;
      if (intent && intent !== 'rag_directo' && confidence >= this.incidenciasService.confidenceThreshold) {
        const incidenciaId = this.incidenciasService.encontrarArbol(intent);
        if (incidenciaId) {
          const primerPaso = this.incidenciasService.iniciarFlujo(body.session_id, incidenciaId);
          client.emit('opciones_guiadas', primerPaso);
          inicioFlujo = true;
          console.log(`[ChatGateway] Flujo guiado iniciado: ${incidenciaId} | session=${body.session_id}`);
        }
      }

      // M5: escalamiento por frustración — omitir si ya iniciamos flujo guiado
      if (
        !inicioFlujo &&
        sentiment?.label === 'negative' &&
        (sentiment.emotion === 'frustracion' || sentiment.score > 0.8)
      ) {
        console.log(
          `[ChatGateway] ESCALAMIENTO | emotion=${sentiment.emotion} | score=${sentiment.score}`,
        );
        client.emit('escalate_human', {
          session_id: body.session_id,
          message: body.text,
          emotion: sentiment.emotion,
          score: sentiment.score,
        });
      }
    } catch (error) {
      console.error(`[ChatGateway] Error procesando mensaje:`, error);
      client.emit('ai_response', { status: 'error', message: String(error) });
    }
  }

  @SubscribeMessage('respuesta_guiada')
  handleRespuestaGuiada(
    @MessageBody() body: { session_id: string; opcionTexto: string },
    @ConnectedSocket() client: Socket,
  ) {
    console.log(
      `[ChatGateway] Respuesta guiada | session=${body.session_id} | opcion="${body.opcionTexto}"`,
    );
    const resultado = this.incidenciasService.procesarRespuesta(body.session_id, body.opcionTexto);

    if (resultado.paso) {
      client.emit('opciones_guiadas', resultado.paso);
    } else if (resultado.accion === 'resolver') {
      client.emit('flujo_completado', {
        resultado: 'resuelto',
        mensaje: '¡Nos alegra que hayas podido resolver tu problema! ¿Puedo ayudarte con algo más?',
      });
    } else if (resultado.accion === 'escalar') {
      // Reutilizar el flujo M5 existente — el frontend ya sabe manejarlo
      client.emit('escalate_human', {
        session_id: body.session_id,
        message: 'Escalado desde flujo de resolución de incidencias.',
        emotion: 'frustracion',
        score: 0.9,
      });
    } else {
      // abandonar
      client.emit('flujo_completado', {
        resultado: 'abandonado',
        mensaje: 'De acuerdo, puedes escribirme directamente.',
      });
    }
  }
}
