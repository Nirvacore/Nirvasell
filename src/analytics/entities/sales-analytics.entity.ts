import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, Index } from 'typeorm';
import { Decimal } from 'decimal.js';

@Entity('sales_analytics')
@Index(['companyId', 'dateStart'])
@Index(['companyId', 'channel'])
export class SalesAnalytics {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  companyId: string;

  @Column()
  dateStart: Date;

  @Column()
  dateEnd: Date;

  @Column({ nullable: true })
  channel?: string;

  @Column('decimal', { precision: 14, scale: 2 })
  totalRevenue: Decimal;

  @Column('decimal', { precision: 14, scale: 2 })
  previousRevenue?: Decimal;

  @Column('int')
  orderCount: number;

  @Column('int')
  customerCount: number;

  @Column('decimal', { precision: 12, scale: 2 })
  averageOrderValue: Decimal;

  @Column('jsonb', { nullable: true })
  metadata?: Record<string, any>;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
