import { Injectable, BadRequestException, NotFoundException, ConflictException, Logger } from '@nestjs/common';
import { PrismaService } from '@nestjs/prisma';
import { Decimal } from 'decimal.js';
import { Supplier, PurchaseOrder, Quotation, Payment } from '@prisma/client';

export interface POItem {
  productId?: string;
  description: string;
  quantity: number;
  unitPrice: Decimal | string;
}

export interface QuotationItem {
  description: string;
  quantity: number;
  unitPrice: Decimal | string;
}

export interface SupplierMetrics {
  totalPOs: number;
  totalSpent: Decimal;
  averageDeliveryDays: number;
  onTimeDeliveryRate: number;
  qualityScore: number;
  lastOrderDate?: Date;
}

@Injectable()
export class SuppliersService {
  private readonly logger = new Logger(SuppliersService.name);
  private poCounter: Map<string, number> = new Map(); // companyId -> counter

  constructor(private prisma: PrismaService) {}

  // ============ Supplier CRUD ============

  async createSupplier(
    companyId: string,
    name: string,
    contact: string,
    email: string,
    phone: string,
    paymentTerms: string,
    rating: number = 3.0,
  ): Promise<Supplier> {
    // Validate payment terms
    const validTerms = ['cod', 'net30', 'net60', 'net90'];
    if (!validTerms.includes(paymentTerms)) {
      throw new BadRequestException(`Invalid payment terms: ${paymentTerms}`);
    }

    // Check for duplicate email
    const existing = await this.prisma.supplier.findUnique({
      where: {
        companyId_email: { companyId, email },
      },
    }).catch(() => null); // Handle case where unique constraint might not exist yet

    if (existing) {
      throw new ConflictException(`Supplier with email ${email} already exists`);
    }

    // Validate rating
    if (rating < 1 || rating > 5) {
      throw new BadRequestException('Rating must be between 1 and 5');
    }

    return this.prisma.supplier.create({
      data: {
        companyId,
        name,
        contact,
        email,
        phone,
        paymentTerms,
        rating: new Decimal(rating),
      },
    });
  }

  async getSupplier(companyId: string, supplierId: string): Promise<Supplier> {
    const supplier = await this.prisma.supplier.findFirst({
      where: { id: supplierId, companyId },
    });

    if (!supplier) {
      throw new NotFoundException('Supplier not found');
    }

    return supplier;
  }

  async listSuppliers(
    companyId: string,
    limit: number = 10,
    offset: number = 0,
  ): Promise<{ suppliers: Supplier[]; total: number }> {
    const [suppliers, total] = await Promise.all([
      this.prisma.supplier.findMany({
        where: { companyId, isActive: true },
        skip: offset,
        take: limit,
        orderBy: { createdAt: 'desc' },
      }),
      this.prisma.supplier.count({
        where: { companyId, isActive: true },
      }),
    ]);

    return { suppliers, total };
  }

  async updateSupplier(
    companyId: string,
    supplierId: string,
    updates: Partial<Supplier>,
  ): Promise<Supplier> {
    const supplier = await this.getSupplier(companyId, supplierId);

    // Validate updates
    if (updates.rating && (updates.rating < 1 || updates.rating > 5)) {
      throw new BadRequestException('Rating must be between 1 and 5');
    }

    if (updates.paymentTerms) {
      const validTerms = ['cod', 'net30', 'net60', 'net90'];
      if (!validTerms.includes(updates.paymentTerms)) {
        throw new BadRequestException(`Invalid payment terms: ${updates.paymentTerms}`);
      }
    }

    return this.prisma.supplier.update({
      where: { id: supplierId },
      data: updates,
    });
  }

  async deactivateSupplier(companyId: string, supplierId: string): Promise<Supplier> {
    await this.getSupplier(companyId, supplierId);

    return this.prisma.supplier.update({
      where: { id: supplierId },
      data: { isActive: false },
    });
  }

  // ============ Purchase Orders ============

