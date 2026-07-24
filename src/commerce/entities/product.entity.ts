import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, Index } from 'typeorm';
import { Decimal } from 'decimal.js';

@Entity('products')
@Index(['companyId'])
@Index(['sku'])
export class Product {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  companyId: string;

  @Column()
  name: string;

  @Column({ unique: true })
  sku: string;

  @Column({ nullable: true })
  description?: string;

  @Column('decimal', { precision: 12, scale: 2 })
  cost: Decimal;

  @Column('decimal', { precision: 12, scale: 2 })
  basePrice: Decimal;

  @Column({ default: 0 })
  totalStock: number;

  @Column({ default: true })
  isActive: boolean;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
