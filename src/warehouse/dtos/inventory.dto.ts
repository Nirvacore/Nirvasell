import { IsString, IsNumber, IsArray, IsOptional, IsEnum, IsPositive, ValidateNested, Type } from 'class-validator';

export enum AdjustmentReasonEnum {
  DAMAGE = 'damage',
  THEFT = 'theft',
  SHRINKAGE = 'shrinkage',
  VARIANCE = 'variance',
  OTHER = 'other',
}

export enum ValuationMethodEnum {
  FIFO = 'FIFO',
  LIFO = 'LIFO',
  WAC = 'WAC',
}

// Transfer DTOs
export class TransferItemDto {
  @IsString()
  productId: string;

  @IsNumber()
  @IsPositive()
  quantity: number;

  @IsOptional()
  @IsNumber()
  receivedQuantity?: number;
}

export class CreateTransferDto {
  @IsString()
  fromWarehouse: string;

  @IsString()
  toWarehouse: string;

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => TransferItemDto)
  items: TransferItemDto[];
}

export class CompleteTransferDto {
  @IsString()
  transferId: string;

  @IsOptional()
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => TransferItemDto)
  receivedItems?: TransferItemDto[];
}

// Cycle Count DTOs
export class CountItemDto {
  @IsString()
  productId: string;

  @IsNumber()
  systemQuantity: number;

  @IsOptional()
  @IsNumber()
  physicalQuantity?: number;
}

export class StartCycleCountDto {
  @IsString()
  warehouseId: string;

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => CountItemDto)
  items: CountItemDto[];
}

export class RecordCountDto {
  @IsString()
  cycleCountId: string;

  @IsString()
  productId: string;

  @IsNumber()
  @IsPositive()
  physicalCount: number;
}

// Stock Adjustment DTOs
export class AdjustStockDto {
  @IsString()
  productId: string;

  @IsString()
  warehouseId: string;

  @IsNumber()
  quantity: number;

  @IsEnum(AdjustmentReasonEnum)
  reason: AdjustmentReasonEnum;

  @IsOptional()
  @IsString()
  notes?: string;
}

// Low Stock Alert DTOs
export class ConfigureLowStockAlertDto {
  @IsString()
  productId: string;

  @IsNumber()
  @IsPositive()
  threshold: number;

  @IsOptional()
  @IsNumber()
  @IsPositive()
  autoReorderQuantity?: number;
}

// Inventory Valuation DTOs
export class CalculateInventoryCostDto {
  @IsEnum(ValuationMethodEnum)
  method: ValuationMethodEnum;
}

// Warehouse Management DTOs
export class CreateWarehouseDto {
  @IsString()
  name: string;

  @IsString()
  location: string;

  @IsNumber()
  @IsPositive()
  capacity: number;
}

export class UpdateProductLocationDto {
  @IsString()
  productId: string;

  @IsString()
  warehouseId: string;

  @IsString()
  shelf: string;

  @IsNumber()
  @IsPositive()
  quantity: number;
}

// Response DTOs
export class TransferResponseDto {
  id: string;
  companyId: string;
  fromWarehouseId: string;
  toWarehouseId: string;
  items: TransferItemDto[];
  status: string;
  referenceNumber?: string;
  createdAt: Date;
  completedAt?: Date;
}

export class WarehouseCapacityDto {
  used: number;
  total: number;
  utilization: number;
}

export class ProductLocationDto {
  warehouseId: string;
  quantity: number;
  shelf?: string;
}

export class LowStockItemDto {
  productId: string;
  currentStock: number;
  threshold: number;
}

export class CycleCountResultDto {
  cycleCountId: string;
  totalItems: number;
  itemsWithVariance: number;
  totalVariance: number;
  completedAt: Date;
}

export class VarianceDto {
  productId: string;
  systemQuantity: number;
  physicalQuantity: number;
  variance: number;
}

export class ReorderNotificationDto {
  productId: string;
  currentStock: number;
  reorderQuantity: number;
  estimatedArrival?: Date;
}

export class InventoryValueDto {
  companyId: string;
  totalValue: string; // Decimal as string
  warehouseId?: string;
}

export class InventoryTurnoverDto {
  companyId: string;
  days: number;
  turnoverRatio: number;
}
