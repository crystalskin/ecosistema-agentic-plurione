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
    const saved = await this.repo.save(registro);

    // Publicar en RabbitMQ vía FastAPI (best-effort: fallo aquí no cancela el registro en BD)
    try {
      const res = await fetch('http://localhost:8000/api/v1/escalate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id, raw_text, emotion, sentiment_score }),
      });
      if (!res.ok) {
        console.warn(`[EscalamientoService] FastAPI /escalate respondió ${res.status}`);
      }
    } catch (e) {
      console.warn('[EscalamientoService] No se pudo publicar en RabbitMQ:', e);
    }

    return saved;
  }
}
