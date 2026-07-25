import { IsString, IsEmail, IsPhoneNumber, IsOptional, IsNumber, IsEnum, Min, Max, ValidateNested } from 'class-validator';
import { Type } from 'class-transformer';
import { Decimal } from 'decimal.js';

export enum PaymentTermsEnum {
  COD = 'cod',
  NET30 = 'net30',
  NET60 = 'net60',
  NET90 = 'net90',
}

export class CreateSupplierDto {
  @IsString()
  name: string;

  @IsString()
  contact: string;

  @IsEmail()
  email: string;

  @IsString()
  phone: string;

  @IsEnum(PaymentTermsEnum)
  paymentTerms: PaymentTermsEnum;

  @IsOptional()
  @IsNumber()
  @Min(1)
  @Max(5)
  rating?: number;

  @IsOptional()
  @IsString()
  address?: string;

  @IsOptional()
  @IsString()
  city?: string;

  @IsOptional()
  @IsString()
  country?: string;

  @IsOptional()
  @IsString()
  taxId?: string;
}

export class UpdateSupplierDto {
  @IsOptional()
  @IsString()
  name?: string;

  @IsOptional()
  @IsString()
  contact?: string;

  @IsOptional()
  @IsEmail()
  email?: string;

  @IsOptional()
  @IsString()
  phone?: string;

  @IsOptional()
  @IsEnum(PaymentTermsEnum)
  paymentTerms?: PaymentTermsEnum;

  @IsOptional()
  @IsNumber()
  @Min(1)
  @Max(5)
  rating?: number;

  @IsOptional()
  @IsString()
  address?: string;

  @IsOptional()
  @IsString()
  city?: string;

  @IsOptional()
  @IsString()
  country?: string;

  @IsOptional()
  @IsString()
  taxId?: string;
}

export class SupplierResponseDto {
  id: string;
  name: string;
  contact: string;
  email: string;
  phone: string;
  paymentTerms: string;
  rating: number;
  address?: string;
  city?: string;
  country?: string;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}
