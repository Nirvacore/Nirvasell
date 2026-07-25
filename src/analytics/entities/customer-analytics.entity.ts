import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, Index } from 'typeorm';
import { Decimal } from 'decimal.js';

@Entity('customer_analytics')
@Index(['companyId', 'customerId'])
@Index(['companyId', 'cohortMonth'])
export class CustomerAnalytics {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  companyId: string;

  @Column()
  customerId: string;

  @Column('decimal', { precision: 14, scale: 2 })
  lifetimeValue: Decimal;

  @Column('decimal', { precision: 5, scale: 2 })
  retentionRate: Decimal;

  @Column('decimal', { precision: 5, scale: 2 })
  churnRate: Decimal;

  @Column('int')
  totalPurchases: number;

  @Column('int')
  repeatPurchases: number;

  @Column({ nullable: true })
  firstPurchaseDate?: Date;

  @Column({ nullable: true })
  lastPurchaseDate?: Date;

  @Column({ nullable: true })
  cohortMonth?: string; // YYYY-MM format

  @Column('decimal', { precision: 5, scale: 2 })
  averagePurchaseFrequency: Decimal;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
