import { IsString, IsNumber, IsOptional, IsUUID, Min } from 'class-validator';
import { Decimal } from 'decimal.js';

export class SyncProductDto {
  @IsUUID()
  productId: string;

  @IsString()
  price: string; // Decimal as string

  @IsNumber()
  @Min(0)
  stock: number;

  @IsOptional()
  @IsString()
  channelSku?: string;
}

export class UpdateProductPriceDto {
  @IsUUID()
  productId: string;

  @IsString()
  newPrice: string; // Decimal as string

  @Min(0)
  newPrice_numeric?: number;
}

export class UpdateProductStockDto {
  @IsUUID()
  productId: string;

  @IsNumber()
  @Min(0)
  newStock: number;
}

export class DistributeInventoryDto {
  @IsUUID()
  productId: string;

  @IsNumber()
  @Min(0)
  totalStock: number;
}

export class ChannelProductResponseDto {
  id: string;
  productId: string;
  channel: string;
  externalProductId: string;
  price: Decimal;
  stock: number;
  channelSku?: string;
  lastSyncedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export class ChannelInventoryResponseDto {
  products: Array<{
    externalProductId: string;
    price: Decimal;
    stock: number;
    channelSku?: string;
  }>;
  totalSKUs: number;
  lastSyncedAt: Date;
}
