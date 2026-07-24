import {
  Controller,
  Post,
  Get,
  Put,
  Body,
  Param,
  Query,
  BadRequestException,
} from '@nestjs/common';
import { InventoryManagementService, ValuationMethod } from '../services/inventory-management.service';
import {
  CreateTransferDto,
  CompleteTransferDto,
  StartCycleCountDto,
  RecordCountDto,
  AdjustStockDto,
  ConfigureLowStockAlertDto,
  CalculateInventoryCostDto,
  CreateWarehouseDto,
  UpdateProductLocationDto,
  AdjustmentReasonEnum,
} from '../dtos/inventory.dto';
import { AdjustmentReason } from '../entities/adjustment-record.entity';

/**
 * Inventory Management Controller
 *
 * Handles all warehouse operations including stock transfers, cycle counts,
 * inventory valuation, low stock management, and warehouse capacity tracking.
 * Multi-tenant: companyId is extracted from request context.
 */
@Controller('warehouse/inventory')
export class InventoryManagementController {
  constructor(private readonly inventoryService: InventoryManagementService) {}

  // ============ Endpoint 1: Stock Transfers ============

  /**
   * Create a stock transfer between warehouses
   * POST /warehouse/inventory/transfers
   */
  @Post('transfers')
  async createTransfer(
    @Param('companyId') companyId: string,
    @Body() dto: CreateTransferDto,
  ) {
    return this.inventoryService.createTransfer(
      companyId,
      dto.fromWarehouse,
      dto.toWarehouse,
      dto.items.map(item => ({
        productId: item.productId,
        quantity: item.quantity,
        receivedQuantity: item.receivedQuantity,
      })),
    );
  }

  /**
   * Complete a pending stock transfer
   * PUT /warehouse/inventory/transfers/:transferId/complete
   */
  @Put('transfers/:transferId/complete')
  async completeTransfer(
    @Param('companyId') companyId: string,
    @Param('transferId') transferId: string,
    @Body() dto: CompleteTransferDto,
  ) {
    return this.inventoryService.completeTransfer(companyId, transferId);
  }

  /**
   * Get transfer history for a warehouse
   * GET /warehouse/inventory/transfers/warehouse/:warehouseId
   */
  @Get('transfers/warehouse/:warehouseId')
  async getTransferHistory(
    @Param('companyId') companyId: string,
    @Param('warehouseId') warehouseId: string,
  ) {
    return this.inventoryService.getTransferHistory(companyId, warehouseId);
  }

  // ============ Endpoint 2: Cycle Count & Audit ============

  /**
   * Start a cycle count for warehouse inventory audit
   * POST /warehouse/inventory/cycle-counts
   */
  @Post('cycle-counts')
  async startCycleCount(
    @Param('companyId') companyId: string,
    @Body() dto: StartCycleCountDto,
  ) {
    return this.inventoryService.startCycleCount(
      companyId,
      dto.warehouseId,
      dto.items.map(item => ({
        productId: item.productId,
        systemQuantity: item.systemQuantity,
      })),
    );
  }

  /**
   * Record physical count for a product in cycle count
   * POST /warehouse/inventory/cycle-counts/record
   */
  @Post('cycle-counts/record')
  async recordCount(
    @Param('companyId') companyId: string,
    @Body() dto: RecordCountDto,
  ) {
    await this.inventoryService.recordCount(
      companyId,
      dto.cycleCountId,
      dto.productId,
      dto.physicalCount,
    );
    return { message: 'Physical count recorded successfully' };
  }

  /**
   * Complete cycle count and get audit results
   * PUT /warehouse/inventory/cycle-counts/:cycleCountId/complete
   */
  @Put('cycle-counts/:cycleCountId/complete')
  async completeCycleCount(
    @Param('companyId') companyId: string,
    @Param('cycleCountId') cycleCountId: string,
  ) {
    return this.inventoryService.completeCycleCount(companyId, cycleCountId);
  }

