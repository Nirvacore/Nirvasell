import {
  Injectable,
  BadRequestException,
  NotFoundException,
  ConflictException,
  Logger,
} from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, LessThan } from 'typeorm';
import { Decimal } from 'decimal.js';
import { Warehouse } from '../entities/warehouse.entity';
import { WarehouseInventory } from '../entities/warehouse-inventory.entity';
import { StockTransfer, TransferStatus, TransferItem } from '../entities/stock-transfer.entity';
import { CycleCount, CycleCountStatus, CountItem } from '../entities/cycle-count.entity';
import { AdjustmentRecord, AdjustmentReason } from '../entities/adjustment-record.entity';
import { LowStockAlert } from '../entities/low-stock-alert.entity';
import { InventoryValuationHistory } from '../entities/inventory-valuation-history.entity';

export enum ValuationMethod {
  FIFO = 'FIFO',
  LIFO = 'LIFO',
  WAC = 'WAC', // Weighted Average Cost
}

export interface Transfer {
  id: string;
  companyId: string;
  fromWarehouseId: string;
  toWarehouseId: string;
  items: TransferItem[];
  status: TransferStatus;
  referenceNumber?: string;
  createdAt: Date;
  completedAt?: Date;
}

export interface CycleCountResult {
  cycleCountId: string;
  totalItems: number;
  itemsWithVariance: number;
  totalVariance: number;
  completedAt: Date;
}

export interface Variance {
  productId: string;
  systemQuantity: number;
  physicalQuantity: number;
  variance: number;
}

export interface ReorderNotification {
  productId: string;
  currentStock: number;
  reorderQuantity: number;
  estimatedArrival?: Date;
}

@Injectable()
export class InventoryManagementService {
  private readonly logger = new Logger(InventoryManagementService.name);

  constructor(
    @InjectRepository(Warehouse)
    private warehouseRepo: Repository<Warehouse>,
    @InjectRepository(WarehouseInventory)
    private inventoryRepo: Repository<WarehouseInventory>,
    @InjectRepository(StockTransfer)
    private transferRepo: Repository<StockTransfer>,
    @InjectRepository(CycleCount)
    private cycleCountRepo: Repository<CycleCount>,
    @InjectRepository(AdjustmentRecord)
    private adjustmentRepo: Repository<AdjustmentRecord>,
    @InjectRepository(LowStockAlert)
    private alertRepo: Repository<LowStockAlert>,
    @InjectRepository(InventoryValuationHistory)
    private valuationHistoryRepo: Repository<InventoryValuationHistory>,
  ) {}

  // ============ Stock Transfers ============

  async createTransfer(
    companyId: string,
    fromWarehouse: string,
    toWarehouse: string,
    items: TransferItem[],
  ): Promise<Transfer> {
    if (fromWarehouse === toWarehouse) {
      throw new BadRequestException('Source and destination warehouses must be different');
    }

    const [fromWh, toWh] = await Promise.all([
      this.warehouseRepo.findOne({ where: { id: fromWarehouse, companyId } }),
      this.warehouseRepo.findOne({ where: { id: toWarehouse, companyId } }),
    ]);

    if (!fromWh || !toWh) {
      throw new NotFoundException('One or both warehouses not found');
    }

    // Validate sufficient stock in source warehouse
    for (const item of items) {
      const inventory = await this.inventoryRepo.findOne({
        where: { warehouseId: fromWarehouse, productId: item.productId, companyId },
      });

      if (!inventory || inventory.quantity < item.quantity) {
        throw new BadRequestException(
          `Insufficient stock for product ${item.productId} in source warehouse`,
        );
      }
    }

    const transfer = this.transferRepo.create({
      companyId,
      fromWarehouseId: fromWarehouse,
      toWarehouseId: toWarehouse,
      items,
      status: TransferStatus.PENDING,
      referenceNumber: `TRF-${Date.now()}`,
    });

    return this.transferRepo.save(transfer);
  }

