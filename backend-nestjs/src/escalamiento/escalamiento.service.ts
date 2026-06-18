import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { randomUUID } from 'crypto';
import { EscalamientoEntity } from './escalamiento.entity';

@Injectable()
export class EscalamientoService {
  constructor(
    @InjectRepository(EscalamientoEntity)
    private readonly repo: Repository<EscalamientoEntity>,
  ) {}

  async registrar(
    session_id: string,
    raw_text: string,
    sentiment_score?: number,
    emotion?: string,
  ): Promise<EscalamientoEntity> {
    const registro = this.repo.create({
      id: randomUUID(),
      session_id,
      raw_text,
      sentiment_score,
      emotion,
      estado: 'pendiente',
    });
    return this.repo.save(registro);
  }
}
