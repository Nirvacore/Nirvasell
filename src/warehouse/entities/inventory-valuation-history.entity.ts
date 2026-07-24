import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, Index } from 'typeorm';
import { Decimal } from 'decimal.js';

@Entity('inventory_valuation_history')
@Index(['companyId', 'warehouseId', 'productId'])
export class InventoryValuationHistory {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  companyId: string;

  @Column()
  warehouseId: string;

  @Column()
  productId: string;

  @Column({ type: 'integer' })
  quantity: number; // Quantity received/added

  @Column({ type: 'decimal', precision: 12, scale: 2 })
  unitCost: Decimal;

  @Column({ type: 'decimal', precision: 14, scale: 2 })
  totalCost: Decimal; // quantity × unitCost

  @Column({ type: 'integer', default: 0 })
  remainingQuantity: number; // For FIFO tracking

  @CreateDateColumn()
  receivedDate: Date;
}
