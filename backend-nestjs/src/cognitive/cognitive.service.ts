import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { CognizeEventEntity } from './cognize-event.entity';

@Injectable()
export class CognitiveService {
  constructor(
    @InjectRepository(CognizeEventEntity)
    private readonly repo: Repository<CognizeEventEntity>,
  ) {}

  async procesarYGuardar(text: string, sessionId: string): Promise<any> {
    const url = `http://localhost:8000/api/v1/cognize?text=${encodeURIComponent(text)}&session_id=${encodeURIComponent(sessionId)}`;

    const response = await fetch(url, { method: 'POST' });

    if (!response.ok) {
      throw new Error(`FastAPI respondió con ${response.status}: ${await response.text()}`);
    }

    const data = await response.json();

    try {
      const entity = this.repo.create({
        event_id: data.event_id,
        session_id: data.session_id,
        timestamp: new Date(data.timestamp),
        raw_text: data.payload?.raw_text,
        intent: data.payload?.intent?.label,
        intent_confidence: data.payload?.intent?.confidence,
        sentiment: data.payload?.sentiment?.label,
        sentiment_score: data.payload?.sentiment?.score,
        emotion: data.payload?.sentiment?.emotion,
        generated_response: data.payload?.generated_response,
      });
      await this.repo.save(entity);
    } catch (dbError) {
      console.error('[CognitiveService] Error al guardar en BD:', dbError);
    }

    return data;
  }
}