  async createPO(
    companyId: string,
    supplierId: string,
    items: POItem[],
  ): Promise<PurchaseOrder> {
    // Verify supplier exists
    await this.getSupplier(companyId, supplierId);

    // Validate items
    if (!items || items.length === 0) {
      throw new BadRequestException('PO must contain at least one item');
    }

    // Calculate total amount
    let totalAmount = new Decimal(0);
    const processedItems = items.map(item => {
      const unitPrice = new Decimal(item.unitPrice);
      const totalPrice = unitPrice.times(item.quantity);
      totalAmount = totalAmount.plus(totalPrice);
      return {
        ...item,
        unitPrice: unitPrice.toJSON(),
        totalPrice: totalPrice.toJSON(),
      };
    });

    // Generate PO number
    const counter = (this.poCounter.get(companyId) || 0) + 1;
    this.poCounter.set(companyId, counter);
    const poNumber = `PO-${companyId.substring(0, 4).toUpperCase()}-${Date.now()}-${counter}`;

    return this.prisma.purchaseOrder.create({
      data: {
        companyId,
        supplierId,
        poNumber,
        items: processedItems,
        totalAmount,
        status: 'draft',
        paymentsMade: new Decimal(0),
        deductedAmount: new Decimal(0),
      },
    });
  }

  async updatePOStatus(
    companyId: string,
    poId: string,
    status: string,
  ): Promise<PurchaseOrder> {
    const validStatuses = ['draft', 'submitted', 'confirmed', 'shipped', 'received', 'cancelled'];
    if (!validStatuses.includes(status)) {
      throw new BadRequestException(`Invalid status: ${status}`);
    }

    const po = await this.prisma.purchaseOrder.findFirst({
      where: { id: poId, companyId },
    });

    if (!po) {
      throw new NotFoundException('Purchase order not found');
    }

    return this.prisma.purchaseOrder.update({
      where: { id: poId },
      data: { status },
    });
  }

  async getPOsByStatus(companyId: string, status: string): Promise<PurchaseOrder[]> {
    return this.prisma.purchaseOrder.findMany({
      where: { companyId, status },
      orderBy: { createdAt: 'desc' },
    });
  }

  async getSupplierPOs(companyId: string, supplierId: string): Promise<PurchaseOrder[]> {
    return this.prisma.purchaseOrder.findMany({
      where: { companyId, supplierId },
      orderBy: { createdAt: 'desc' },
    });
  }

  // ============ Quotations ============

  async requestQuotation(
    companyId: string,
    supplierId: string,
    items: QuotationItem[],
    validUntilDays: number = 30,
  ): Promise<Quotation> {
    // Verify supplier exists
    await this.getSupplier(companyId, supplierId);

    // Validate items
    if (!items || items.length === 0) {
      throw new BadRequestException('Quotation must contain at least one item');
    }

    // Calculate total amount
    let totalAmount = new Decimal(0);
    const processedItems = items.map(item => {
      const unitPrice = new Decimal(item.unitPrice);
      const totalPrice = unitPrice.times(item.quantity);
      totalAmount = totalAmount.plus(totalPrice);
      return {
        ...item,
        unitPrice: unitPrice.toJSON(),
        totalPrice: totalPrice.toJSON(),
      };
    });

    // Generate quotation number
    const quotationNumber = `QT-${companyId.substring(0, 4).toUpperCase()}-${Date.now()}`;
    const validUntil = new Date();
    validUntil.setDate(validUntil.getDate() + validUntilDays);

    return this.prisma.quotation.create({
      data: {
        companyId,
        supplierId,
        quotationNumber,
        items: processedItems,
        totalAmount,
        status: 'pending',
        validUntil,
      },
    });
  }

