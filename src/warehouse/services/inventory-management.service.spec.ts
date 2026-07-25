import { Test, TestingModule } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Decimal } from 'decimal.js';
import { BadRequestException, NotFoundException, ConflictException } from '@nestjs/common';
import {
  InventoryManagementService,
  ValuationMethod,
} from './inventory-management.service';
import { Warehouse } from '../entities/warehouse.entity';
import { WarehouseInventory } from '../entities/warehouse-inventory.entity';
import { StockTransfer, TransferStatus } from '../entities/stock-transfer.entity';
import { CycleCount, CycleCountStatus } from '../entities/cycle-count.entity';
import { AdjustmentRecord, AdjustmentReason } from '../entities/adjustment-record.entity';
import { LowStockAlert } from '../entities/low-stock-alert.entity';
import { InventoryValuationHistory } from '../entities/inventory-valuation-history.entity';

describe('InventoryManagementService', () => {
  let service: InventoryManagementService;
  let warehouseRepo: Repository<Warehouse>;
  let inventoryRepo: Repository<WarehouseInventory>;
  let transferRepo: Repository<StockTransfer>;
  let cycleCountRepo: Repository<CycleCount>;
  let adjustmentRepo: Repository<AdjustmentRecord>;
  let alertRepo: Repository<LowStockAlert>;
  let valuationHistoryRepo: Repository<InventoryValuationHistory>;

  const mockCompanyId = 'company-123';
  const mockWarehouseId = 'warehouse-456';
  const mockProductId = 'product-789';

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        InventoryManagementService,
        {
          provide: getRepositoryToken(Warehouse),
          useValue: {
            findOne: jest.fn(),
            find: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
          },
        },
        {
          provide: getRepositoryToken(WarehouseInventory),
          useValue: {
            findOne: jest.fn(),
            find: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
            createQueryBuilder: jest.fn(),
          },
        },
        {
          provide: getRepositoryToken(StockTransfer),
          useValue: {
            findOne: jest.fn(),
            find: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
          },
        },
        {
          provide: getRepositoryToken(CycleCount),
          useValue: {
            findOne: jest.fn(),
            find: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
          },
        },
        {
          provide: getRepositoryToken(AdjustmentRecord),
          useValue: {
            findOne: jest.fn(),
            find: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
          },
        },
        {
          provide: getRepositoryToken(LowStockAlert),
          useValue: {
            findOne: jest.fn(),
            find: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
          },
        },
        {
          provide: getRepositoryToken(InventoryValuationHistory),
          useValue: {
            find: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
          },
        },
      ],
    }).compile();

    service = module.get<InventoryManagementService>(InventoryManagementService);
    warehouseRepo = module.get<Repository<Warehouse>>(getRepositoryToken(Warehouse));
    inventoryRepo = module.get<Repository<WarehouseInventory>>(
      getRepositoryToken(WarehouseInventory),
    );
    transferRepo = module.get<Repository<StockTransfer>>(getRepositoryToken(StockTransfer));
    cycleCountRepo = module.get<Repository<CycleCount>>(getRepositoryToken(CycleCount));
    adjustmentRepo = module.get<Repository<AdjustmentRecord>>(
      getRepositoryToken(AdjustmentRecord),
    );
    alertRepo = module.get<Repository<LowStockAlert>>(getRepositoryToken(LowStockAlert));
    valuationHistoryRepo = module.get<Repository<InventoryValuationHistory>>(
      getRepositoryToken(InventoryValuationHistory),
    );
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  // ============ Stock Transfer Tests ============

  describe('Stock Transfers', () => {
    describe('createTransfer', () => {
      it('should create a stock transfer successfully', async () => {
        const fromWarehouse: Warehouse = { id: 'wh-1', companyId: mockCompanyId, name: 'WH1', location: 'NYC', capacity: new Decimal(1000), usedCapacity: new Decimal(0), isActive: true, createdAt: new Date(), updatedAt: new Date() };
        const toWarehouse: Warehouse = { id: 'wh-2', companyId: mockCompanyId, name: 'WH2', location: 'LA', capacity: new Decimal(1000), usedCapacity: new Decimal(0), isActive: true, createdAt: new Date(), updatedAt: new Date() };

        jest.spyOn(warehouseRepo, 'findOne').mockResolvedValueOnce(fromWarehouse).mockResolvedValueOnce(toWarehouse);

        const inventory: WarehouseInventory = { id: 'inv-1', companyId: mockCompanyId, warehouseId: 'wh-1', productId: mockProductId, quantity: 100, unitCost: new Decimal('10'), shelf: 'A-1', isLocked: false, createdAt: new Date(), updatedAt: new Date() };
        jest.spyOn(inventoryRepo, 'findOne').mockResolvedValue(inventory);

        const mockTransfer = { id: 'tr-1', companyId: mockCompanyId, fromWarehouseId: 'wh-1', toWarehouseId: 'wh-2', items: [{ productId: mockProductId, quantity: 50 }], status: TransferStatus.PENDING, referenceNumber: 'TRF-12345', createdAt: new Date(), completedAt: undefined, updatedAt: new Date() };
        jest.spyOn(transferRepo, 'create').mockReturnValue(mockTransfer as any);
        jest.spyOn(transferRepo, 'save').mockResolvedValue(mockTransfer as any);

        const result = await service.createTransfer(
          mockCompanyId,
          'wh-1',
          'wh-2',
          [{ productId: mockProductId, quantity: 50 }],
        );

        expect(result).toEqual(mockTransfer);
        expect(result.status).toBe(TransferStatus.PENDING);
      });

      it('should throw error when source and destination are same', async () => {
        await expect(
          service.createTransfer(mockCompanyId, 'wh-1', 'wh-1', []),
        ).rejects.toThrow(BadRequestException);
      });

      it('should throw error when warehouse not found', async () => {
        jest.spyOn(warehouseRepo, 'findOne').mockResolvedValueOnce(null);

        await expect(
          service.createTransfer(mockCompanyId, 'wh-1', 'wh-2', []),
        ).rejects.toThrow(NotFoundException);
      });

      it('should throw error for insufficient stock', async () => {
        const fromWarehouse: Warehouse = { id: 'wh-1', companyId: mockCompanyId, name: 'WH1', location: 'NYC', capacity: new Decimal(1000), usedCapacity: new Decimal(0), isActive: true, createdAt: new Date(), updatedAt: new Date() };
        const toWarehouse: Warehouse = { id: 'wh-2', companyId: mockCompanyId, name: 'WH2', location: 'LA', capacity: new Decimal(1000), usedCapacity: new Decimal(0), isActive: true, createdAt: new Date(), updatedAt: new Date() };

        jest.spyOn(warehouseRepo, 'findOne').mockResolvedValueOnce(fromWarehouse).mockResolvedValueOnce(toWarehouse);

        const inventory: WarehouseInventory = { id: 'inv-1', companyId: mockCompanyId, warehouseId: 'wh-1', productId: mockProductId, quantity: 30, unitCost: new Decimal('10'), shelf: 'A-1', isLocked: false, createdAt: new Date(), updatedAt: new Date() };
        jest.spyOn(inventoryRepo, 'findOne').mockResolvedValue(inventory);

        await expect(
          service.createTransfer(mockCompanyId, 'wh-1', 'wh-2', [
            { productId: mockProductId, quantity: 50 },
          ]),
        ).rejects.toThrow(BadRequestException);
      });
    });

    describe('completeTransfer', () => {
      it('should complete a transfer successfully', async () => {
        const transfer: StockTransfer = {
          id: 'tr-1',
          companyId: mockCompanyId,
          fromWarehouseId: 'wh-1',
          toWarehouseId: 'wh-2',
          items: [{ productId: mockProductId, quantity: 50 }],
          status: TransferStatus.PENDING,
          referenceNumber: 'TRF-1',
          createdAt: new Date(),
          completedAt: undefined,
          updatedAt: new Date(),
        };

        jest.spyOn(transferRepo, 'findOne').mockResolvedValue(transfer);

        const fromInventory: WarehouseInventory = { id: 'inv-1', companyId: mockCompanyId, warehouseId: 'wh-1', productId: mockProductId, quantity: 100, unitCost: new Decimal('10'), shelf: 'A-1', isLocked: false, createdAt: new Date(), updatedAt: new Date() };
        const toInventory: WarehouseInventory = { id: 'inv-2', companyId: mockCompanyId, warehouseId: 'wh-2', productId: mockProductId, quantity: 20, unitCost: new Decimal('10'), shelf: 'B-1', isLocked: false, createdAt: new Date(), updatedAt: new Date() };

        jest.spyOn(inventoryRepo, 'findOne').mockResolvedValueOnce(fromInventory).mockResolvedValueOnce(toInventory);
        jest.spyOn(inventoryRepo, 'save').mockResolvedValue(fromInventory);

        jest.spyOn(transferRepo, 'save').mockResolvedValue({
          ...transfer,
          status: TransferStatus.RECEIVED,
          completedAt: new Date(),
        });

        const result = await service.completeTransfer(mockCompanyId, 'tr-1');

        expect(result.status).toBe(TransferStatus.RECEIVED);
        expect(result.completedAt).toBeDefined();
      });

      it('should throw error if transfer already completed', async () => {
        const transfer: StockTransfer = {
          id: 'tr-1',
          companyId: mockCompanyId,
          fromWarehouseId: 'wh-1',
          toWarehouseId: 'wh-2',
          items: [],
          status: TransferStatus.RECEIVED,
          referenceNumber: 'TRF-1',
          createdAt: new Date(),
          completedAt: new Date(),
          updatedAt: new Date(),
        };

        jest.spyOn(transferRepo, 'findOne').mockResolvedValue(transfer);

        await expect(service.completeTransfer(mockCompanyId, 'tr-1')).rejects.toThrow(
          ConflictException,
        );
      });
    });

    describe('getTransferHistory', () => {
      it('should get transfer history for warehouse', async () => {
        const transfers: StockTransfer[] = [
          {
            id: 'tr-1',
            companyId: mockCompanyId,
            fromWarehouseId: 'wh-1',
            toWarehouseId: 'wh-2',
            items: [],
            status: TransferStatus.PENDING,
            referenceNumber: 'TRF-1',
            createdAt: new Date(),
            completedAt: undefined,
            updatedAt: new Date(),
          },
        ];

        jest.spyOn(transferRepo, 'find').mockResolvedValue(transfers);

        const result = await service.getTransferHistory(mockCompanyId, 'wh-1');

        expect(result).toHaveLength(1);
        expect(result[0].id).toBe('tr-1');
      });
    });
  });

  // ============ Cycle Count Tests ============

  describe('Cycle Count & Audit', () => {
    describe('startCycleCount', () => {
      it('should start a cycle count', async () => {
        const warehouse: Warehouse = { id: 'wh-1', companyId: mockCompanyId, name: 'WH1', location: 'NYC', capacity: new Decimal(1000), usedCapacity: new Decimal(0), isActive: true, createdAt: new Date(), updatedAt: new Date() };
        jest.spyOn(warehouseRepo, 'findOne').mockResolvedValue(warehouse);

        const mockCycleCount = {
          id: 'cc-1',
          companyId: mockCompanyId,
          warehouseId: 'wh-1',
          items: [{ productId: mockProductId, systemQuantity: 100 }],
          status: CycleCountStatus.ACTIVE,
          createdAt: new Date(),
          completedAt: undefined,
          updatedAt: new Date(),
        };

        jest.spyOn(cycleCountRepo, 'create').mockReturnValue(mockCycleCount as any);
        jest.spyOn(cycleCountRepo, 'save').mockResolvedValue(mockCycleCount as any);

        const result = await service.startCycleCount(mockCompanyId, 'wh-1', [
          { productId: mockProductId, systemQuantity: 100 },
        ]);

        expect(result.status).toBe(CycleCountStatus.ACTIVE);
      });

      it('should throw error if warehouse not found', async () => {
        jest.spyOn(warehouseRepo, 'findOne').mockResolvedValue(null);

        await expect(
          service.startCycleCount(mockCompanyId, 'wh-1', []),
        ).rejects.toThrow(NotFoundException);
      });
    });

    describe('recordCount', () => {
      it('should record physical count', async () => {
        const cycleCount: CycleCount = {
          id: 'cc-1',
          companyId: mockCompanyId,
          warehouseId: 'wh-1',
          items: [{ productId: mockProductId, systemQuantity: 100 }],
          status: CycleCountStatus.ACTIVE,
          createdAt: new Date(),
          completedAt: undefined,
          updatedAt: new Date(),
        };

        jest.spyOn(cycleCountRepo, 'findOne').mockResolvedValue(cycleCount);
        jest.spyOn(cycleCountRepo, 'save').mockResolvedValue(cycleCount);

        await service.recordCount(mockCompanyId, 'cc-1', mockProductId, 95);

        expect(cycleCount.items[0].physicalQuantity).toBe(95);
        expect(cycleCount.items[0].variance).toBe(5);
      });

      it('should throw error if cycle count not found', async () => {
        jest.spyOn(cycleCountRepo, 'findOne').mockResolvedValue(null);

        await expect(
          service.recordCount(mockCompanyId, 'cc-1', mockProductId, 95),
        ).rejects.toThrow(NotFoundException);
      });

      it('should throw error if product not in cycle count', async () => {
        const cycleCount: CycleCount = {
          id: 'cc-1',
          companyId: mockCompanyId,
          warehouseId: 'wh-1',
          items: [],
          status: CycleCountStatus.ACTIVE,
          createdAt: new Date(),
          completedAt: undefined,
          updatedAt: new Date(),
        };

        jest.spyOn(cycleCountRepo, 'findOne').mockResolvedValue(cycleCount);

        await expect(
          service.recordCount(mockCompanyId, 'cc-1', mockProductId, 95),
        ).rejects.toThrow(NotFoundException);
      });
    });

    describe('completeCycleCount', () => {
      it('should complete cycle count and return results', async () => {
        const cycleCount: CycleCount = {
          id: 'cc-1',
          companyId: mockCompanyId,
          warehouseId: 'wh-1',
          items: [
            { productId: 'p1', systemQuantity: 100, physicalQuantity: 95, variance: 5 },
            { productId: 'p2', systemQuantity: 50, physicalQuantity: 50, variance: 0 },
          ],
          status: CycleCountStatus.ACTIVE,
          createdAt: new Date(),
          completedAt: undefined,
          updatedAt: new Date(),
        };

        jest.spyOn(cycleCountRepo, 'findOne').mockResolvedValue(cycleCount);
        jest.spyOn(cycleCountRepo, 'save').mockResolvedValue(cycleCount);

        const result = await service.completeCycleCount(mockCompanyId, 'cc-1');

        expect(result.totalItems).toBe(2);
        expect(result.itemsWithVariance).toBe(1);
        expect(result.totalVariance).toBe(5);
      });
    });

    describe('getVariances', () => {
      it('should return variances from cycle count', async () => {
        const cycleCount: CycleCount = {
          id: 'cc-1',
          companyId: mockCompanyId,
          warehouseId: 'wh-1',
          items: [
            { productId: 'p1', systemQuantity: 100, physicalQuantity: 95, variance: 5 },
          ],
          status: CycleCountStatus.ACTIVE,
          createdAt: new Date(),
          completedAt: undefined,
          updatedAt: new Date(),
        };

        jest.spyOn(cycleCountRepo, 'findOne').mockResolvedValue(cycleCount);

        const result = await service.getVariances(mockCompanyId, 'cc-1');

        expect(result).toHaveLength(1);
        expect(result[0].variance).toBe(5);
      });
    });
  });

  // ============ Stock Adjustment Tests ============

  describe('Stock Adjustments', () => {
    describe('adjustStock', () => {
      it('should adjust stock for damage', async () => {
        const inventory: WarehouseInventory = { id: 'inv-1', companyId: mockCompanyId, warehouseId: 'wh-1', productId: mockProductId, quantity: 100, unitCost: new Decimal('10'), shelf: 'A-1', isLocked: false, createdAt: new Date(), updatedAt: new Date() };
        jest.spyOn(inventoryRepo, 'findOne').mockResolvedValue(inventory);

        const mockAdjustment = { id: 'adj-1', companyId: mockCompanyId, warehouseId: 'wh-1', productId: mockProductId, quantity: -5, reason: AdjustmentReason.DAMAGE, notes: 'Broken unit', createdAt: new Date() };
        jest.spyOn(adjustmentRepo, 'create').mockReturnValue(mockAdjustment as any);
        jest.spyOn(adjustmentRepo, 'save').mockResolvedValue(mockAdjustment as any);
        jest.spyOn(inventoryRepo, 'save').mockResolvedValue(inventory);

        const result = await service.adjustStock(
          mockCompanyId,
          mockProductId,
          'wh-1',
          -5,
          AdjustmentReason.DAMAGE,
        );

        expect(result.quantity).toBe(-5);
        expect(result.reason).toBe(AdjustmentReason.DAMAGE);
      });

      it('should throw error for negative stock', async () => {
        const inventory: WarehouseInventory = { id: 'inv-1', companyId: mockCompanyId, warehouseId: 'wh-1', productId: mockProductId, quantity: 5, unitCost: new Decimal('10'), shelf: 'A-1', isLocked: false, createdAt: new Date(), updatedAt: new Date() };
        jest.spyOn(inventoryRepo, 'findOne').mockResolvedValue(inventory);

        await expect(
          service.adjustStock(mockCompanyId, mockProductId, 'wh-1', -10, AdjustmentReason.DAMAGE),
        ).rejects.toThrow(BadRequestException);
      });
    });

    describe('getAdjustmentHistory', () => {
      it('should return adjustment history', async () => {
        const adjustments: AdjustmentRecord[] = [
          { id: 'adj-1', companyId: mockCompanyId, warehouseId: 'wh-1', productId: mockProductId, quantity: -5, reason: AdjustmentReason.DAMAGE, notes: 'Broken', createdAt: new Date() },
        ];

        jest.spyOn(adjustmentRepo, 'find').mockResolvedValue(adjustments);

        const result = await service.getAdjustmentHistory(
          mockCompanyId,
          new Date('2024-01-01'),
          new Date('2024-12-31'),
        );

        expect(result).toHaveLength(1);
      });
    });
  });

  // ============ Low Stock Alert Tests ============

  describe('Low Stock Alerts', () => {
    describe('configureLowStockAlert', () => {
      it('should create a new low stock alert', async () => {
        jest.spyOn(alertRepo, 'findOne').mockResolvedValue(null);

        const mockAlert = { id: 'alert-1', companyId: mockCompanyId, productId: mockProductId, threshold: 20, autoReorderQuantity: 100, isActive: true, lastAlertDate: undefined, createdAt: new Date(), updatedAt: new Date() };
        jest.spyOn(alertRepo, 'create').mockReturnValue(mockAlert as any);
        jest.spyOn(alertRepo, 'save').mockResolvedValue(mockAlert as any);

        const result = await service.configureLowStockAlert(
          mockCompanyId,
          mockProductId,
          20,
          100,
        );

        expect(result.threshold).toBe(20);
        expect(result.autoReorderQuantity).toBe(100);
      });

      it('should update existing alert', async () => {
        const existingAlert = { id: 'alert-1', companyId: mockCompanyId, productId: mockProductId, threshold: 10, autoReorderQuantity: 50, isActive: true, lastAlertDate: undefined, createdAt: new Date(), updatedAt: new Date() };
        jest.spyOn(alertRepo, 'findOne').mockResolvedValue(existingAlert as any);
        jest.spyOn(alertRepo, 'save').mockResolvedValue(existingAlert as any);

        const result = await service.configureLowStockAlert(
          mockCompanyId,
          mockProductId,
          20,
          100,
        );

        expect(result.threshold).toBe(20);
      });
    });

    describe('getLowStockItems', () => {
      it('should return low stock items', async () => {
        const alerts = [{ id: 'alert-1', companyId: mockCompanyId, productId: 'p1', threshold: 20, autoReorderQuantity: 100, isActive: true, lastAlertDate: undefined, createdAt: new Date(), updatedAt: new Date() }];
        jest.spyOn(alertRepo, 'find').mockResolvedValue(alerts as any);

        const mockQueryBuilder = {
          where: jest.fn().mockReturnThis(),
          andWhere: jest.fn().mockReturnThis(),
          select: jest.fn().mockReturnThis(),
          getRawOne: jest.fn().mockResolvedValue({ total: 15 }),
        };

        jest.spyOn(inventoryRepo, 'createQueryBuilder').mockReturnValue(mockQueryBuilder as any);

        const result = await service.getLowStockItems(mockCompanyId);

        expect(result).toHaveLength(1);
        expect(result[0].currentStock).toBeLessThanOrEqual(result[0].threshold);
      });
    });

    describe('triggerAutoReorder', () => {
      it('should trigger auto reorder', async () => {
        const alert = { id: 'alert-1', companyId: mockCompanyId, productId: mockProductId, threshold: 20, autoReorderQuantity: 100, isActive: true, lastAlertDate: undefined, createdAt: new Date(), updatedAt: new Date() };
        jest.spyOn(alertRepo, 'findOne').mockResolvedValue(alert as any);
        jest.spyOn(alertRepo, 'save').mockResolvedValue(alert as any);

        const result = await service.triggerAutoReorder(mockCompanyId, mockProductId, 15);

        expect(result.productId).toBe(mockProductId);
        expect(result.reorderQuantity).toBe(100);
      });
    });
  });

  // ============ Inventory Valuation Tests ============

  describe('Inventory Valuation', () => {
    describe('calculateInventoryCost', () => {
      it('should calculate FIFO cost', async () => {
        const history: InventoryValuationHistory[] = [
          { id: '1', companyId: mockCompanyId, warehouseId: 'wh-1', productId: mockProductId, quantity: 100, unitCost: new Decimal('10'), totalCost: new Decimal('1000'), remainingQuantity: 50, receivedDate: new Date('2024-01-01') },
        ];

        jest.spyOn(valuationHistoryRepo, 'find').mockResolvedValue(history);

        const result = await service.calculateInventoryCost(mockCompanyId, ValuationMethod.FIFO);

        expect(result.toNumber()).toBeGreaterThan(0);
      });

      it('should calculate LIFO cost', async () => {
        const history: InventoryValuationHistory[] = [
          { id: '1', companyId: mockCompanyId, warehouseId: 'wh-1', productId: mockProductId, quantity: 100, unitCost: new Decimal('10'), totalCost: new Decimal('1000'), remainingQuantity: 50, receivedDate: new Date('2024-01-01') },
        ];

        jest.spyOn(valuationHistoryRepo, 'find').mockResolvedValue(history);

        const result = await service.calculateInventoryCost(mockCompanyId, ValuationMethod.LIFO);

        expect(result.toNumber()).toBeGreaterThan(0);
      });

      it('should calculate WAC', async () => {
        const history: InventoryValuationHistory[] = [
          { id: '1', companyId: mockCompanyId, warehouseId: 'wh-1', productId: mockProductId, quantity: 100, unitCost: new Decimal('10'), totalCost: new Decimal('1000'), remainingQuantity: 50, receivedDate: new Date('2024-01-01') },
        ];

        jest.spyOn(valuationHistoryRepo, 'find').mockResolvedValue(history);

        const result = await service.calculateInventoryCost(mockCompanyId, ValuationMethod.WAC);

        expect(result.toNumber()).toBeGreaterThan(0);
      });
    });

    describe('getInventoryValue', () => {
      it('should get total inventory value', async () => {
        const inventories = [
          { id: 'inv-1', companyId: mockCompanyId, warehouseId: 'wh-1', productId: 'p1', quantity: 100, unitCost: new Decimal('10'), shelf: 'A-1', isLocked: false, createdAt: new Date(), updatedAt: new Date() },
        ];

        const mockQueryBuilder = {
          createQueryBuilder: jest.fn().mockReturnThis(),
          where: jest.fn().mockReturnThis(),
          andWhere: jest.fn().mockReturnThis(),
          getMany: jest.fn().mockResolvedValue(inventories),
        };

        jest.spyOn(inventoryRepo, 'createQueryBuilder').mockReturnValue(mockQueryBuilder as any);

        // Mock implementation properly
        const result = await service.getInventoryValue(mockCompanyId);

        expect(result).toBeDefined();
      });
    });

    describe('getInventoryTurnover', () => {
      it('should calculate inventory turnover', async () => {
        const mockQueryBuilder = {
          createQueryBuilder: jest.fn().mockReturnThis(),
          where: jest.fn().mockReturnThis(),
          select: jest.fn().mockReturnThis(),
          getRawOne: jest.fn().mockResolvedValue({ avg: 500 }),
        };

        jest.spyOn(inventoryRepo, 'createQueryBuilder').mockReturnValue(mockQueryBuilder as any);

        const result = await service.getInventoryTurnover(mockCompanyId, 30);

        expect(result).toBeDefined();
      });
    });
  });

  // ============ Warehouse Management Tests ============

  describe('Warehouse Management', () => {
    describe('createWarehouse', () => {
      it('should create a warehouse', async () => {
        const mockWarehouse = {
          id: 'wh-1',
          companyId: mockCompanyId,
          name: 'Main Warehouse',
          location: 'NYC',
          capacity: new Decimal('5000'),
          usedCapacity: new Decimal('0'),
          isActive: true,
          createdAt: new Date(),
          updatedAt: new Date(),
        };

        jest.spyOn(warehouseRepo, 'create').mockReturnValue(mockWarehouse as any);
        jest.spyOn(warehouseRepo, 'save').mockResolvedValue(mockWarehouse as any);

        const result = await service.createWarehouse(
          mockCompanyId,
          'Main Warehouse',
          'NYC',
          5000,
        );

        expect(result.name).toBe('Main Warehouse');
        expect(result.isActive).toBe(true);
      });

      it('should throw error for invalid capacity', async () => {
        await expect(
          service.createWarehouse(mockCompanyId, 'WH', 'NYC', 0),
        ).rejects.toThrow(BadRequestException);
      });
    });

    describe('getWarehouseInventory', () => {
      it('should get warehouse inventory', async () => {
        const inventories = [
          { id: 'inv-1', companyId: mockCompanyId, warehouseId: 'wh-1', productId: 'p1', quantity: 100, unitCost: new Decimal('10'), shelf: 'A-1', isLocked: false, createdAt: new Date(), updatedAt: new Date() },
        ];

        jest.spyOn(inventoryRepo, 'find').mockResolvedValue(inventories as any);

        const result = await service.getWarehouseInventory(mockCompanyId, 'wh-1');

        expect(result).toHaveLength(1);
        expect(result[0].productId).toBe('p1');
      });
    });

    describe('getWarehouseCapacity', () => {
      it('should get warehouse capacity', async () => {
        const warehouse: Warehouse = { id: 'wh-1', companyId: mockCompanyId, name: 'WH1', location: 'NYC', capacity: new Decimal(1000), usedCapacity: new Decimal(0), isActive: true, createdAt: new Date(), updatedAt: new Date() };
        jest.spyOn(warehouseRepo, 'findOne').mockResolvedValue(warehouse);

        const inventories = [
          { id: 'inv-1', companyId: mockCompanyId, warehouseId: 'wh-1', productId: 'p1', quantity: 200, unitCost: new Decimal('10'), shelf: 'A-1', isLocked: false, createdAt: new Date(), updatedAt: new Date() },
        ];

        jest.spyOn(inventoryRepo, 'find').mockResolvedValue(inventories as any);

        const result = await service.getWarehouseCapacity(mockCompanyId, 'wh-1');

        expect(result.used).toBe(200);
        expect(result.total).toBe(1000);
        expect(result.utilization).toBe(20);
      });
    });
  });

  // ============ Multi-location Tracking Tests ============

  describe('Multi-location Tracking', () => {
    describe('getProductLocations', () => {
      it('should get product locations across warehouses', async () => {
        const locations = [
          { id: 'inv-1', companyId: mockCompanyId, warehouseId: 'wh-1', productId: mockProductId, quantity: 100, unitCost: new Decimal('10'), shelf: 'A-1', isLocked: false, createdAt: new Date(), updatedAt: new Date() },
          { id: 'inv-2', companyId: mockCompanyId, warehouseId: 'wh-2', productId: mockProductId, quantity: 50, unitCost: new Decimal('10'), shelf: 'B-1', isLocked: false, createdAt: new Date(), updatedAt: new Date() },
        ];

        jest.spyOn(inventoryRepo, 'find').mockResolvedValue(locations as any);

        const result = await service.getProductLocations(mockCompanyId, mockProductId);

        expect(result).toHaveLength(2);
        expect(result[0].warehouseId).toBe('wh-1');
      });
    });

    describe('updateProductLocation', () => {
      it('should update product location', async () => {
        const inventory: WarehouseInventory = { id: 'inv-1', companyId: mockCompanyId, warehouseId: 'wh-1', productId: mockProductId, quantity: 100, unitCost: new Decimal('10'), shelf: 'A-1', isLocked: false, createdAt: new Date(), updatedAt: new Date() };

        jest.spyOn(inventoryRepo, 'findOne').mockResolvedValue(inventory);
        jest.spyOn(inventoryRepo, 'save').mockResolvedValue(inventory);

        await service.updateProductLocation(
          mockCompanyId,
          mockProductId,
          'wh-1',
          'B-2',
          150,
        );

        expect(inventory.shelf).toBe('B-2');
        expect(inventory.quantity).toBe(150);
      });

      it('should throw error for negative quantity', async () => {
        await expect(
          service.updateProductLocation(mockCompanyId, mockProductId, 'wh-1', 'A-1', -10),
        ).rejects.toThrow(BadRequestException);
      });
    });
  });
});
