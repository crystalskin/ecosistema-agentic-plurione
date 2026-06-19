import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { randomUUID } from 'crypto';
import { TicketEntity } from './ticket.entity';

@Injectable()
export class TicketService {
  constructor(
    @InjectRepository(TicketEntity)
    private readonly repo: Repository<TicketEntity>,
  ) {}

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

    const ticket = this.repo.create({
      id: randomUUID(),
      texto,
      categoria: data.categoria,
      confianza: data.confianza,
      prioridad: data.prioridad,
      estado: 'abierto',
    });
    return this.repo.save(ticket);
  }
}
