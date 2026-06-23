import { Injectable, OnModuleInit } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { randomUUID } from 'crypto';
import { TicketEntity } from './ticket.entity';

@Injectable()
export class TicketService implements OnModuleInit {
  constructor(
    @InjectRepository(TicketEntity)
    private readonly repo: Repository<TicketEntity>,
  ) {}

  async onModuleInit() {
    await this.repo.query(
      `CREATE SEQUENCE IF NOT EXISTS tickets_folio_seq START WITH 1 INCREMENT BY 1`,
    );
  }

  async obtenerMetricas() {
    const total   = await this.repo.count();
    const abiertos = await this.repo.count({ where: { estado: 'abierto' } });

    const porCategoria = await this.repo
      .createQueryBuilder('t')
      .select('t.categoria', 'categoria')
      .addSelect('COUNT(*)', 'total')
      .groupBy('t.categoria')
      .orderBy('total', 'DESC')
      .getRawMany();

    const porPrioridad = await this.repo
      .createQueryBuilder('t')
      .select('t.prioridad', 'prioridad')
      .addSelect('COUNT(*)', 'total')
      .groupBy('t.prioridad')
      .getRawMany();

    return {
      total,
      abiertos,
      porCategoria: porCategoria.map(r => ({ categoria: r.categoria, count: parseInt(r.total, 10) })),
      porPrioridad: porPrioridad.map(r => ({ prioridad: r.prioridad, count: parseInt(r.total, 10) })),
    };
  }

  async clasificarYGuardar(texto: string): Promise<TicketEntity> {
    const res = await fetch('http://localhost:8000/api/v1/clasificar-ticket', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ texto }),
    });
    if (!res.ok) {
      throw new Error(`FastAPI /clasificar-ticket respondió ${res.status}`);
    }
    const data: { categoria: string; confianza: number; prioridad: string } =
      await res.json();

    const [{ nextval }] = await this.repo.query(
      `SELECT nextval('tickets_folio_seq')::int AS nextval`,
    );
    const folio = `TK-${String(nextval).padStart(5, '0')}`;

    const ticket = this.repo.create({
      id: randomUUID(),
      texto,
      categoria: data.categoria,
      confianza: data.confianza,
      prioridad: data.prioridad,
      estado: 'abierto',
      folio,
    });
    return this.repo.save(ticket);
  }

  async buscarPorFolio(folio: string): Promise<TicketEntity | null> {
    return this.repo.findOne({ where: { folio } });
  }
}
