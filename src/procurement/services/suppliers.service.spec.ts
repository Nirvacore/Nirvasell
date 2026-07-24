import { Test, TestingModule } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Decimal } from 'decimal.js';
import { SuppliersService } from './suppliers.service';
import { Supplier } from '../entities/supplier.entity';
import { PurchaseOrder } from '../entities/purchase-order.entity';
import { Quotation } from '../entities/quotation.entity';
import { Payment } from '../entities/payment.entity';
import { BadRequestException, NotFoundException, ConflictException } from '@nestjs/common';

describe('SuppliersService', () => {
  let service: SuppliersService;
  let supplierRepo: Repository<Supplier>;
  let poRepo: Repository<PurchaseOrder>;
  let quotationRepo: Repository<Quotation>;
  let paymentRepo: Repository<Payment>;

  const mockCompanyId = 'company-123';
  const mockSupplierId = 'supplier-456';
  const mockPoId = 'po-789';
  const mockQuotationId = 'quotation-101';

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        SuppliersService,
        {
          provide: getRepositoryToken(Supplier),
          useValue: {
            findOne: jest.fn(),
            find: jest.fn(),
            findAndCount: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
          },
        },
        {
          provide: getRepositoryToken(PurchaseOrder),
          useValue: {
            findOne: jest.fn(),
            find: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
          },
        },
        {
          provide: getRepositoryToken(Quotation),
          useValue: {
            findOne: jest.fn(),
            find: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
          },
        },
        {
          provide: getRepositoryToken(Payment),
          useValue: {
            findOne: jest.fn(),
            find: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
          },
        },
      ],
    }).compile();

    service = module.get<SuppliersService>(SuppliersService);
    supplierRepo = module.get<Repository<Supplier>>(getRepositoryToken(Supplier));
    poRepo = module.get<Repository<PurchaseOrder>>(getRepositoryToken(PurchaseOrder));
    quotationRepo = module.get<Repository<Quotation>>(getRepositoryToken(Quotation));
    paymentRepo = module.get<Repository<Payment>>(getRepositoryToken(Payment));
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  // ============ SUPPLIER CRUD TESTS ============

  describe('createSupplier', () => {
    it('should create a supplier successfully', async () => {
      const mockSupplier = {
        id: mockSupplierId,
        companyId: mockCompanyId,
        name: 'Test Supplier',
        contact: 'John Doe',
        email: 'john@supplier.com',
        phone: '123456789',
        paymentTerms: 'net30',
        rating: new Decimal(4.5),
        isActive: true,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      jest.spyOn(supplierRepo, 'findOne').mockResolvedValue(null);
      jest.spyOn(supplierRepo, 'create').mockReturnValue(mockSupplier);
      jest.spyOn(supplierRepo, 'save').mockResolvedValue(mockSupplier);

      const result = await service.createSupplier(
        mockCompanyId,
        'Test Supplier',
        'John Doe',
        'john@supplier.com',
        '123456789',
        'net30',
        4.5,
      );

      expect(result).toEqual(mockSupplier);
      expect(supplierRepo.findOne).toHaveBeenCalledWith({
        where: { companyId: mockCompanyId, email: 'john@supplier.com' },
      });
    });

    it('should throw ConflictException if supplier email already exists', async () => {
      jest.spyOn(supplierRepo, 'findOne').mockResolvedValue({
        id: 'existing-id',
      } as Supplier);

      await expect(
        service.createSupplier(
          mockCompanyId,
          'Test',
          'John',
          'john@supplier.com',
          '123456789',
          'net30',
        ),
      ).rejects.toThrow(ConflictException);
    });

    it('should throw BadRequestException for invalid payment terms', async () => {
      jest.spyOn(supplierRepo, 'findOne').mockResolvedValue(null);

      await expect(
        service.createSupplier(
          mockCompanyId,
          'Test',
          'John',
          'john@supplier.com',
          '123456789',
          'invalid_term',
        ),
      ).rejects.toThrow(BadRequestException);
    });

    it('should throw BadRequestException for invalid rating', async () => {
      jest.spyOn(supplierRepo, 'findOne').mockResolvedValue(null);

      await expect(
        service.createSupplier(
          mockCompanyId,
          'Test',
          'John',
          'john@supplier.com',
          '123456789',
          'net30',
          6, // Invalid rating > 5
        ),
      ).rejects.toThrow(BadRequestException);
    });
  });

  describe('getSupplier', () => {
    it('should return a supplier by ID', async () => {
      const mockSupplier = {
        id: mockSupplierId,
        companyId: mockCompanyId,
      } as Supplier;

      jest.spyOn(supplierRepo, 'findOne').mockResolvedValue(mockSupplier);

      const result = await service.getSupplier(mockCompanyId, mockSupplierId);

      expect(result).toEqual(mockSupplier);
      expect(supplierRepo.findOne).toHaveBeenCalledWith({
        where: { id: mockSupplierId, companyId: mockCompanyId },
      });
    });

    it('should throw NotFoundException if supplier not found', async () => {
      jest.spyOn(supplierRepo, 'findOne').mockResolvedValue(null);

      await expect(service.getSupplier(mockCompanyId, 'unknown-id')).rejects.toThrow(
        NotFoundException,
      );
    });
  });

  describe('listSuppliers', () => {
    it('should list suppliers with pagination', async () => {
      const mockSuppliers = [
        { id: 'sup-1', companyId: mockCompanyId } as Supplier,
        { id: 'sup-2', companyId: mockCompanyId } as Supplier,
      ];

      jest.spyOn(supplierRepo, 'findAndCount').mockResolvedValue([mockSuppliers, 2]);

      const result = await service.listSuppliers(mockCompanyId, 10, 0);

      expect(result.suppliers).toEqual(mockSuppliers);
      expect(result.total).toBe(2);
      expect(supplierRepo.findAndCount).toHaveBeenCalledWith({
        where: { companyId: mockCompanyId, isActive: true },
        skip: 0,
        take: 10,
        order: { createdAt: 'DESC' },
      });
    });

    it('should handle empty supplier list', async () => {
      jest.spyOn(supplierRepo, 'findAndCount').mockResolvedValue([[], 0]);

      const result = await service.listSuppliers(mockCompanyId);

      expect(result.suppliers).toEqual([]);
      expect(result.total).toBe(0);
    });
  });

  describe('updateSupplier', () => {
    it('should update supplier details', async () => {
      const existingSupplier = {
        id: mockSupplierId,
        companyId: mockCompanyId,
        name: 'Old Name',
        rating: new Decimal(3),
      } as Supplier;

      const updatedSupplier = {
        ...existingSupplier,
        name: 'New Name',
        rating: new Decimal(4),
      };

      jest.spyOn(supplierRepo, 'findOne').mockResolvedValue(existingSupplier);
      jest.spyOn(supplierRepo, 'save').mockResolvedValue(updatedSupplier);

      const result = await service.updateSupplier(mockCompanyId, mockSupplierId, {
        name: 'New Name',
        rating: new Decimal(4),
      });

      expect(result.name).toBe('New Name');
      expect(supplierRepo.save).toHaveBeenCalled();
    });

    it('should throw BadRequestException for invalid rating update', async () => {
      const existingSupplier = {
        id: mockSupplierId,
        companyId: mockCompanyId,
      } as Supplier;

      jest.spyOn(supplierRepo, 'findOne').mockResolvedValue(existingSupplier);

      await expect(
        service.updateSupplier(mockCompanyId, mockSupplierId, {
          rating: new Decimal(6), // Invalid
        }),
      ).rejects.toThrow(BadRequestException);
    });
  });

  describe('deactivateSupplier', () => {
    it('should deactivate a supplier', async () => {
      const supplier = {
        id: mockSupplierId,
        companyId: mockCompanyId,
        isActive: true,
      } as Supplier;

      jest.spyOn(supplierRepo, 'findOne').mockResolvedValue(supplier);
      jest.spyOn(supplierRepo, 'save').mockResolvedValue({
        ...supplier,
        isActive: false,
      });

      const result = await service.deactivateSupplier(mockCompanyId, mockSupplierId);

      expect(result.isActive).toBe(false);
    });
  });

  // ============ PURCHASE ORDER TESTS ============

  describe('createPO', () => {
    it('should create a purchase order successfully', async () => {
      const supplier = { id: mockSupplierId, companyId: mockCompanyId } as Supplier;
      const items = [
        { description: 'Product A', quantity: 10, unitPrice: new Decimal(100) },
      ];

      jest.spyOn(supplierRepo, 'findOne').mockResolvedValue(supplier);
      jest.spyOn(poRepo, 'create').mockReturnValue({
        id: mockPoId,
        companyId: mockCompanyId,
        supplierId: mockSupplierId,
        status: 'draft',
      } as any);
      jest.spyOn(poRepo, 'save').mockResolvedValue({
        id: mockPoId,
        totalAmount: new Decimal(1000),
      } as PurchaseOrder);

      const result = await service.createPO(mockCompanyId, mockSupplierId, items);

      expect(result.id).toBe(mockPoId);
      expect(poRepo.save).toHaveBeenCalled();
    });

    it('should throw BadRequestException for empty items', async () => {
      const supplier = { id: mockSupplierId } as Supplier;
      jest.spyOn(supplierRepo, 'findOne').mockResolvedValue(supplier);

      await expect(service.createPO(mockCompanyId, mockSupplierId, [])).rejects.toThrow(
        BadRequestException,
      );
    });

    it('should calculate correct total amount', async () => {
      const supplier = { id: mockSupplierId } as Supplier;
      const items = [
        { description: 'Item 1', quantity: 5, unitPrice: new Decimal(50) },
        { description: 'Item 2', quantity: 3, unitPrice: new Decimal(100) },
      ];

      jest.spyOn(supplierRepo, 'findOne').mockResolvedValue(supplier);
      let capturedPO: any;
      jest.spyOn(poRepo, 'create').mockImplementation(po => {
        capturedPO = po;
        return po as any;
      });
      jest.spyOn(poRepo, 'save').mockResolvedValue({} as PurchaseOrder);

      await service.createPO(mockCompanyId, mockSupplierId, items);

      // Total should be (5*50) + (3*100) = 250 + 300 = 550
      expect(capturedPO.totalAmount.toNumber()).toBe(550);
    });
  });

  describe('updatePOStatus', () => {
    it('should update PO status', async () => {
      const po = {
        id: mockPoId,
        companyId: mockCompanyId,
        status: 'draft',
      } as PurchaseOrder;

      jest.spyOn(poRepo, 'findOne').mockResolvedValue(po);
      jest.spyOn(poRepo, 'save').mockResolvedValue({
        ...po,
        status: 'submitted',
      });

      const result = await service.updatePOStatus(mockCompanyId, mockPoId, 'submitted');

      expect(result.status).toBe('submitted');
    });

    it('should throw BadRequestException for invalid status', async () => {
      await expect(
        service.updatePOStatus(mockCompanyId, mockPoId, 'invalid_status'),
      ).rejects.toThrow(BadRequestException);
    });

    it('should throw NotFoundException if PO not found', async () => {
      jest.spyOn(poRepo, 'findOne').mockResolvedValue(null);

      await expect(
        service.updatePOStatus(mockCompanyId, 'unknown-po', 'submitted'),
      ).rejects.toThrow(NotFoundException);
    });
  });

  describe('getPOsByStatus', () => {
    it('should return POs by status', async () => {
      const pos = [
        { id: 'po-1', status: 'submitted' } as PurchaseOrder,
        { id: 'po-2', status: 'submitted' } as PurchaseOrder,
      ];

      jest.spyOn(poRepo, 'find').mockResolvedValue(pos);

      const result = await service.getPOsByStatus(mockCompanyId, 'submitted');

      expect(result).toEqual(pos);
      expect(result.length).toBe(2);
    });
  });

  describe('getSupplierPOs', () => {
    it('should return all POs for a supplier', async () => {
      const pos = [
        { id: 'po-1', supplierId: mockSupplierId } as PurchaseOrder,
        { id: 'po-2', supplierId: mockSupplierId } as PurchaseOrder,
      ];

      jest.spyOn(poRepo, 'find').mockResolvedValue(pos);

      const result = await service.getSupplierPOs(mockCompanyId, mockSupplierId);

      expect(result).toEqual(pos);
      expect(result.length).toBe(2);
    });
  });

  // ============ QUOTATION TESTS ============

  describe('requestQuotation', () => {
    it('should create a quotation', async () => {
      const supplier = { id: mockSupplierId } as Supplier;
      const items = [{ description: 'Item', quantity: 5, unitPrice: new Decimal(50) }];

      jest.spyOn(supplierRepo, 'findOne').mockResolvedValue(supplier);
      jest.spyOn(quotationRepo, 'create').mockReturnValue({
        id: mockQuotationId,
        status: 'pending',
      } as any);
      jest.spyOn(quotationRepo, 'save').mockResolvedValue({
        id: mockQuotationId,
      } as Quotation);

      const result = await service.requestQuotation(mockCompanyId, mockSupplierId, items);

      expect(result.id).toBe(mockQuotationId);
      expect(quotationRepo.save).toHaveBeenCalled();
    });

    it('should throw BadRequestException for empty items', async () => {
      const supplier = { id: mockSupplierId } as Supplier;
      jest.spyOn(supplierRepo, 'findOne').mockResolvedValue(supplier);

      await expect(
        service.requestQuotation(mockCompanyId, mockSupplierId, []),
      ).rejects.toThrow(BadRequestException);
    });
  });

  describe('acceptQuotation', () => {
    it('should accept quotation and create PO', async () => {
      const quotation = {
        id: mockQuotationId,
        companyId: mockCompanyId,
        supplierId: mockSupplierId,
        status: 'pending',
        validUntil: new Date(Date.now() + 86400000), // Tomorrow
        items: [{ description: 'Item', quantity: 5, unitPrice: new Decimal(50) }],
        totalAmount: new Decimal(250),
      } as Quotation;

      jest.spyOn(quotationRepo, 'findOne').mockResolvedValue(quotation);
      jest.spyOn(supplierRepo, 'findOne').mockResolvedValue({
        id: mockSupplierId,
      } as Supplier);
      jest.spyOn(poRepo, 'create').mockReturnValue({ id: mockPoId } as any);
      jest.spyOn(poRepo, 'save').mockResolvedValue({
        id: mockPoId,
        totalAmount: new Decimal(250),
      } as PurchaseOrder);
      jest.spyOn(quotationRepo, 'save').mockResolvedValue({
        ...quotation,
        status: 'accepted',
        poId: mockPoId,
      });

      const result = await service.acceptQuotation(mockCompanyId, mockQuotationId);

      expect(result.id).toBe(mockPoId);
    });

    it('should throw error for expired quotation', async () => {
      const quotation = {
        id: mockQuotationId,
        companyId: mockCompanyId,
        status: 'pending',
        validUntil: new Date(Date.now() - 86400000), // Yesterday
      } as Quotation;

      jest.spyOn(quotationRepo, 'findOne').mockResolvedValue(quotation);

      await expect(
        service.acceptQuotation(mockCompanyId, mockQuotationId),
      ).rejects.toThrow(BadRequestException);
    });
  });

  describe('rejectQuotation', () => {
    it('should reject a quotation', async () => {
      const quotation = {
        id: mockQuotationId,
        companyId: mockCompanyId,
        status: 'pending',
      } as Quotation;

      jest.spyOn(quotationRepo, 'findOne').mockResolvedValue(quotation);
      jest.spyOn(quotationRepo, 'save').mockResolvedValue({
        ...quotation,
        status: 'rejected',
      });

      const result = await service.rejectQuotation(mockCompanyId, mockQuotationId);

      expect(result.status).toBe('rejected');
    });
  });

  describe('compareQuotations', () => {
    it('should compare multiple quotations', async () => {
      const quotations = [
        { id: 'qt-1', totalAmount: new Decimal(100) } as Quotation,
        { id: 'qt-2', totalAmount: new Decimal(150) } as Quotation,
      ];

      jest.spyOn(quotationRepo, 'find').mockResolvedValue(quotations);

      const result = await service.compareQuotations(mockCompanyId, ['qt-1', 'qt-2']);

      expect(result.length).toBe(2);
      expect(result[0].totalAmount.toNumber()).toBe(100); // Lowest price first
    });

    it('should throw error for less than 2 quotations', async () => {
      await expect(
        service.compareQuotations(mockCompanyId, ['qt-1']),
      ).rejects.toThrow(BadRequestException);
    });
  });

  // ============ PAYMENT TESTS ============

  describe('recordPayment', () => {
    it('should record a payment', async () => {
      const po = {
        id: mockPoId,
        companyId: mockCompanyId,
        supplierId: mockSupplierId,
        totalAmount: new Decimal(1000),
        paymentsMade: 0,
        deductedAmount: 0,
      } as PurchaseOrder;

      jest.spyOn(poRepo, 'findOne').mockResolvedValue(po);
      jest.spyOn(paymentRepo, 'create').mockReturnValue({ id: 'payment-1' } as any);
      jest.spyOn(paymentRepo, 'save').mockResolvedValue({
        id: 'payment-1',
        amount: new Decimal(500),
      } as Payment);
      jest.spyOn(poRepo, 'save').mockResolvedValue(po);

      const result = await service.recordPayment(
        mockCompanyId,
        mockPoId,
        new Decimal(500),
        'partial',
        'INV-001',
      );

      expect(result.amount).toEqual(new Decimal(500));
      expect(paymentRepo.save).toHaveBeenCalled();
    });

    it('should throw error for payment exceeding balance', async () => {
      const po = {
        id: mockPoId,
        companyId: mockCompanyId,
        totalAmount: new Decimal(1000),
        paymentsMade: 900,
        deductedAmount: 0,
      } as PurchaseOrder;

      jest.spyOn(poRepo, 'findOne').mockResolvedValue(po);

      await expect(
        service.recordPayment(
          mockCompanyId,
          mockPoId,
          new Decimal(200), // Exceeds balance
          'partial',
          'INV-001',
        ),
      ).rejects.toThrow(BadRequestException);
    });

    it('should throw error for invalid payment type', async () => {
      const po = { id: mockPoId, companyId: mockCompanyId } as PurchaseOrder;
      jest.spyOn(poRepo, 'findOne').mockResolvedValue(po);

      await expect(
        service.recordPayment(
          mockCompanyId,
          mockPoId,
          new Decimal(500),
          'invalid_type',
          'INV-001',
        ),
      ).rejects.toThrow(BadRequestException);
    });
  });

  describe('getPaymentHistory', () => {
    it('should return payment history for supplier', async () => {
      const payments = [
        { id: 'pay-1', amount: new Decimal(500) } as Payment,
        { id: 'pay-2', amount: new Decimal(300) } as Payment,
      ];

      jest.spyOn(paymentRepo, 'find').mockResolvedValue(payments);

      const result = await service.getPaymentHistory(mockCompanyId, mockSupplierId);

      expect(result).toEqual(payments);
      expect(result.length).toBe(2);
    });
  });

  // ============ ANALYTICS TESTS ============

  describe('getSupplierMetrics', () => {
    it('should calculate supplier metrics', async () => {
      const supplier = { id: mockSupplierId, rating: new Decimal(4.5) } as Supplier;
      const pos = [
        {
          id: 'po-1',
          status: 'received',
          totalAmount: new Decimal(1000),
          createdAt: new Date(Date.now() - 14 * 86400000),
          deliveryDate: new Date(Date.now() - 7 * 86400000),
        } as PurchaseOrder,
      ];

      jest.spyOn(supplierRepo, 'findOne').mockResolvedValue(supplier);
      jest.spyOn(poRepo, 'find').mockResolvedValue(pos);

      const result = await service.getSupplierMetrics(mockCompanyId, mockSupplierId);

      expect(result.totalPOs).toBe(1);
      expect(result.qualityScore).toBe(4.5);
      expect(result.onTimeDeliveryRate).toBe(100);
    });
  });

  describe('getTopSuppliers', () => {
    it('should return top suppliers by rating', async () => {
      const suppliers = [
        { id: 'sup-1', rating: new Decimal(5), isActive: true } as Supplier,
        { id: 'sup-2', rating: new Decimal(4), isActive: true } as Supplier,
        { id: 'sup-3', rating: new Decimal(3), isActive: true } as Supplier,
      ];

      jest.spyOn(supplierRepo, 'find').mockResolvedValue(suppliers);

      const result = await service.getTopSuppliers(mockCompanyId, 'rating', 2);

      expect(result.length).toBe(2);
      expect(result[0].rating.toNumber()).toBe(5);
    });

    it('should return top suppliers by frequency', async () => {
      const suppliers = [
        { id: 'sup-1', isActive: true } as Supplier,
        { id: 'sup-2', isActive: true } as Supplier,
      ];

      jest.spyOn(supplierRepo, 'find').mockResolvedValue(suppliers);
      jest.spyOn(poRepo, 'find').mockResolvedValue([{ id: 'po-1' } as PurchaseOrder]);

      const result = await service.getTopSuppliers(mockCompanyId, 'frequency', 10);

      expect(result.length).toBeGreaterThan(0);
    });
  });

  describe('calculateOutstandingBalance', () => {
    it('should calculate correct outstanding balance', () => {
      const po = {
        totalAmount: new Decimal(1000),
        paymentsMade: 600,
        deductedAmount: 100,
      } as PurchaseOrder;

      const balance = service.calculateOutstandingBalance(po);

      expect(balance.toNumber()).toBe(300); // 1000 - 600 - 100
    });

    it('should handle zero balance', () => {
      const po = {
        totalAmount: new Decimal(1000),
        paymentsMade: 1000,
        deductedAmount: 0,
      } as PurchaseOrder;

      const balance = service.calculateOutstandingBalance(po);

      expect(balance.toNumber()).toBe(0);
    });
  });
});
