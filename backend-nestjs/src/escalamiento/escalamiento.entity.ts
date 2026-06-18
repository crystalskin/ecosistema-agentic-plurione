import { Entity, PrimaryColumn, Column, CreateDateColumn } from 'typeorm';

@Entity('solicitudes_escalamiento')
export class EscalamientoEntity {
  @PrimaryColumn('uuid')
  id: string;

  @Column()
  session_id: string;

  @Column({ type: 'text' })
  raw_text: string;

  @Column({ type: 'float', nullable: true })
  sentiment_score?: number;

  @Column({ nullable: true })
  emotion?: string;

  @Column({ default: 'pendiente' })
  estado: string;

  @CreateDateColumn()
  created_at: Date;
}