  /**
   * Get variance details from completed cycle count
   * GET /warehouse/inventory/cycle-counts/:cycleCountId/variances
   */
  @Get('cycle-counts/:cycleCountId/variances')
  async getVariances(
    @Param('companyId') companyId: string,
    @Param('cycleCountId') cycleCountId: string,
  ) {
    return this.inventoryService.getVariances(companyId, cycleCountId);
  }

  // ============ Endpoint 3: Stock Adjustments ============

  /**
   * Adjust stock for damage, theft, shrinkage, or variance
   * POST /warehouse/inventory/adjustments
   */
  @Post('adjustments')
  async adjustStock(
    @Param('companyId') companyId: string,
    @Body() dto: AdjustStockDto,
  ) {
    const reasonMap: Record<AdjustmentReasonEnum, AdjustmentReason> = {
      [AdjustmentReasonEnum.DAMAGE]: AdjustmentReason.DAMAGE,
      [AdjustmentReasonEnum.THEFT]: AdjustmentReason.THEFT,
      [AdjustmentReasonEnum.SHRINKAGE]: AdjustmentReason.SHRINKAGE,
      [AdjustmentReasonEnum.VARIANCE]: AdjustmentReason.VARIANCE,
      [AdjustmentReasonEnum.OTHER]: AdjustmentReason.OTHER,
    };

    return this.inventoryService.adjustStock(
      companyId,
      dto.productId,
      dto.warehouseId,
      dto.quantity,
      reasonMap[dto.reason],
    );
  }

  /**
   * Get adjustment history within date range
   * GET /warehouse/inventory/adjustments
   */
  @Get('adjustments')
  async getAdjustmentHistory(
    @Param('companyId') companyId: string,
    @Query('from') from: string,
    @Query('to') to: string,
  ) {
    if (!from || !to) {
      throw new BadRequestException('from and to dates are required');
    }
    return this.inventoryService.getAdjustmentHistory(
      companyId,
      new Date(from),
      new Date(to),
    );
  }

  // ============ Endpoint 4: Low Stock Alerts ============

  /**
   * Configure low stock alert for a product
   * POST /warehouse/inventory/alerts
   */
  @Post('alerts')
  async configureLowStockAlert(
    @Param('companyId') companyId: string,
    @Body() dto: ConfigureLowStockAlertDto,
  ) {
    return this.inventoryService.configureLowStockAlert(
      companyId,
      dto.productId,
      dto.threshold,
      dto.autoReorderQuantity,
    );
  }

  /**
   * Get all products currently below low stock threshold
   * GET /warehouse/inventory/alerts/low-stock
   */
  @Get('alerts/low-stock')
  async getLowStockItems(@Param('companyId') companyId: string) {
    return this.inventoryService.getLowStockItems(companyId);
  }

  /**
   * Trigger auto-reorder for a product
   * POST /warehouse/inventory/alerts/:productId/reorder
   */
  @Post('alerts/:productId/reorder')
  async triggerAutoReorder(
    @Param('companyId') companyId: string,
    @Param('productId') productId: string,
    @Query('quantity') quantity: number,
  ) {
    return this.inventoryService.triggerAutoReorder(companyId, productId, quantity);
  }

  // ============ Endpoint 5: Inventory Valuation ============

  /**
   * Calculate inventory cost using FIFO, LIFO, or WAC method
   * POST /warehouse/inventory/valuation/cost
   */
  @Post('valuation/cost')
  async calculateInventoryCost(
    @Param('companyId') companyId: string,
    @Body() dto: CalculateInventoryCostDto,
  ) {
    const methodMap: Record<string, ValuationMethod> = {
      FIFO: ValuationMethod.FIFO,
      LIFO: ValuationMethod.LIFO,
      WAC: ValuationMethod.WAC,
    };

    const method = methodMap[dto.method];
    if (!method) {
      throw new BadRequestException('Invalid valuation method');
    }

    const cost = await this.inventoryService.calculateInventoryCost(companyId, method);
    return { method: dto.method, totalCost: cost.toString() };
  }

