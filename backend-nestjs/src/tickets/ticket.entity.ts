import { Entity, PrimaryColumn, Column, CreateDateColumn } from 'typeorm';

@Entity('tickets_clasificados')
export class TicketEntity {
  @PrimaryColumn('uuid')
  id: string;

  @Column({ type: 'text' })
  texto: string;

  @Column()
  categoria: string;

  @Column({ type: 'float' })
  confianza: number;

  @Column()
  prioridad: string;

  @Column({ default: 'abierto' })
  estado: string;

  @CreateDateColumn()
  created_at: Date;
}
