import { Controller, Get } from '@nestjs/common';
import { EscalamientoService } from './escalamiento.service';

@Controller('api/escalamientos')
export class EscalamientoController {
  constructor(private readonly service: EscalamientoService) {}

  @Get('metricas')
  async metricas() {
    return this.service.obtenerResumen();
  }
}
