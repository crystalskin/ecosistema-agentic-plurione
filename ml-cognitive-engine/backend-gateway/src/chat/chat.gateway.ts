import { WebSocketGateway, SubscribeMessage, MessageBody, WebSocketServer, ConnectedSocket } from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';
import { CognitiveService } from '../cognitive/cognitive.service';

// @WebSocketGateway() abre el puerto por defecto de WebSockets
// cors: true es VITAL para que nuestro navegador o React pueda conectarse sin ser rechazado
@WebSocketGateway({ cors: true })
export class ChatGateway {
  
  @WebSocketServer()
  server: Server;

  // Inyectamos nuestro servicio de IA que ya funciona
  constructor(private readonly cognitiveService: CognitiveService) {}

  // Este método se ejecuta cuando alguien abre el chat
  handleConnection(client: Socket) {
    console.log(`[Socket] Cliente conectado: ${client.id}`);
  }

  // Este método se ejecuta cuando alguien cierra el chat
  handleDisconnect(client: Socket) {
    console.log(`[Socket] Cliente desconectado: ${client.id}`);
  }

  // Escuchamos el evento 'user_message' que vendrá desde el Frontend
  @SubscribeMessage('user_message')
  async handleUserMessage(
    @MessageBody() payload: { text: string; session_id: string },
    @ConnectedSocket() client: Socket,
  ) {
    console.log(`[Socket] Mensaje recibido: "${payload.text}"`);

    try {
      // 1. Le pedimos a nuestro servicio existente que analice el texto y lo guarde en BD
      const aiAnalysis = await this.cognitiveService.analyzeText(payload.text, payload.session_id);

      // 2. Le enviamos la respuesta de vuelta AL CLIENTE que lo envió
      client.emit('ai_response', {
        status: 'success',
        data: aiAnalysis
      });

    } catch (error) {
      // Si la IA falla, le enviamos un error al cliente
      client.emit('ai_response', {
        status: 'error',
        message: 'La IA no pudo procesar el mensaje'
      });
    }
  }
}