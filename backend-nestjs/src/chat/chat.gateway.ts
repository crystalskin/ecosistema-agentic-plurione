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

@WebSocketGateway({ cors: { origin: '*' } })
export class ChatGateway implements OnGatewayInit, OnGatewayConnection, OnGatewayDisconnect {
  @WebSocketServer()
  server!: Server;

  constructor(
    private readonly cognitiveService: CognitiveService,
    private readonly escalamientoService: EscalamientoService,
  ) {}

  afterInit() {
    console.log('[ChatGateway] WebSocket Socket.io inicializado');
  }

  handleConnection(client: Socket) {
    console.log(`[ChatGateway] Cliente conectado: ${client.id}`);
  }

  handleDisconnect(client: Socket) {
    console.log(`[ChatGateway] Cliente desconectado: ${client.id}`);
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
      const result = await this.cognitiveService.procesarYGuardar(body.text, body.session_id);
      client.emit('ai_response', { status: 'success', data: result });

      // Escalamiento: negative + (frustracion o score alto)
      const sentiment = result?.payload?.sentiment;
      if (
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
}
