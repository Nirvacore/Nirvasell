import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, Index } from 'typeorm';

@Entity('channel_configs')
@Index(['companyId', 'channel'], { unique: true })
@Index(['companyId', 'isActive'])
export class ChannelConfig {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  companyId: string;

  @Column()
  channel: string; // 'shopee' | 'lazada' | 'tiktok'

  @Column('jsonb')
  credentials: {
    apiKey: string;
    shopId: string;
    sellerId?: string;
    accessToken?: string;
    refreshToken?: string;
  };

  @Column('jsonb', { default: {} })
  settings: {
    enableAutoSync?: boolean;
    syncInterval?: number;
    defaultMargin?: string;
    enableInventoryDistribution?: boolean;
    maxStockPerChannel?: number;
    priceOverride?: string;
    priceRules?: Record<string, any>;
  };

  @Column({ default: true })
  isActive: boolean;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