  async completeTransfer(companyId: string, transferId: string): Promise<Transfer> {
    const transfer = await this.transferRepo.findOne({
      where: { id: transferId, companyId },
    });

    if (!transfer) {
      throw new NotFoundException('Transfer not found');
    }

    if (transfer.status === TransferStatus.RECEIVED) {
      throw new ConflictException('Transfer already completed');
    }

    // Move inventory
    for (const item of transfer.items) {
      const fromInventory = await this.inventoryRepo.findOne({
        where: {
          warehouseId: transfer.fromWarehouseId,
          productId: item.productId,
          companyId,
        },
      });

      if (fromInventory) {
        fromInventory.quantity -= item.receivedQuantity || item.quantity;
        await this.inventoryRepo.save(fromInventory);
      }

      let toInventory = await this.inventoryRepo.findOne({
        where: {
          warehouseId: transfer.toWarehouseId,
          productId: item.productId,
          companyId,
        },
      });

      if (!toInventory) {
        toInventory = this.inventoryRepo.create({
          companyId,
          warehouseId: transfer.toWarehouseId,
          productId: item.productId,
          quantity: item.receivedQuantity || item.quantity,
        });
      } else {
        toInventory.quantity += item.receivedQuantity || item.quantity;
      }

      await this.inventoryRepo.save(toInventory);
    }

    transfer.status = TransferStatus.RECEIVED;
    transfer.completedAt = new Date();

    return this.transferRepo.save(transfer);
  }

  async getTransferHistory(companyId: string, warehouseId: string): Promise<Transfer[]> {
    return this.transferRepo.find({
      where: [
        { companyId, fromWarehouseId: warehouseId },
        { companyId, toWarehouseId: warehouseId },
      ],
      order: { createdAt: 'DESC' },
    });
  }

  // ============ Cycle Count & Audit ============

  async startCycleCount(
    companyId: string,
    warehouseId: string,
    items: CountItem[],
  ): Promise<CycleCount> {
    const warehouse = await this.warehouseRepo.findOne({
      where: { id: warehouseId, companyId },
    });

    if (!warehouse) {
      throw new NotFoundException('Warehouse not found');
    }

    const cycleCount = this.cycleCountRepo.create({
      companyId,
      warehouseId,
      items,
      status: CycleCountStatus.ACTIVE,
    });

    return this.cycleCountRepo.save(cycleCount);
  }

  async recordCount(
    companyId: string,
    cycleCountId: string,
    productId: string,
    physicalCount: number,
  ): Promise<void> {
    const cycleCount = await this.cycleCountRepo.findOne({
      where: { id: cycleCountId, companyId },
    });

    if (!cycleCount) {
      throw new NotFoundException('Cycle count not found');
    }

    const item = cycleCount.items.find(i => i.productId === productId);
    if (!item) {
      throw new NotFoundException('Product not found in cycle count');
    }

    item.physicalQuantity = physicalCount;
    item.variance = item.systemQuantity - physicalCount;

    await this.cycleCountRepo.save(cycleCount);
  }

  async completeCycleCount(companyId: string, cycleCountId: string): Promise<CycleCountResult> {
    const cycleCount = await this.cycleCountRepo.findOne({
      where: { id: cycleCountId, companyId },
    });

    if (!cycleCount) {
      throw new NotFoundException('Cycle count not found');
    }

    const itemsWithVariance = cycleCount.items.filter(i => i.variance !== 0).length;
    const totalVariance = cycleCount.items.reduce((sum, i) => sum + (i.variance || 0), 0);

    cycleCount.status = CycleCountStatus.COMPLETED;
    cycleCount.completedAt = new Date();

    await this.cycleCountRepo.save(cycleCount);

    return {
      cycleCountId,
      totalItems: cycleCount.items.length,
      itemsWithVariance,
      totalVariance,
      completedAt: cycleCount.completedAt,
    };
  }

  async getVariances(companyId: string, cycleCountId: string): Promise<Variance[]> {
    const cycleCount = await this.cycleCountRepo.findOne({
      where: { id: cycleCountId, companyId },
    });

    if (!cycleCount) {
      throw new NotFoundException('Cycle count not found');
    }

    return cycleCount.items
      .filter(i => i.physicalQuantity !== undefined && i.variance !== 0)
      .map(i => ({
        productId: i.productId,
        systemQuantity: i.systemQuantity,
        physicalQuantity: i.physicalQuantity!,
        variance: i.variance!,
      }));
  }

  // ============ Stock Adjustments ============

