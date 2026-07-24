import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, Index } from 'typeorm';

@Entity('dashboards')
@Index(['companyId', 'name'])
export class Dashboard {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  companyId: string;

  @Column()
  name: string;

  @Column({ nullable: true })
  description?: string;

  @Column('jsonb')
  kpis: Array<{
    key: string;
    label: string;
    type: 'revenue' | 'growth' | 'retention' | 'margin' | 'custom';
    params?: Record<string, any>;
  }>;

  @Column({ default: true })
  isActive: boolean;

  @Column({ nullable: true })
  lastViewedAt?: Date;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
