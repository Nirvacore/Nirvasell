import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { InventoryManagementService } from './services/inventory-management.service';
import { InventoryManagementController } from './controllers/inventory-management.controller';
import { Warehouse } from './entities/warehouse.entity';
import { WarehouseInventory } from './entities/warehouse-inventory.entity';
import { StockTransfer } from './entities/stock-transfer.entity';
import { CycleCount } from './entities/cycle-count.entity';
import { AdjustmentRecord } from './entities/adjustment-record.entity';
import { LowStockAlert } from './entities/low-stock-alert.entity';
import { InventoryValuationHistory } from './entities/inventory-valuation-history.entity';

/**
 * Warehouse Module
 *
 * Provides comprehensive inventory management capabilities including:
 * - Stock transfers between warehouses
 * - Cycle count and audit operations
 * - Stock adjustments (damage, theft, shrinkage, variance)
 * - Low stock alerts and auto-reorder triggers
 * - Inventory cost valuation (FIFO, LIFO, WAC)
 * - Warehouse location management
 * - Multi-tenant isolation
 */
@Module({
  imports: [
    TypeOrmModule.forFeature([
      Warehouse,
      WarehouseInventory,
      StockTransfer,
      CycleCount,
      AdjustmentRecord,
      LowStockAlert,
      InventoryValuationHistory,
    ]),
  ],
  providers: [InventoryManagementService],
  controllers: [InventoryManagementController],
  exports: [InventoryManagementService],
})
export class WarehouseModule {}
