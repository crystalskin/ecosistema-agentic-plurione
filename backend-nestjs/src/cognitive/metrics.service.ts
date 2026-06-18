import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { CognizeEventEntity } from './cognize-event.entity';

@Injectable()
export class MetricsService {
  constructor(
    @InjectRepository(CognizeEventEntity)
    private readonly repo: Repository<CognizeEventEntity>,
  ) {}

  async obtenerMetricas() {
    const total = await this.repo.count();

    const porSentimiento = await this.repo
      .createQueryBuilder('e')
      .select('e.sentiment', 'sentiment')
      .addSelect('COUNT(*)', 'total')
      .groupBy('e.sentiment')
      .getRawMany();

    const porIntencion = await this.repo
      .createQueryBuilder('e')
      .select('e.intent', 'intent')
      .addSelect('COUNT(*)', 'total')
      .addSelect('AVG(e.intent_confidence)', 'confianza_promedio')
      .groupBy('e.intent')
      .orderBy('total', 'DESC')
      .getRawMany();

    const ultimos = await this.repo.find({
      order: { created_at: 'DESC' },
      take: 20,
    });

    return { total, porSentimiento, porIntencion, ultimos };
  }
}
