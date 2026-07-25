import { Test, TestingModule } from '@nestjs/testing';
import { PrismaService } from '@nestjs/prisma';
import { Decimal } from 'decimal.js';
import { SuppliersService } from './suppliers.service';
import { BadRequestException, NotFoundException, ConflictException } from '@nestjs/common';

describe('SuppliersService', () => {
  let service: SuppliersService;
  let prisma: PrismaService;

  const mockCompanyId = 'company-123';
  const mockSupplierId = 'supplier-456';
  const mockPoId = 'po-789';
  const mockQuotationId = 'quotation-101';

  const mockSupplier = {
    id: mockSupplierId,
    companyId: mockCompanyId,
    name: 'Test Supplier',
    contact: 'John Doe',
    email: 'john@supplier.com',
    phone: '123456789',
    paymentTerms: 'net30',
    rating: new Decimal(4.5),
    address: '123 Street',
    city: 'City',
    country: 'Country',
    taxId: 'TAX123',
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        SuppliersService,
        {
          provide: PrismaService,
          useValue: {
            supplier: {
              findUnique: jest.fn(),
              findFirst: jest.fn(),
              findMany: jest.fn(),
              count: jest.fn(),
              create: jest.fn(),
              update: jest.fn(),
              delete: jest.fn(),
            },
            purchaseOrder: {
              findFirst: jest.fn(),
              findMany: jest.fn(),
              create: jest.fn(),
              update: jest.fn(),
              delete: jest.fn(),
            },
            quotation: {
              findFirst: jest.fn(),
              findMany: jest.fn(),
              create: jest.fn(),
              update: jest.fn(),
              delete: jest.fn(),
            },
            payment: {
              findMany: jest.fn(),
              create: jest.fn(),
              update: jest.fn(),
              delete: jest.fn(),
            },
            $transaction: jest.fn(),
          },
        },
      ],
    }).compile();

    service = module.get<SuppliersService>(SuppliersService);
    prisma = module.get<PrismaService>(PrismaService);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  // ============ SUPPLIER CRUD TESTS ============

  describe('createSupplier', () => {
    it('should create a supplier successfully', async () => {
      jest.spyOn(prisma.supplier, 'findUnique').mockResolvedValue(null);
      jest.spyOn(prisma.supplier, 'create').mockResolvedValue(mockSupplier);

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
      expect(prisma.supplier.create).toHaveBeenCalledWith({
        data: {
          companyId: mockCompanyId,
          name: 'Test Supplier',
          contact: 'John Doe',
          email: 'john@supplier.com',
          phone: '123456789',
          paymentTerms: 'net30',
          rating: expect.any(Decimal),
        },
      });
    });

    it('should throw ConflictException if supplier email already exists', async () => {
      jest.spyOn(prisma.supplier, 'findUnique').mockResolvedValue(mockSupplier);

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
      jest.spyOn(prisma.supplier, 'findUnique').mockResolvedValue(null);

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
      jest.spyOn(prisma.supplier, 'findUnique').mockResolvedValue(null);

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
      jest.spyOn(prisma.supplier, 'findFirst').mockResolvedValue(mockSupplier);

      const result = await service.getSupplier(mockCompanyId, mockSupplierId);

      expect(result).toEqual(mockSupplier);
      expect(prisma.supplier.findFirst).toHaveBeenCalledWith({
        where: { id: mockSupplierId, companyId: mockCompanyId },
      });
    });

    it('should throw NotFoundException if supplier not found', async () => {
      jest.spyOn(prisma.supplier, 'findFirst').mockResolvedValue(null);

      await expect(service.getSupplier(mockCompanyId, 'unknown-id')).rejects.toThrow(
        NotFoundException,
      );
    });
  });

  describe('listSuppliers', () => {
    it('should list suppliers with pagination', async () => {
      const mockSuppliers = [
        { id: 'sup-1', companyId: mockCompanyId },
        { id: 'sup-2', companyId: mockCompanyId },
      ];

      jest.spyOn(prisma.supplier, 'findMany').mockResolvedValue(mockSuppliers as any);
      jest.spyOn(prisma.supplier, 'count').mockResolvedValue(2);

      const result = await service.listSuppliers(mockCompanyId, 10, 0);

      expect(result.suppliers).toEqual(mockSuppliers);
      expect(result.total).toBe(2);
      expect(prisma.supplier.findMany).toHaveBeenCalledWith({
        where: { companyId: mockCompanyId, isActive: true },
        skip: 0,
        take: 10,
        orderBy: { createdAt: 'desc' },
      });
      expect(prisma.supplier.count).toHaveBeenCalledWith({
        where: { companyId: mockCompanyId, isActive: true },
      });
    });

    it('should handle empty supplier list', async () => {
      jest.spyOn(prisma.supplier, 'findMany').mockResolvedValue([]);
      jest.spyOn(prisma.supplier, 'count').mockResolvedValue(0);

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
      };

      const updatedSupplier = {
        ...existingSupplier,
        name: 'New Name',
        rating: new Decimal(4),
      };

      jest.spyOn(prisma.supplier, 'findFirst').mockResolvedValue(existingSupplier as any);
      jest.spyOn(prisma.supplier, 'update').mockResolvedValue(updatedSupplier as any);

      const result = await service.updateSupplier(mockCompanyId, mockSupplierId, {
        name: 'New Name',
        rating: new Decimal(4),
      });

      expect(result.name).toBe('New Name');
      expect(prisma.supplier.update).toHaveBeenCalled();
    });

    it('should throw BadRequestException for invalid rating update', async () => {
      jest.spyOn(prisma.supplier, 'findFirst').mockResolvedValue(mockSupplier);

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
      };

      jest.spyOn(prisma.supplier, 'findFirst').mockResolvedValue(supplier as any);
      jest.spyOn(prisma.supplier, 'update').mockResolvedValue({
        ...supplier,
        isActive: false,
      } as any);

      const result = await service.deactivateSupplier(mockCompanyId, mockSupplierId);

      expect(result.isActive).toBe(false);
      expect(prisma.supplier.update).toHaveBeenCalledWith({
        where: { id: mockSupplierId },
        data: { isActive: false },
      });
    });
  });

  // ============ PURCHASE ORDER TESTS ============

  describe('createPO', () => {
    it('should create a purchase order successfully', async () => {
      const items = [
        { description: 'Product A', quantity: 10, unitPrice: new Decimal(100) },
      ];

      const mockPO = {
        id: mockPoId,
        companyId: mockCompanyId,
        supplierId: mockSupplierId,
        status: 'draft',
        totalAmount: new Decimal(1000),
      };

      jest.spyOn(prisma.supplier, 'findFirst').mockResolvedValue(mockSupplier);
      jest.spyOn(prisma.purchaseOrder, 'create').mockResolvedValue(mockPO as any);

      const result = await service.createPO(mockCompanyId, mockSupplierId, items);

      expect(result.id).toBe(mockPoId);
      expect(prisma.purchaseOrder.create).toHaveBeenCalled();
    });

    it('should throw BadRequestException for empty items', async () => {
      jest.spyOn(prisma.supplier, 'findFirst').mockResolvedValue(mockSupplier);

      await expect(service.createPO(mockCompanyId, mockSupplierId, [])).rejects.toThrow(
        BadRequestException,
      );
    });

    it('should calculate correct total amount', async () => {
      const items = [
        { description: 'Item 1', quantity: 5, unitPrice: new Decimal(50) },
        { description: 'Item 2', quantity: 3, unitPrice: new Decimal(100) },
      ];

      jest.spyOn(prisma.supplier, 'findFirst').mockResolvedValue(mockSupplier);

      let capturedData: any;
      jest.spyOn(prisma.purchaseOrder, 'create').mockImplementation((args: any) => {
        capturedData = args.data;
        return Promise.resolve({ id: mockPoId, ...args.data } as any);
      });

      await service.createPO(mockCompanyId, mockSupplierId, items);

      // Total should be (5*50) + (3*100) = 250 + 300 = 550
      expect(capturedData.totalAmount.toNumber()).toBe(550);
    });
  });

  describe('updatePOStatus', () => {
    it('should update PO status', async () => {
      const po = {
        id: mockPoId,
        companyId: mockCompanyId,
        status: 'draft',
      };

      jest.spyOn(prisma.purchaseOrder, 'findFirst').mockResolvedValue(po as any);
      jest.spyOn(prisma.purchaseOrder, 'update').mockResolvedValue({
        ...po,
        status: 'submitted',
      } as any);

      const result = await service.updatePOStatus(mockCompanyId, mockPoId, 'submitted');

      expect(result.status).toBe('submitted');
    });

    it('should throw BadRequestException for invalid status', async () => {
      await expect(
        service.updatePOStatus(mockCompanyId, mockPoId, 'invalid_status'),
      ).rejects.toThrow(BadRequestException);
    });

    it('should throw NotFoundException if PO not found', async () => {
      jest.spyOn(prisma.purchaseOrder, 'findFirst').mockResolvedValue(null);

      await expect(
        service.updatePOStatus(mockCompanyId, 'unknown-po', 'submitted'),
      ).rejects.toThrow(NotFoundException);
    });
  });

  describe('getPOsByStatus', () => {
    it('should return POs by status', async () => {
      const pos = [
        { id: 'po-1', status: 'submitted' },
        { id: 'po-2', status: 'submitted' },
      ];

      jest.spyOn(prisma.purchaseOrder, 'findMany').mockResolvedValue(pos as any);

      const result = await service.getPOsByStatus(mockCompanyId, 'submitted');

      expect(result).toEqual(pos);
      expect(result.length).toBe(2);
      expect(prisma.purchaseOrder.findMany).toHaveBeenCalledWith({
        where: { companyId: mockCompanyId, status: 'submitted' },
        orderBy: { createdAt: 'desc' },
      });
    });
  });

  describe('getSupplierPOs', () => {
    it('should return all POs for a supplier', async () => {
      const pos = [
        { id: 'po-1', supplierId: mockSupplierId },
        { id: 'po-2', supplierId: mockSupplierId },
      ];

      jest.spyOn(prisma.purchaseOrder, 'findMany').mockResolvedValue(pos as any);

      const result = await service.getSupplierPOs(mockCompanyId, mockSupplierId);

      expect(result).toEqual(pos);
      expect(result.length).toBe(2);
      expect(prisma.purchaseOrder.findMany).toHaveBeenCalledWith({
        where: { companyId: mockCompanyId, supplierId: mockSupplierId },
        orderBy: { createdAt: 'desc' },
      });
    });
  });

  // ============ QUOTATION TESTS ============

  describe('requestQuotation', () => {
    it('should create a quotation', async () => {
      const items = [{ description: 'Item', quantity: 5, unitPrice: new Decimal(50) }];

      jest.spyOn(prisma.supplier, 'findFirst').mockResolvedValue(mockSupplier);
      jest.spyOn(prisma.quotation, 'create').mockResolvedValue({
        id: mockQuotationId,
        status: 'pending',
      } as any);

      const result = await service.requestQuotation(mockCompanyId, mockSupplierId, items);

      expect(result.id).toBe(mockQuotationId);
      expect(prisma.quotation.create).toHaveBeenCalled();
    });

    it('should throw BadRequestException for empty items', async () => {
      jest.spyOn(prisma.supplier, 'findFirst').mockResolvedValue(mockSupplier);

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
      };

      const mockPO = {
        id: mockPoId,
        totalAmount: new Decimal(250),
      };

      jest.spyOn(prisma.quotation, 'findFirst').mockResolvedValue(quotation as any);
      jest.spyOn(prisma, '$transaction' as any).mockImplementation(async (callback: any) => {
        return callback({
          supplier: {
            findFirst: jest.fn().mockResolvedValue(mockSupplier),
          },
          purchaseOrder: {
            create: jest.fn().mockResolvedValue(mockPO),
          },
          quotation: {
            update: jest.fn().mockResolvedValue({ ...quotation, status: 'accepted', poId: mockPoId }),
          },
        });
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
      };

      jest.spyOn(prisma.quotation, 'findFirst').mockResolvedValue(quotation as any);

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
      };

      jest.spyOn(prisma.quotation, 'findFirst').mockResolvedValue(quotation as any);
      jest.spyOn(prisma.quotation, 'update').mockResolvedValue({
        ...quotation,
        status: 'rejected',
      } as any);

      const result = await service.rejectQuotation(mockCompanyId, mockQuotationId);

      expect(result.status).toBe('rejected');
    });
  });

  describe('compareQuotations', () => {
    it('should compare multiple quotations', async () => {
      const quotations = [
        { id: 'qt-1', totalAmount: new Decimal(100) },
        { id: 'qt-2', totalAmount: new Decimal(150) },
      ];

      jest.spyOn(prisma.quotation, 'findMany').mockResolvedValue(quotations as any);

      const result = await service.compareQuotations(mockCompanyId, ['qt-1', 'qt-2']);

      expect(result.length).toBe(2);
      expect((result[0].totalAmount as any).toNumber()).toBe(100); // Lowest price first
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
        paymentsMade: new Decimal(0),
        deductedAmount: new Decimal(0),
      };

      jest.spyOn(prisma.purchaseOrder, 'findFirst').mockResolvedValue(po as any);
      jest.spyOn(prisma, '$transaction' as any).mockImplementation(async (callback: any) => {
        return callback({
          payment: {
            create: jest.fn().mockResolvedValue({ id: 'payment-1', amount: new Decimal(500) }),
          },
          purchaseOrder: {
            update: jest.fn().mockResolvedValue(po),
          },
        });
      });

      const result = await service.recordPayment(
        mockCompanyId,
        mockPoId,
        new Decimal(500),
        'partial',
        'INV-001',
      );

      expect(result.amount).toEqual(new Decimal(500));
    });

    it('should throw error for payment exceeding balance', async () => {
      const po = {
        id: mockPoId,
        companyId: mockCompanyId,
        totalAmount: new Decimal(1000),
        paymentsMade: new Decimal(900),
        deductedAmount: new Decimal(0),
      };

      jest.spyOn(prisma.purchaseOrder, 'findFirst').mockResolvedValue(po as any);

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
      const po = { id: mockPoId, companyId: mockCompanyId };
      jest.spyOn(prisma.purchaseOrder, 'findFirst').mockResolvedValue(po as any);

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
        { id: 'pay-1', amount: new Decimal(500) },
        { id: 'pay-2', amount: new Decimal(300) },
      ];

      jest.spyOn(prisma.payment, 'findMany').mockResolvedValue(payments as any);

      const result = await service.getPaymentHistory(mockCompanyId, mockSupplierId);

      expect(result).toEqual(payments);
      expect(result.length).toBe(2);
      expect(prisma.payment.findMany).toHaveBeenCalledWith({
        where: { companyId: mockCompanyId, supplierId: mockSupplierId },
        orderBy: { recordedAt: 'desc' },
      });
    });
  });

  // ============ ANALYTICS TESTS ============

  describe('getSupplierMetrics', () => {
    it('should calculate supplier metrics', async () => {
      const supplier = { id: mockSupplierId, rating: new Decimal(4.5) };
      const pos = [
        {
          id: 'po-1',
          status: 'received',
          totalAmount: new Decimal(1000),
          createdAt: new Date(Date.now() - 14 * 86400000),
          deliveryDate: new Date(Date.now() - 7 * 86400000),
        },
      ];

      jest.spyOn(prisma.supplier, 'findFirst').mockResolvedValue(supplier as any);
      jest.spyOn(prisma.purchaseOrder, 'findMany').mockResolvedValue(pos as any);

      const result = await service.getSupplierMetrics(mockCompanyId, mockSupplierId);

      expect(result.totalPOs).toBe(1);
      expect(result.qualityScore).toBe(4.5);
      expect(result.onTimeDeliveryRate).toBe(100);
    });
  });

  describe('getTopSuppliers', () => {
    it('should return top suppliers by rating', async () => {
      const suppliers = [
        { id: 'sup-1', rating: new Decimal(5), isActive: true },
        { id: 'sup-2', rating: new Decimal(4), isActive: true },
        { id: 'sup-3', rating: new Decimal(3), isActive: true },
      ];

      jest.spyOn(prisma.supplier, 'findMany').mockResolvedValue(suppliers as any);

      const result = await service.getTopSuppliers(mockCompanyId, 'rating', 2);

      expect(result.length).toBe(2);
      expect((result[0].rating as any).toNumber()).toBe(5);
    });

    it('should return top suppliers by frequency', async () => {
      const suppliers = [
        { id: 'sup-1', isActive: true },
        { id: 'sup-2', isActive: true },
      ];

      jest.spyOn(prisma.supplier, 'findMany').mockResolvedValue(suppliers as any);
      jest.spyOn(prisma.purchaseOrder, 'findMany').mockResolvedValue([{ id: 'po-1' }] as any);

      const result = await service.getTopSuppliers(mockCompanyId, 'frequency', 10);

      expect(result.length).toBeGreaterThan(0);
    });
  });

  describe('calculateOutstandingBalance', () => {
    it('should calculate correct outstanding balance', () => {
      const po = {
        totalAmount: new Decimal(1000),
        paymentsMade: new Decimal(600),
        deductedAmount: new Decimal(100),
      };

      const balance = service.calculateOutstandingBalance(po as any);

      expect(balance.toNumber()).toBe(300); // 1000 - 600 - 100
    });

    it('should handle zero balance', () => {
      const po = {
        totalAmount: new Decimal(1000),
        paymentsMade: new Decimal(1000),
        deductedAmount: new Decimal(0),
      };

      const balance = service.calculateOutstandingBalance(po as any);

      expect(balance.toNumber()).toBe(0);
    });
  });
});
