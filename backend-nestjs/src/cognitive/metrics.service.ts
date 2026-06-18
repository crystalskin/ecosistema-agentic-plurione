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

    const sentimentCounts = porSentimiento.map(r => ({
      sentiment: r.sentiment ?? 'desconocido',
      count: parseInt(r.total, 10),
    }));

    const intentCounts = porIntencion.map(r => ({
      intent: r.intent ?? 'desconocido',
      count: parseInt(r.total, 10),
      avgConfidence: parseFloat(Number(r.confianza_promedio).toFixed(4)),
    }));

    const totalPonderado = intentCounts.reduce((acc, r) => acc + r.count, 0);
    const avgConfidence =
      totalPonderado > 0
        ? intentCounts.reduce((acc, r) => acc + r.avgConfidence * r.count, 0) / totalPonderado
        : 0;

    return {
      total,
      sentimentCounts,
      intentCounts,
      avgConfidence: parseFloat(avgConfidence.toFixed(4)),
      ultimos,
    };
  }
}
