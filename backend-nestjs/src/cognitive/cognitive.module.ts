import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { CognizeEventEntity } from './cognize-event.entity';
import { CognitiveController } from './cognitive.controller';
import { CognitiveService } from './cognitive.service';
import { MetricsService } from './metrics.service';

@Module({
  imports: [TypeOrmModule.forFeature([CognizeEventEntity])],
  controllers: [CognitiveController],
  providers: [CognitiveService, MetricsService],
  exports: [CognitiveService],
})
export class CognitiveModule {}
