import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, Index } from 'typeorm';
import { Decimal } from 'decimal.js';

@Entity('payments')
@Index(['companyId', 'poId'])
@Index(['companyId', 'supplierId'])
@Index(['companyId', 'status'])
export class Payment {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  companyId: string;

  @Column()
  poId: string;

  @Column()
  supplierId: string;

  @Column()
  invoiceNumber: string; // Supplier invoice number

  @Column('decimal', { precision: 12, scale: 2 })
  amount: Decimal;

  @Column()
  paymentType: string; // 'deposit' | 'partial' | 'full' | 'settlement'

  @Column({ nullable: true })
  paymentMethod?: string; // 'bank_transfer' | 'check' | 'cash' | 'credit'

  @Column({ nullable: true })
  referenceNumber?: string; // Transaction/check number

  @Column()
  status: string; // 'pending' | 'processed' | 'failed'

  @Column({ nullable: true })
  dueDate?: Date;

  @Column({ nullable: true })
  paidDate?: Date;

  @Column({ nullable: true })
  notes?: string;

  @CreateDateColumn()
  recordedAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
