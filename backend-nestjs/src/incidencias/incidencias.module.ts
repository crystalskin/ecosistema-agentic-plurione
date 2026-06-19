import { Module } from '@nestjs/common';
import { IncidenciasService } from './incidencias.service';

@Module({
  providers: [IncidenciasService],
  exports: [IncidenciasService],
})
export class IncidenciasModule {}
