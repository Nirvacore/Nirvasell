import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, Index } from 'typeorm';

export enum CycleCountStatus {
  ACTIVE = 'active',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
}

export interface CountItem {
  productId: string;
  systemQuantity: number;
  physicalQuantity?: number;
  variance?: number;
}

@Entity('cycle_counts')
@Index(['companyId', 'warehouseId'])
export class CycleCount {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  companyId: string;

  @Column()
  warehouseId: string;

  @Column({ type: 'json' })
  items: CountItem[];

  @Column({ type: 'varchar', enum: CycleCountStatus, default: CycleCountStatus.ACTIVE })
  status: CycleCountStatus;

  @CreateDateColumn()
  createdAt: Date;

  @Column({ nullable: true })
  completedAt?: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