  /**
   * Get total inventory value for company or warehouse
   * GET /warehouse/inventory/valuation/value
   */
  @Get('valuation/value')
  async getInventoryValue(
    @Param('companyId') companyId: string,
    @Query('warehouseId') warehouseId?: string,
  ) {
    const value = await this.inventoryService.getInventoryValue(companyId, warehouseId);
    return { companyId, warehouseId, totalValue: value.toString() };
  }

  /**
   * Get inventory turnover ratio
   * GET /warehouse/inventory/valuation/turnover
   */
  @Get('valuation/turnover')
  async getInventoryTurnover(
    @Param('companyId') companyId: string,
    @Query('days') daysStr: string = '30',
  ) {
    const days = parseInt(daysStr, 10);
    if (isNaN(days) || days <= 0) {
      throw new BadRequestException('Days must be a positive number');
    }

    const turnover = await this.inventoryService.getInventoryTurnover(companyId, days);
    return { companyId, days, turnoverRatio: turnover };
  }

  // ============ Endpoint 6: Warehouse Management ============

  /**
   * Create a new warehouse
   * POST /warehouse/inventory/warehouses
   */
  @Post('warehouses')
  async createWarehouse(
    @Param('companyId') companyId: string,
    @Body() dto: CreateWarehouseDto,
  ) {
    return this.inventoryService.createWarehouse(
      companyId,
      dto.name,
      dto.location,
      dto.capacity,
    );
  }

  /**
   * Get current inventory for a warehouse
   * GET /warehouse/inventory/warehouses/:warehouseId/inventory
   */
  @Get('warehouses/:warehouseId/inventory')
  async getWarehouseInventory(
    @Param('companyId') companyId: string,
    @Param('warehouseId') warehouseId: string,
  ) {
    return this.inventoryService.getWarehouseInventory(companyId, warehouseId);
  }

  /**
   * Get warehouse capacity utilization
   * GET /warehouse/inventory/warehouses/:warehouseId/capacity
   */
  @Get('warehouses/:warehouseId/capacity')
  async getWarehouseCapacity(
    @Param('companyId') companyId: string,
    @Param('warehouseId') warehouseId: string,
  ) {
    return this.inventoryService.getWarehouseCapacity(companyId, warehouseId);
  }

  // ============ Endpoint 7: Multi-location Tracking ============

  /**
   * Get all locations where a product is stored
   * GET /warehouse/inventory/products/:productId/locations
   */
  @Get('products/:productId/locations')
  async getProductLocations(
    @Param('companyId') companyId: string,
    @Param('productId') productId: string,
  ) {
    return this.inventoryService.getProductLocations(companyId, productId);
  }

  /**
   * Update product shelf location and quantity
   * PUT /warehouse/inventory/products/location
   */
  @Put('products/location')
  async updateProductLocation(
    @Param('companyId') companyId: string,
    @Body() dto: UpdateProductLocationDto,
  ) {
    await this.inventoryService.updateProductLocation(
      companyId,
      dto.productId,
      dto.warehouseId,
      dto.shelf,
      dto.quantity,
    );
    return { message: 'Product location updated successfully' };
  }

  // ============ Endpoint 8: Health Check & Summary ============

  /**
   * Get comprehensive inventory health summary
   * GET /warehouse/inventory/health
   */
  @Get('health')
  async getInventoryHealth(@Param('companyId') companyId: string) {
    const lowStockItems = await this.inventoryService.getLowStockItems(companyId);
    const inventoryValue = await this.inventoryService.getInventoryValue(companyId);
    const turnover = await this.inventoryService.getInventoryTurnover(companyId, 30);

    return {
      companyId,
      lowStockItemsCount: lowStockItems.length,
      totalInventoryValue: inventoryValue.toString(),
      inventoryTurnover30Days: turnover,
      timestamp: new Date(),
    };
  }
}
