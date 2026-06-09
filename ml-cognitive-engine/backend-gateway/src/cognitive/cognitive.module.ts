import { Module } from '@nestjs/common';
import { HttpModule } from '@nestjs/axios';
import { TypeOrmModule } from '@nestjs/typeorm';
import { CognitiveService } from './cognitive.service';
import { CognitiveController } from './cognitive.controller';
import { CognizeEventEntity } from './cognize-event.entity';

@Module({
  imports: [
    HttpModule,
    TypeOrmModule.forFeature([CognizeEventEntity]), // <- AGREGADO
  ],
  controllers: [CognitiveController],
  providers: [CognitiveService],
})
export class CognitiveModule {}