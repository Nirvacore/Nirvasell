import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, Index } from 'typeorm';
import { Decimal } from 'decimal.js';

@Entity('channel_products')
@Index(['companyId', 'productId', 'channel'], { unique: true })
@Index(['companyId', 'channel'])
@Index(['externalProductId', 'channel'])
export class ChannelProduct {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  companyId: string;

  @Column()
  productId: string;

  @Column()
  channel: string; // 'shopee' | 'lazada' | 'tiktok'

  @Column()
  externalProductId: string;

  @Column({ nullable: true })
  channelSku?: string;

  @Column('decimal', { precision: 12, scale: 2 })
  price: Decimal;

  @Column()
  stock: number;

  @Column({ nullable: true })
  lastSyncedAt?: Date;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
