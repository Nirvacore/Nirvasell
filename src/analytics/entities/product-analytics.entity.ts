import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, Index } from 'typeorm';
import { Decimal } from 'decimal.js';

@Entity('product_analytics')
@Index(['companyId', 'productId'])
@Index(['companyId', 'rank'])
export class ProductAnalytics {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  companyId: string;

  @Column()
  productId: string;

  @Column()
  productName: string;

  @Column('decimal', { precision: 14, scale: 2 })
  totalRevenue: Decimal;

  @Column('decimal', { precision: 14, scale: 2 })
  totalCost: Decimal;

  @Column('decimal', { precision: 14, scale: 2 })
  totalProfit: Decimal;

  @Column('decimal', { precision: 5, scale: 2 })
  profitMargin: Decimal;

  @Column('decimal', { precision: 5, scale: 2 })
  revenueContribution: Decimal;

  @Column('int')
  unitsSold: number;

  @Column('int')
  unitsInStock: number;

  @Column('int')
  rank?: number;

  @Column('decimal', { precision: 12, scale: 2 })
  averagePrice: Decimal;

  @Column('int')
  daysSinceLastSale?: number;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
