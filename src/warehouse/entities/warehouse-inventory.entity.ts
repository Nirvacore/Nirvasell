import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, Index } from 'typeorm';
import { Decimal } from 'decimal.js';

@Entity('warehouse_inventory')
@Index(['companyId', 'warehouseId'])
@Index(['productId'])
export class WarehouseInventory {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  companyId: string;

  @Column()
  warehouseId: string;

  @Column()
  productId: string;

  @Column({ type: 'integer', default: 0 })
  quantity: number;

  @Column({ type: 'decimal', precision: 12, scale: 2, default: 0 })
  unitCost: Decimal;

  @Column({ nullable: true })
  shelf?: string; // Physical location in warehouse (e.g., "A-1-3")

  @Column({ default: false })
  isLocked: boolean; // Locked for transfers

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
