import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, Index } from 'typeorm';

export enum TransferStatus {
  PENDING = 'pending',
  IN_TRANSIT = 'in_transit',
  RECEIVED = 'received',
  CANCELLED = 'cancelled',
}

export interface TransferItem {
  productId: string;
  quantity: number;
  receivedQuantity?: number;
}

@Entity('stock_transfers')
@Index(['companyId'])
@Index(['fromWarehouseId', 'toWarehouseId'])
export class StockTransfer {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  companyId: string;

  @Column()
  fromWarehouseId: string;

  @Column()
  toWarehouseId: string;

  @Column({ type: 'json' })
  items: TransferItem[];

  @Column({ type: 'varchar', enum: TransferStatus, default: TransferStatus.PENDING })
  status: TransferStatus;

  @Column({ nullable: true })
  referenceNumber?: string;

  @CreateDateColumn()
  createdAt: Date;

  @Column({ nullable: true })
  completedAt?: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
