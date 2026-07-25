import { IsString, IsNumber, IsOptional, IsArray, ValidateNested, Min } from 'class-validator';
import { Type } from 'class-transformer';
import { Decimal } from 'decimal.js';

export class QuotationItemDto {
  @IsString()
  description: string;

  @IsNumber()
  @Min(1)
  quantity: number;

  @IsString()
  unitPrice: string; // Decimal as string
}

export class CreateQuotationDto {
  @IsString()
  supplierId: string;

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => QuotationItemDto)
  items: QuotationItemDto[];

  @IsOptional()
  @IsNumber()
  @Min(1)
  validUntilDays?: number; // Default 30

  @IsOptional()
  @IsString()
  notes?: string;
}

export class AcceptQuotationDto {
  @IsString()
  quotationId: string;
}

export class RejectQuotationDto {
  @IsString()
  quotationId: string;

  @IsOptional()
  @IsString()
  reason?: string;
}

export class CompareQuotationsDto {
  @IsArray()
  @IsString({ each: true })
  quotationIds: string[];
}

export class QuotationResponseDto {
  id: string;
  quotationNumber: string;
  supplierId: string;
  items: any[];
  totalAmount: Decimal;
  validUntil: Date;
  status: string;
  acceptedAt?: Date;
  rejectedAt?: Date;
  poId?: string;
  revisionNumber: number;
  createdAt: Date;
  updatedAt: Date;
}
