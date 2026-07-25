import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, Index } from 'typeorm';

export enum AdjustmentReason {
  DAMAGE = 'damage',
  THEFT = 'theft',
  SHRINKAGE = 'shrinkage',
  VARIANCE = 'variance',
  OTHER = 'other',
}

@Entity('adjustment_records')
@Index(['companyId', 'warehouseId'])
@Index(['productId'])
export class AdjustmentRecord {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  companyId: string;

  @Column()
  warehouseId: string;

  @Column()
  productId: string;

  @Column({ type: 'integer' })
  quantity: number; // Negative or positive

  @Column({ type: 'varchar', enum: AdjustmentReason })
  reason: AdjustmentReason;

  @Column({ nullable: true })
  notes?: string;

  @CreateDateColumn()
  createdAt: Date;
}
