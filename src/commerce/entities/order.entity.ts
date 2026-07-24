import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, Index } from 'typeorm';
import { Decimal } from 'decimal.js';

@Entity('orders')
@Index(['companyId', 'channel'])
@Index(['companyId', 'status'])
@Index(['companyId', 'externalOrderId', 'channel'], { unique: true })
export class Order {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  companyId: string;

  @Column()
  channel: string; // 'shopee' | 'lazada' | 'tiktok'

  @Column()
  externalOrderId: string;

  @Column()
  buyerName: string;

  @Column({ nullable: true })
  buyerPhone?: string;

  @Column()
  deliveryAddress: string;

  @Column('jsonb')
  items: Array<{
    externalProductId: string;
    quantity: number;
    price: Decimal | string;
  }>;

  @Column('decimal', { precision: 12, scale: 2 })
  totalPrice: Decimal;

  @Column()
  status: string; // 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled'

  @Column()
  orderDate: Date;

  @Column({ nullable: true })
  lastSyncedAt?: Date;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
