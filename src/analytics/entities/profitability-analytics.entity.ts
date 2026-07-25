import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, Index } from 'typeorm';
import { Decimal } from 'decimal.js';

@Entity('profitability_analytics')
@Index(['companyId', 'dateStart'])
@Index(['companyId', 'channel'])
@Index(['companyId', 'productId'])
export class ProfitabilityAnalytics {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  companyId: string;

  @Column()
  dateStart: Date;

  @Column()
  dateEnd: Date;

  @Column({ nullable: true })
  productId?: string;

  @Column({ nullable: true })
  channel?: string;

  @Column('decimal', { precision: 14, scale: 2 })
  revenue: Decimal;

  @Column('decimal', { precision: 14, scale: 2 })
  costOfGoodsSold: Decimal;

  @Column('decimal', { precision: 14, scale: 2 })
  operatingExpenses: Decimal;

  @Column('decimal', { precision: 14, scale: 2 })
  grossProfit: Decimal;

  @Column('decimal', { precision: 14, scale: 2 })
  netProfit: Decimal;

  @Column('decimal', { precision: 5, scale: 2 })
  grossMargin: Decimal;

  @Column('decimal', { precision: 5, scale: 2 })
  netMargin: Decimal;

  @Column('decimal', { precision: 14, scale: 2 })
  breakEvenPoint?: Decimal;

  @Column('jsonb', { nullable: true })
  metadata?: Record<string, any>;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
