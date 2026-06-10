import { Module } from '@nestjs/common';
import { ChatGateway } from './chat.gateway';
import { CognitiveModule } from '../cognitive/cognitive.module';

@Module({
  imports: [CognitiveModule], // Importamos el módulo de IA para poder usarlo aquí
  providers: [ChatGateway],
})
export class ChatModule {}