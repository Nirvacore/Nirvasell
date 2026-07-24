import { IsString, IsNumber, IsOptional, IsArray, IsDateString, IsEnum, Min, ValidateNested } from 'class-validator';
import { Type } from 'class-transformer';
import { Decimal } from 'decimal.js';

export enum OrderStatusEnum {
  PENDING = 'pending',
  CONFIRMED = 'confirmed',
  SHIPPED = 'shipped',
  DELIVERED = 'delivered',
  CANCELLED = 'cancelled',
}

export class OrderItemDto {
  @IsString()
  externalProductId: string;

  @IsNumber()
  @Min(1)
  quantity: number;

  @IsString()
  price: string; // Decimal as string
}

export class ImportOrderDto {
  @IsString()
  externalOrderId: string;

  @IsString()
  buyerName: string;

  @IsOptional()
  @IsString()
  buyerPhone?: string;

  @IsString()
  deliveryAddress: string;

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => OrderItemDto)
  items: OrderItemDto[];

  @IsString()
  totalPrice: string; // Decimal as string

  @IsDateString()
  orderDate: string;

  @IsEnum(OrderStatusEnum)
  status: OrderStatusEnum;
}

export class UpdateOrderStatusDto {
  @IsString()
  orderId: string;

  @IsEnum(OrderStatusEnum)
  status: OrderStatusEnum;
}

export class OrderResponseDto {
  id: string;
  companyId: string;
  channel: string;
  externalOrderId: string;
  buyerName: string;
  buyerPhone?: string;
  deliveryAddress: string;
  items: Array<{
    externalProductId: string;
    quantity: number;
    price: Decimal | string;
  }>;
  totalPrice: Decimal;
  status: string;
  orderDate: Date;
  lastSyncedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export class ChannelOrdersResponseDto {
  orders: OrderResponseDto[];
  total: number;
  limit: number;
  offset: number;
}
