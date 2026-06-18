import { Entity, PrimaryColumn, Column, CreateDateColumn } from 'typeorm';

@Entity('cognize_events')
export class CognizeEventEntity {
  @PrimaryColumn('uuid')
  event_id: string;

  @Column()
  session_id: string;

  @Column({ type: 'timestamptz' })
  timestamp: Date;

  @Column({ type: 'text', nullable: true })
  raw_text?: string;

  @Column({ nullable: true })
  intent?: string;

  @Column({ type: 'float', nullable: true })
  intent_confidence?: number;

  @Column({ nullable: true })
  sentiment?: string;

  @Column({ type: 'float', nullable: true })
  sentiment_score?: number;

  @Column({ nullable: true })
  emotion?: string;

  @Column({ type: 'text', nullable: true })
  generated_response?: string;

  @CreateDateColumn()
  created_at: Date;
}
