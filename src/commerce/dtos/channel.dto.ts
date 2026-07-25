import { IsString, IsOptional, IsEnum, IsJSON, IsBoolean, IsNumber, ValidateNested } from 'class-validator';
import { Type } from 'class-transformer';
import { Decimal } from 'decimal.js';

export enum ChannelEnum {
  SHOPEE = 'shopee',
  LAZADA = 'lazada',
  TIKTOK = 'tiktok',
}

export class ChannelCredentialsDto {
  @IsString()
  apiKey: string;

  @IsString()
  shopId: string;

  @IsOptional()
  @IsString()
  sellerId?: string;

  @IsOptional()
  @IsString()
  accessToken?: string;

  @IsOptional()
  @IsString()
  refreshToken?: string;
}

export class ChannelSettingsDto {
  @IsOptional()
  @IsBoolean()
  enableAutoSync?: boolean;

  @IsOptional()
  @IsNumber()
  syncInterval?: number;

  @IsOptional()
  @IsString()
  defaultMargin?: string;

  @IsOptional()
  @IsBoolean()
  enableInventoryDistribution?: boolean;

  @IsOptional()
  @IsNumber()
  maxStockPerChannel?: number;
}

export class AddChannelDto {
  @IsEnum(ChannelEnum)
  channel: ChannelEnum;

  @ValidateNested()
  @Type(() => ChannelCredentialsDto)
  credentials: ChannelCredentialsDto;

  @IsOptional()
  @ValidateNested()
  @Type(() => ChannelSettingsDto)
  settings?: ChannelSettingsDto;
}

export class UpdateChannelSettingsDto {
  @IsOptional()
  @IsBoolean()
  enableAutoSync?: boolean;

  @IsOptional()
  @IsNumber()
  syncInterval?: number;

  @IsOptional()
  @IsString()
  defaultMargin?: string;

  @IsOptional()
  @IsBoolean()
  enableInventoryDistribution?: boolean;

  @IsOptional()
  @IsNumber()
  maxStockPerChannel?: number;
}

export class ChannelConfigResponseDto {
  id: string;
  channel: ChannelEnum;
  isActive: boolean;
  settings: Record<string, any>;
  createdAt: Date;
  updatedAt: Date;
}
