import { Controller, Post, Get, Query, HttpException, HttpStatus } from '@nestjs/common';
import { CognitiveService } from './cognitive.service';
import { MetricsService } from './metrics.service';

@Controller('api/cognitive')
export class CognitiveController {
  constructor(
    private readonly cognitiveService: CognitiveService,
    private readonly metricsService: MetricsService,
  ) {}

  @Post('process')
  async procesarMensaje(
    @Query('text') text: string,
    @Query('session_id') sessionId: string,
  ) {
    if (!text || !sessionId) {
      throw new HttpException('Faltan parámetros: text y session_id', HttpStatus.BAD_REQUEST);
    }
    return await this.cognitiveService.procesarYGuardar(text, sessionId);
  }

  @Get('metrics')
  async obtenerMetricas() {
    return await this.metricsService.obtenerMetricas();
  }
}
