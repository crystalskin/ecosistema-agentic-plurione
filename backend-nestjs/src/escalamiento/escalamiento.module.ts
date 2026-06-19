import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { EscalamientoEntity } from './escalamiento.entity';
import { EscalamientoService } from './escalamiento.service';
import { EscalamientoController } from './escalamiento.controller';

@Module({
  imports: [TypeOrmModule.forFeature([EscalamientoEntity])],
  controllers: [EscalamientoController],
  providers: [EscalamientoService],
  exports: [EscalamientoService],
})
export class EscalamientoModule {}
