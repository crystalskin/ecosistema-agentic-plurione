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

@WebSocketGateway({ cors: { origin: '*' } })
export class ChatGateway implements OnGatewayInit, OnGatewayConnection, OnGatewayDisconnect {
  @WebSocketServer()
  server: Server;

  constructor(private readonly cognitiveService: CognitiveService) {}

  afterInit() {
    console.log('[ChatGateway] WebSocket Socket.io inicializado');
  }

  handleConnection(client: Socket) {
    console.log(`[ChatGateway] Cliente conectado: ${client.id}`);
  }

  handleDisconnect(client: Socket) {
    console.log(`[ChatGateway] Cliente desconectado: ${client.id}`);
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
    } catch (error) {
      console.error(`[ChatGateway] Error procesando mensaje:`, error);
      client.emit('ai_response', { status: 'error', message: String(error) });
    }
  }
}
