import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, Index } from 'typeorm';

@Entity('low_stock_alerts')
@Index(['companyId', 'productId'])
export class LowStockAlert {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  companyId: string;

  @Column()
  productId: string;

  @Column({ type: 'integer' })
  threshold: number;

  @Column({ default: true })
  isActive: boolean;

  @Column({ type: 'integer', nullable: true })
  autoReorderQuantity?: number; // Auto-reorder quantity when triggered

  @Column({ nullable: true })
  lastAlertDate?: Date;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
