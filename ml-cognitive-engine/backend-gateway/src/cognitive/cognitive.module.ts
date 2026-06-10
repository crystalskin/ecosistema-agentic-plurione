import { Module } from '@nestjs/common';
import { HttpModule } from '@nestjs/axios';
import { TypeOrmModule } from '@nestjs/typeorm';
import { CognitiveService } from './cognitive.service';
import { CognitiveController } from './cognitive.controller';
import { CognizeEventEntity } from './cognize-event.entity';

@Module({
  imports: [
    HttpModule,
    TypeOrmModule.forFeature([CognizeEventEntity]),
  ],
  controllers: [CognitiveController],
  providers: [CognitiveService],
  exports: [CognitiveService], // <--- ¡AGREGA ESTA LÍNEA! ES LA LLAVE DE LA CAJA FUERTE
})
export class CognitiveModule {}