  async adjustStock(
    companyId: string,
    productId: string,
    warehouseId: string,
    qty: number,
    reason: AdjustmentReason,
  ): Promise<AdjustmentRecord> {
    let inventory = await this.inventoryRepo.findOne({
      where: { companyId, warehouseId, productId },
    });

    if (!inventory) {
      throw new NotFoundException('Product not found in warehouse');
    }

    const newQuantity = inventory.quantity + qty;
    if (newQuantity < 0) {
      throw new BadRequestException('Adjustment would result in negative stock');
    }

    inventory.quantity = newQuantity;
    await this.inventoryRepo.save(inventory);

    const adjustment = this.adjustmentRepo.create({
      companyId,
      warehouseId,
      productId,
      quantity: qty,
      reason,
    });

    return this.adjustmentRepo.save(adjustment);
  }

  async getAdjustmentHistory(companyId: string, from: Date, to: Date): Promise<AdjustmentRecord[]> {
    return this.adjustmentRepo.find({
      where: {
        companyId,
        createdAt: LessThan(to),
      },
      order: { createdAt: 'DESC' },
    });
  }

  // ============ Low Stock Alerts ============

  async configureLowStockAlert(
    companyId: string,
    productId: string,
    threshold: number,
    autoReorderQuantity?: number,
  ): Promise<LowStockAlert> {
    let alert = await this.alertRepo.findOne({
      where: { companyId, productId },
    });

    if (!alert) {
      alert = this.alertRepo.create({
        companyId,
        productId,
        threshold,
        autoReorderQuantity,
      });
    } else {
      alert.threshold = threshold;
      alert.autoReorderQuantity = autoReorderQuantity;
    }

    return this.alertRepo.save(alert);
  }

  async getLowStockItems(
    companyId: string,
  ): Promise<Array<{ productId: string; currentStock: number; threshold: number }>> {
    const alerts = await this.alertRepo.find({
      where: { companyId, isActive: true },
    });

    const result = [];

    for (const alert of alerts) {
      const totalStock = await this.inventoryRepo
        .createQueryBuilder('wi')
        .where('wi.companyId = :companyId', { companyId })
        .andWhere('wi.productId = :productId', { productId: alert.productId })
        .select('SUM(wi.quantity)', 'total')
        .getRawOne();

      const currentStock = parseInt(totalStock?.total || 0, 10);

      if (currentStock <= alert.threshold) {
        result.push({
          productId: alert.productId,
          currentStock,
          threshold: alert.threshold,
        });
      }
    }

    return result;
  }

  async triggerAutoReorder(
    companyId: string,
    productId: string,
    quantity: number,
  ): Promise<ReorderNotification> {
    const alert = await this.alertRepo.findOne({
      where: { companyId, productId },
    });

    if (!alert) {
      throw new NotFoundException('Alert configuration not found');
    }

    alert.lastAlertDate = new Date();
    await this.alertRepo.save(alert);

    return {
      productId,
      currentStock: quantity,
      reorderQuantity: alert.autoReorderQuantity || 0,
    };
  }

  // ============ Inventory Valuation ============

  async calculateInventoryCost(
    companyId: string,
    method: ValuationMethod,
  ): Promise<Decimal> {
    const valuationHistory = await this.valuationHistoryRepo.find({
      where: { companyId },
      order: { receivedDate: 'ASC' },
    });

    if (valuationHistory.length === 0) {
      return new Decimal(0);
    }

    if (method === ValuationMethod.FIFO) {
      return this.calculateFIFO(valuationHistory);
    } else if (method === ValuationMethod.LIFO) {
      return this.calculateLIFO(valuationHistory);
    } else if (method === ValuationMethod.WAC) {
      return this.calculateWAC(valuationHistory);
    }

    return new Decimal(0);
  }

  private calculateFIFO(history: InventoryValuationHistory[]): Decimal {
    let totalCost = new Decimal(0);
    for (const record of history) {
      if (record.remainingQuantity > 0) {
        totalCost = totalCost.plus(
          new Decimal(record.unitCost).times(new Decimal(record.remainingQuantity)),
        );
      }
    }
    return totalCost;
  }

  private calculateLIFO(history: InventoryValuationHistory[]): Decimal {
    let totalCost = new Decimal(0);
    for (let i = history.length - 1; i >= 0; i--) {
      const record = history[i];
      if (record.remainingQuantity > 0) {
        totalCost = totalCost.plus(
          new Decimal(record.unitCost).times(new Decimal(record.remainingQuantity)),
        );
      }
    }
    return totalCost;
  }

