import { IsString, IsNumber, IsOptional, IsEnum, IsArray, ValidateNested, Min } from 'class-validator';
import { Type } from 'class-transformer';
import { Decimal } from 'decimal.js';

export enum POStatusEnum {
  DRAFT = 'draft',
  SUBMITTED = 'submitted',
  CONFIRMED = 'confirmed',
  SHIPPED = 'shipped',
  RECEIVED = 'received',
  CANCELLED = 'cancelled',
}

export class POItemDto {
  @IsOptional()
  @IsString()
  productId?: string;

  @IsString()
  description: string;

  @IsNumber()
  @Min(1)
  quantity: number;

  @IsString()
  unitPrice: string; // Decimal as string
}

export class CreatePODto {
  @IsString()
  supplierId: string;

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => POItemDto)
  items: POItemDto[];

  @IsOptional()
  @IsString()
  shippingAddress?: string;

  @IsOptional()
  @IsString()
  notes?: string;
}

export class UpdatePOStatusDto {
  @IsEnum(POStatusEnum)
  status: POStatusEnum;
}

export class POResponseDto {
  id: string;
  poNumber: string;
  supplierId: string;
  items: any[];
  totalAmount: Decimal;
  status: string;
  deliveryDate?: Date;
  shippingAddress?: string;
  paymentsMade: number;
  deductedAmount: number;
  createdAt: Date;
  updatedAt: Date;
}
