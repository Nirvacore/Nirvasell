import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, Index, ManyToOne, JoinColumn } from 'typeorm';
import { Decimal } from 'decimal.js';
import { Supplier } from './supplier.entity';

@Entity('purchase_orders')
@Index(['companyId', 'supplierId'])
@Index(['companyId', 'status'])
@Index(['companyId', 'createdAt'])
export class PurchaseOrder {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  companyId: string;

  @Column()
  supplierId: string;

  @ManyToOne(() => Supplier)
  @JoinColumn({ name: 'supplierId' })
  supplier: Supplier;

  @Column()
  poNumber: string; // Auto-generated PO number

  @Column('jsonb')
  items: Array<{
    productId?: string;
    description: string;
    quantity: number;
    unitPrice: Decimal | string;
    totalPrice: Decimal | string;
  }>;

  @Column('decimal', { precision: 12, scale: 2 })
  totalAmount: Decimal;

  @Column()
  status: string; // 'draft' | 'submitted' | 'confirmed' | 'shipped' | 'received' | 'cancelled'

  @Column({ nullable: true })
  deliveryDate?: Date;

  @Column({ nullable: true })
  shippingAddress?: string;

  @Column({ nullable: true })
  notes?: string;

  @Column({ default: 0 })
  paymentsMade: number; // Total amount paid

  @Column({ default: 0 })
  deductedAmount: number; // Tax or other deductions

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
