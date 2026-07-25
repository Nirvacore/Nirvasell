import { IsString, IsOptional, IsEnum, Min } from 'class-validator';
import { Decimal } from 'decimal.js';

export enum PaymentTypeEnum {
  DEPOSIT = 'deposit',
  PARTIAL = 'partial',
  FULL = 'full',
  SETTLEMENT = 'settlement',
}

export enum PaymentMethodEnum {
  BANK_TRANSFER = 'bank_transfer',
  CHECK = 'check',
  CASH = 'cash',
  CREDIT = 'credit',
}

export enum PaymentStatusEnum {
  PENDING = 'pending',
  PROCESSED = 'processed',
  FAILED = 'failed',
}

export class RecordPaymentDto {
  @IsString()
  poId: string;

  @IsString()
  amount: string; // Decimal as string

  @IsEnum(PaymentTypeEnum)
  paymentType: PaymentTypeEnum;

  @IsString()
  invoiceNumber: string;

  @IsOptional()
  @IsEnum(PaymentMethodEnum)
  paymentMethod?: PaymentMethodEnum;

  @IsOptional()
  @IsString()
  referenceNumber?: string;

  @IsOptional()
  @IsString()
  notes?: string;
}

export class PaymentResponseDto {
  id: string;
  poId: string;
  supplierId: string;
  invoiceNumber: string;
  amount: Decimal;
  paymentType: string;
  paymentMethod?: string;
  referenceNumber?: string;
  status: string;
  dueDate?: Date;
  paidDate?: Date;
  recordedAt: Date;
  updatedAt: Date;
}
