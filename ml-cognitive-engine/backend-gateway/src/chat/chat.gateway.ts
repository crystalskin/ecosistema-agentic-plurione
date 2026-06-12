import { WebSocketGateway, SubscribeMessage, MessageBody, WebSocketServer, ConnectedSocket } from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';
import { CognitiveService } from '../cognitive/cognitive.service';

@WebSocketGateway({ cors: true })
export class ChatGateway {
  
  @WebSocketServer()
  server: Server;

  constructor(private readonly cognitiveService: CognitiveService) {}

  handleConnection(client: Socket) {
    console.log(`[Socket] Cliente conectado: ${client.id}`);
  }

  handleDisconnect(client: Socket) {
    console.log(`[Socket] Cliente desconectado: ${client.id}`);
  }

  @SubscribeMessage('user_message')
  async handleUserMessage(
    @MessageBody() payload: { text: string; session_id: string },
    @ConnectedSocket() client: Socket,
  ) {
    console.log(`[Socket] Mensaje recibido: "${payload.text}"`);

    try {
      const aiAnalysis = await this.cognitiveService.analyzeText(payload.text, payload.session_id);
      client.emit('ai_response', { status: 'success', data: aiAnalysis });
    } catch (error) {
      client.emit('ai_response', { status: 'error', message: 'La IA no pudo procesar el mensaje' });
    }
  }
}