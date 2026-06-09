import { Entity, Column, PrimaryGeneratedColumn, CreateDateColumn } from 'typeorm';

@Entity('cognize_events') // Este será el nombre de tu tabla en PostgreSQL
export class CognizeEventEntity {
  @PrimaryGeneratedColumn('uuid')
  event_id: string;

  @Column()
  session_id: string;

  @Column({ type: 'text' })
  raw_text: string;

  @Column({ name: 'intent_label' })
  intent_label: string;

  @Column({ type: 'float', name: 'intent_confidence' })
  intent_confidence: number;

  @Column({ name: 'sentiment_label' })
  sentiment_label: string;

  @Column({ type: 'float', name: 'sentiment_score' })
  sentiment_score: number;

  @CreateDateColumn({ type: 'timestamp' })
  timestamp: Date;
}