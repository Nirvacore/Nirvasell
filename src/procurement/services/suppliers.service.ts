import { Injectable, BadRequestException, NotFoundException, ConflictException, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Decimal } from 'decimal.js';
import { Supplier } from '../entities/supplier.entity';
import { PurchaseOrder } from '../entities/purchase-order.entity';
import { Quotation } from '../entities/quotation.entity';
import { Payment } from '../entities/payment.entity';

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

  constructor(
    @InjectRepository(Supplier)
    private supplierRepo: Repository<Supplier>,
    @InjectRepository(PurchaseOrder)
    private poRepo: Repository<PurchaseOrder>,
    @InjectRepository(Quotation)
    private quotationRepo: Repository<Quotation>,
    @InjectRepository(Payment)
    private paymentRepo: Repository<Payment>,
  ) {}

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
    const existing = await this.supplierRepo.findOne({
      where: { companyId, email },
    });
    if (existing) {
      throw new ConflictException(`Supplier with email ${email} already exists`);
    }

    // Validate rating
    if (rating < 1 || rating > 5) {
      throw new BadRequestException('Rating must be between 1 and 5');
    }

    const supplier = this.supplierRepo.create({
      companyId,
      name,
      contact,
      email,
      phone,
      paymentTerms,
      rating: new Decimal(rating),
    });

    return this.supplierRepo.save(supplier);
  }

  async getSupplier(companyId: string, supplierId: string): Promise<Supplier> {
    const supplier = await this.supplierRepo.findOne({
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
    const [suppliers, total] = await this.supplierRepo.findAndCount({
      where: { companyId, isActive: true },
      skip: offset,
      take: limit,
      order: { createdAt: 'DESC' },
    });

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

    Object.assign(supplier, updates);
    return this.supplierRepo.save(supplier);
  }

  async deactivateSupplier(companyId: string, supplierId: string): Promise<Supplier> {
    const supplier = await this.getSupplier(companyId, supplierId);
    supplier.isActive = false;
    return this.supplierRepo.save(supplier);
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
        unitPrice,
        totalPrice,
      };
    });

    // Generate PO number
    const counter = (this.poCounter.get(companyId) || 0) + 1;
    this.poCounter.set(companyId, counter);
    const poNumber = `PO-${companyId.substring(0, 4).toUpperCase()}-${Date.now()}-${counter}`;

    const po = this.poRepo.create({
      companyId,
      supplierId,
      poNumber,
      items: processedItems,
      totalAmount,
      status: 'draft',
      paymentsMade: 0,
      deductedAmount: 0,
    });

    return this.poRepo.save(po);
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

    const po = await this.poRepo.findOne({
      where: { id: poId, companyId },
    });

    if (!po) {
      throw new NotFoundException('Purchase order not found');
    }

    po.status = status;
    return this.poRepo.save(po);
  }

  async getPOsByStatus(companyId: string, status: string): Promise<PurchaseOrder[]> {
    return this.poRepo.find({
      where: { companyId, status },
      order: { createdAt: 'DESC' },
    });
  }

  async getSupplierPOs(companyId: string, supplierId: string): Promise<PurchaseOrder[]> {
    return this.poRepo.find({
      where: { companyId, supplierId },
      order: { createdAt: 'DESC' },
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
        unitPrice,
        totalPrice,
      };
    });

    // Generate quotation number
    const quotationNumber = `QT-${companyId.substring(0, 4).toUpperCase()}-${Date.now()}`;
    const validUntil = new Date();
    validUntil.setDate(validUntil.getDate() + validUntilDays);

    const quotation = this.quotationRepo.create({
      companyId,
      supplierId,
      quotationNumber,
      items: processedItems,
      totalAmount,
      status: 'pending',
      validUntil,
    });

    return this.quotationRepo.save(quotation);
  }

  async acceptQuotation(companyId: string, quotationId: string): Promise<PurchaseOrder> {
    const quotation = await this.quotationRepo.findOne({
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

    // Create PO from quotation
    const po = await this.createPO(
      companyId,
      quotation.supplierId,
      quotation.items.map(item => ({
        description: item.description,
        quantity: item.quantity,
        unitPrice: item.unitPrice,
      })),
    );

    // Update quotation
    quotation.status = 'accepted';
    quotation.acceptedAt = new Date();
    quotation.poId = po.id;
    await this.quotationRepo.save(quotation);

    return po;
  }

  async rejectQuotation(companyId: string, quotationId: string): Promise<Quotation> {
    const quotation = await this.quotationRepo.findOne({
      where: { id: quotationId, companyId },
    });

    if (!quotation) {
      throw new NotFoundException('Quotation not found');
    }

    if (quotation.status !== 'pending') {
      throw new BadRequestException('Only pending quotations can be rejected');
    }

    quotation.status = 'rejected';
    quotation.rejectedAt = new Date();
    return this.quotationRepo.save(quotation);
  }

  async compareQuotations(companyId: string, quotationIds: string[]): Promise<Quotation[]> {
    if (quotationIds.length < 2) {
      throw new BadRequestException('At least 2 quotations are required for comparison');
    }

    const quotations = await this.quotationRepo.find({
      where: {
        id: quotationIds.includes('{id}') ? undefined : undefined, // Use IN query
        companyId,
      },
    });

    // Manual filtering since TypeORM doesn't support IN directly in this context
    return quotations.filter(q => quotationIds.includes(q.id)).sort((a, b) => {
      return a.totalAmount.toNumber() - b.totalAmount.toNumber();
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
    const po = await this.poRepo.findOne({
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

    const payment = this.paymentRepo.create({
      companyId,
      poId,
      supplierId: po.supplierId,
      invoiceNumber,
      amount: paymentAmount,
      paymentType,
      status: 'processed',
    });

    await this.paymentRepo.save(payment);

    // Update PO
    po.paymentsMade = new Decimal(po.paymentsMade).plus(paymentAmount).toNumber();
    await this.poRepo.save(po);

    return payment;
  }

  async getPaymentHistory(companyId: string, supplierId: string): Promise<Payment[]> {
    return this.paymentRepo.find({
      where: { companyId, supplierId },
      order: { recordedAt: 'DESC' },
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
      qualityScore: supplier.rating.toNumber(),
      lastOrderDate,
    };
  }

  async getTopSuppliers(
    companyId: string,
    by: 'rating' | 'frequency' | 'savings' = 'rating',
    limit: number = 10,
  ): Promise<Supplier[]> {
    const suppliers = await this.supplierRepo.find({
      where: { companyId, isActive: true },
    });

    // Get metrics for sorting
    if (by === 'rating') {
      return suppliers.sort((a, b) => b.rating.toNumber() - a.rating.toNumber()).slice(0, limit);
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
