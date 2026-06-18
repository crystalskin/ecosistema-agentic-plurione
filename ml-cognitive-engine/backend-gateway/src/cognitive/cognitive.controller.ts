import { Controller, Get, Query } from '@nestjs/common';
import { CognitiveService } from './cognitive.service';
import { MetricsService } from './metrics.service';  // importa el nuevo servicio

@Controller('api/cognitive')
export class CognitiveController {
  constructor(
    private readonly cognitiveService: CognitiveService,
    private readonly metricsService: MetricsService,  // inyecta el servicio de métricas
  ) {}

  @Get('analyze')
  async analyze(@Query('text') text: string, @Query('session_id') sessionId: string) {
    return await this.cognitiveService.analyzeText(text, sessionId);
  }

  @Get('metrics')
  async getMetrics() {
    return this.metricsService.getMetrics();
  }
}