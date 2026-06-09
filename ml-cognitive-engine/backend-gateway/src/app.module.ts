import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { CognitiveModule } from './cognitive/cognitive.module'; // <-- AGREGADO

@Module({
  imports: [CognitiveModule], // <-- AGREGADO
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}