import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, Index } from 'typeorm';
import { Decimal } from 'decimal.js';

@Entity('quotations')
@Index(['companyId', 'supplierId'])
@Index(['companyId', 'status'])
@Index(['companyId', 'validUntil'])
export class Quotation {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  companyId: string;

  @Column()
  supplierId: string;

  @Column()
  quotationNumber: string; // Auto-generated

  @Column('jsonb')
  items: Array<{
    description: string;
    quantity: number;
    unitPrice: Decimal | string;
    totalPrice: Decimal | string;
  }>;

  @Column('decimal', { precision: 12, scale: 2 })
  totalAmount: Decimal;

  @Column()
  validUntil: Date;

  @Column()
  status: string; // 'pending' | 'accepted' | 'rejected' | 'expired'

  @Column({ nullable: true })
  acceptedAt?: Date;

  @Column({ nullable: true })
  rejectedAt?: Date;

  @Column({ nullable: true })
  poId?: string; // Reference to converted PO

  @Column({ nullable: true })
  notes?: string;

  @Column({ default: 0 })
  revisionNumber: number;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