  private calculateWAC(history: InventoryValuationHistory[]): Decimal {
    let totalCost = new Decimal(0);
    let totalQuantity = 0;

    for (const record of history) {
      totalCost = totalCost.plus(record.totalCost);
      totalQuantity += record.quantity;
    }

    if (totalQuantity === 0) return new Decimal(0);

    return totalCost.dividedBy(new Decimal(totalQuantity));
  }

  async getInventoryValue(companyId: string, warehouseId?: string): Promise<Decimal> {
    let query = this.inventoryRepo
      .createQueryBuilder('wi')
      .where('wi.companyId = :companyId', { companyId });

    if (warehouseId) {
      query = query.andWhere('wi.warehouseId = :warehouseId', { warehouseId });
    }

    const inventories = await query.getMany();

    let totalValue = new Decimal(0);
    for (const inv of inventories) {
      totalValue = totalValue.plus(
        new Decimal(inv.unitCost).times(new Decimal(inv.quantity)),
      );
    }

    return totalValue;
  }

  async getInventoryTurnover(companyId: string, days: number): Promise<number> {
    // Simplified: COGS / average inventory * 365
    // In production, fetch actual COGS from sales data
    const avgInventory = await this.inventoryRepo
      .createQueryBuilder('wi')
      .where('wi.companyId = :companyId', { companyId })
      .select('AVG(wi.quantity)', 'avg')
      .getRawOne();

    if (!avgInventory || avgInventory.avg === 0) return 0;

    // Placeholder: In production, sum actual COGS from orders
    const cogs = new Decimal(0); // TODO: Fetch from orders
    const average = new Decimal(avgInventory.avg);

    return cogs.dividedBy(average).times(new Decimal(365 / days)).toNumber();
  }

  // ============ Warehouse Management ============

  async createWarehouse(
    companyId: string,
    name: string,
    location: string,
    capacity: number,
  ): Promise<Warehouse> {
    if (capacity <= 0) {
      throw new BadRequestException('Capacity must be greater than zero');
    }

    const warehouse = this.warehouseRepo.create({
      companyId,
      name,
      location,
      capacity,
      usedCapacity: 0,
      isActive: true,
    });

    return this.warehouseRepo.save(warehouse);
  }

  async getWarehouseInventory(
    companyId: string,
    warehouseId: string,
  ): Promise<Array<{ productId: string; quantity: number; shelf?: string }>> {
    const inventory = await this.inventoryRepo.find({
      where: { companyId, warehouseId },
    });

    return inventory.map(inv => ({
      productId: inv.productId,
      quantity: inv.quantity,
      shelf: inv.shelf,
    }));
  }

  async getWarehouseCapacity(
    companyId: string,
    warehouseId: string,
  ): Promise<{ used: number; total: number; utilization: number }> {
    const warehouse = await this.warehouseRepo.findOne({
      where: { id: warehouseId, companyId },
    });

    if (!warehouse) {
      throw new NotFoundException('Warehouse not found');
    }

    const inventory = await this.inventoryRepo.find({
      where: { companyId, warehouseId },
    });

    const used = inventory.reduce((sum, inv) => sum + inv.quantity, 0);
    const total = parseInt(warehouse.capacity.toString(), 10);
    const utilization = total > 0 ? (used / total) * 100 : 0;

    return { used, total, utilization };
  }

  // ============ Multi-location Tracking ============

  async getProductLocations(
    companyId: string,
    productId: string,
  ): Promise<Array<{ warehouseId: string; quantity: number; shelf?: string }>> {
    const locations = await this.inventoryRepo.find({
      where: { companyId, productId },
    });

    return locations.map(loc => ({
      warehouseId: loc.warehouseId,
      quantity: loc.quantity,
      shelf: loc.shelf,
    }));
  }

  async updateProductLocation(
    companyId: string,
    productId: string,
    warehouseId: string,
    shelf: string,
    quantity: number,
  ): Promise<void> {
    if (quantity < 0) {
      throw new BadRequestException('Quantity cannot be negative');
    }

    let inventory = await this.inventoryRepo.findOne({
      where: { companyId, productId, warehouseId },
    });

    if (!inventory) {
      inventory = this.inventoryRepo.create({
        companyId,
        productId,
        warehouseId,
        quantity,
        shelf,
      });
    } else {
      inventory.quantity = quantity;
      inventory.shelf = shelf;
    }

    await this.inventoryRepo.save(inventory);
  }
}
