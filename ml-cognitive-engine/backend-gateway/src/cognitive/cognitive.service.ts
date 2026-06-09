import { Injectable } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { firstValueFrom } from 'rxjs';
import { CognizeEventEntity } from './cognize-event.entity';

@Injectable()
export class CognitiveService {
  constructor(
    private readonly httpService: HttpService,
    @InjectRepository(CognizeEventEntity)
    private readonly eventRepository: Repository<CognizeEventEntity>, // Inyectamos la tabla
  ) {}

  async analyzeText(text: string, sessionId: string) {
    const pythonApiUrl = `http://localhost:8000/api/v1/cognize?text=${encodeURIComponent(text)}&session_id=${sessionId}`;
    
    // 1. Pedimos datos a Python
    const response = await firstValueFrom(this.httpService.post(pythonApiUrl));
    const data = response.data;

    // 2. Mapeamos la respuesta de Python a nuestro formato de Base de Datos
    const newRecord = this.eventRepository.create({
      event_id: data.event_id,
      session_id: data.session_id,
      raw_text: data.payload.raw_text,
      intent_label: data.payload.intent.label,
      intent_confidence: data.payload.intent.confidence,
      sentiment_label: data.payload.sentiment.label,
      sentiment_score: data.payload.sentiment.score,
    });

    // 3. Guardamos en PostgreSQL
    await this.eventRepository.save(newRecord);

    // 4. Devolvemos el dato original al usuario
    return data;
  }
}