  async acceptQuotation(companyId: string, quotationId: string): Promise<PurchaseOrder> {
    const quotation = await this.prisma.quotation.findFirst({
      where: { id: quotationId, companyId },
    });

    if (!quotation) {
      throw new NotFoundException('Quotation not found');
    }

    if (quotation.status !== 'pending') {
      throw new BadRequestException('Only pending quotations can be accepted');
    }

    if (new Date() > quotation.validUntil) {
      throw new BadRequestException('Quotation has expired');
    }

    // Use transaction for multi-step operation
    return this.prisma.$transaction(async tx => {
      // Create PO from quotation
      const po = await this.createPOFromQuotation(
        companyId,
        quotation.supplierId,
        quotation.items as any[],
        tx,
      );

      // Update quotation
      await tx.quotation.update({
        where: { id: quotationId },
        data: {
          status: 'accepted',
          acceptedAt: new Date(),
          poId: po.id,
        },
      });

      return po;
    });
  }

  private async createPOFromQuotation(
    companyId: string,
    supplierId: string,
    items: Array<{ description: string; quantity: number; unitPrice: any }>,
    tx: any,
  ): Promise<PurchaseOrder> {
    // Verify supplier exists
    const supplier = await tx.supplier.findFirst({
      where: { id: supplierId, companyId },
    });

    if (!supplier) {
      throw new NotFoundException('Supplier not found');
    }

    // Calculate total amount
    let totalAmount = new Decimal(0);
    const processedItems = items.map(item => {
      const unitPrice = new Decimal(item.unitPrice);
      const totalPrice = unitPrice.times(item.quantity);
      totalAmount = totalAmount.plus(totalPrice);
      return {
        ...item,
        unitPrice: unitPrice.toJSON(),
        totalPrice: totalPrice.toJSON(),
      };
    });

    // Generate PO number
    const counter = (this.poCounter.get(companyId) || 0) + 1;
    this.poCounter.set(companyId, counter);
    const poNumber = `PO-${companyId.substring(0, 4).toUpperCase()}-${Date.now()}-${counter}`;

    return tx.purchaseOrder.create({
      data: {
        companyId,
        supplierId,
        poNumber,
        items: processedItems,
        totalAmount,
        status: 'draft',
        paymentsMade: new Decimal(0),
        deductedAmount: new Decimal(0),
      },
    });
  }

  async rejectQuotation(companyId: string, quotationId: string): Promise<Quotation> {
    const quotation = await this.prisma.quotation.findFirst({
      where: { id: quotationId, companyId },
    });

    if (!quotation) {
      throw new NotFoundException('Quotation not found');
    }

    if (quotation.status !== 'pending') {
      throw new BadRequestException('Only pending quotations can be rejected');
    }

    return this.prisma.quotation.update({
      where: { id: quotationId },
      data: {
        status: 'rejected',
        rejectedAt: new Date(),
      },
    });
  }

  async compareQuotations(companyId: string, quotationIds: string[]): Promise<Quotation[]> {
    if (quotationIds.length < 2) {
      throw new BadRequestException('At least 2 quotations are required for comparison');
    }

    const quotations = await this.prisma.quotation.findMany({
      where: {
        id: { in: quotationIds },
        companyId,
      },
    });

    return quotations.sort((a, b) => {
      return (a.totalAmount as any).toNumber() - (b.totalAmount as any).toNumber();
    });
  }

  // ============ Payments ============

  async recordPayment(
    companyId: string,
    poId: string,
    amount: Decimal | string,
    paymentType: string,
    invoiceNumber: string,
  ): Promise<Payment> {
    const po = await this.prisma.purchaseOrder.findFirst({
      where: { id: poId, companyId },
    });

    if (!po) {
      throw new NotFoundException('Purchase order not found');
    }

    const paymentAmount = new Decimal(amount);
    const outstanding = this.calculateOutstandingBalance(po);

    if (paymentAmount.greaterThan(outstanding)) {
      throw new BadRequestException('Payment amount exceeds outstanding balance');
    }

    const validTypes = ['deposit', 'partial', 'full', 'settlement'];
    if (!validTypes.includes(paymentType)) {
      throw new BadRequestException(`Invalid payment type: ${paymentType}`);
    }

    // Use transaction for multi-step operation
    return this.prisma.$transaction(async tx => {
      // Record payment
      const payment = await tx.payment.create({
        data: {
          companyId,
          poId,
          supplierId: po.supplierId,
          invoiceNumber,
          amount: paymentAmount,
          paymentType,
          status: 'processed',
        },
      });

      // Update PO
      const newPaymentsMade = new Decimal(po.paymentsMade).plus(paymentAmount);
      await tx.purchaseOrder.update({
        where: { id: poId },
        data: { paymentsMade: newPaymentsMade },
      });

      return payment;
    });
  }

