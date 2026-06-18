import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { CognizeEventEntity } from './cognize-event.entity';

@Injectable()
export class MetricsService {
  constructor(
    @InjectRepository(CognizeEventEntity)
    private readonly cognizeRepository: Repository<CognizeEventEntity>,
  ) {}

  async getMetrics() {
    const total = await this.cognizeRepository.count();
    // Ajusta los nombres de columna si tu entidad los tiene diferentes
    const sentimentCounts = await this.cognizeRepository
      .createQueryBuilder('event')
      .select('event.sentiment', 'sentiment')
      .addSelect('COUNT(*)', 'count')
      .groupBy('event.sentiment')
      .getRawMany();

    const intentCounts = await this.cognizeRepository
      .createQueryBuilder('event')
      .select('event.intent', 'intent')
      .addSelect('COUNT(*)', 'count')
      .groupBy('event.intent')
      .getRawMany();

    const avgConfidence = await this.cognizeRepository
      .createQueryBuilder('event')
      .select('AVG(event.intent_confidence)', 'avgConfidence')
      .getRawOne();

    return {
      total,
      sentimentCounts,
      intentCounts,
      avgConfidence: avgConfidence?.avgConfidence || 0,
    };
  }
}