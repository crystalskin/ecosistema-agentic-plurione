import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { EscalamientoEntity } from './escalamiento.entity';
import { EscalamientoService } from './escalamiento.service';

@Module({
  imports: [TypeOrmModule.forFeature([EscalamientoEntity])],
  providers: [EscalamientoService],
  exports: [EscalamientoService],
})
export class EscalamientoModule {}