  async getPaymentHistory(companyId: string, supplierId: string): Promise<Payment[]> {
    return this.prisma.payment.findMany({
      where: { companyId, supplierId },
      orderBy: { recordedAt: 'desc' },
    });
  }

  calculateOutstandingBalance(po: PurchaseOrder): Decimal {
    const paid = new Decimal(po.paymentsMade);
    const deducted = new Decimal(po.deductedAmount);
    const total = po.totalAmount instanceof Decimal ? po.totalAmount : new Decimal(po.totalAmount);
    return total.minus(paid).minus(deducted);
  }

  // ============ Analytics ============

  async getSupplierMetrics(companyId: string, supplierId: string): Promise<SupplierMetrics> {
    const pos = await this.getSupplierPOs(companyId, supplierId);

    let totalSpent = new Decimal(0);
    let totalDeliveryDays = 0;
    let deliveredCount = 0;
    let onTimeCount = 0;

    pos.forEach(po => {
      totalSpent = totalSpent.plus(po.totalAmount);

      if (po.status === 'received') {
        deliveredCount++;
        if (po.deliveryDate) {
          const daysToDeliver = Math.floor((po.deliveryDate.getTime() - po.createdAt.getTime()) / (1000 * 60 * 60 * 24));
          totalDeliveryDays += daysToDeliver;
          if (daysToDeliver <= 14) {
            onTimeCount++;
          }
        }
      }
    });

    const supplier = await this.getSupplier(companyId, supplierId);
    const lastOrderDate = pos.length > 0 ? pos[0].createdAt : undefined;

    return {
      totalPOs: pos.length,
      totalSpent,
      averageDeliveryDays: deliveredCount > 0 ? Math.floor(totalDeliveryDays / deliveredCount) : 0,
      onTimeDeliveryRate: deliveredCount > 0 ? Math.round((onTimeCount / deliveredCount) * 100) : 0,
      qualityScore: supplier.rating instanceof Decimal ? supplier.rating.toNumber() : (supplier.rating as any).toNumber(),
      lastOrderDate,
    };
  }

  async getTopSuppliers(
    companyId: string,
    by: 'rating' | 'frequency' | 'savings' = 'rating',
    limit: number = 10,
  ): Promise<Supplier[]> {
    const suppliers = await this.prisma.supplier.findMany({
      where: { companyId, isActive: true },
    });

    // Get metrics for sorting
    if (by === 'rating') {
      return suppliers.sort((a, b) => {
        const aRating = a.rating instanceof Decimal ? a.rating.toNumber() : (a.rating as any).toNumber();
        const bRating = b.rating instanceof Decimal ? b.rating.toNumber() : (b.rating as any).toNumber();
        return bRating - aRating;
      }).slice(0, limit);
    }

    if (by === 'frequency') {
      const supplierPOCounts = await Promise.all(
        suppliers.map(async s => ({
          supplier: s,
          poCount: (await this.getSupplierPOs(companyId, s.id)).length,
        })),
      );
      return supplierPOCounts.sort((a, b) => b.poCount - a.poCount).map(s => s.supplier).slice(0, limit);
    }

    // By savings - based on lower prices
    const supplierMetrics = await Promise.all(
      suppliers.map(async s => ({
        supplier: s,
        metrics: await this.getSupplierMetrics(companyId, s.id),
      })),
    );

    return supplierMetrics.sort((a, b) => a.metrics.totalSpent.toNumber() - b.metrics.totalSpent.toNumber()).map(s => s.supplier).slice(0, limit);
  }
}
