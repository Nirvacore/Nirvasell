import {
  Controller,
  Post,
  Get,
  Put,
  Delete,
  Body,
  Param,
  Query,
  BadRequestException,
  HttpCode,
  HttpStatus,
} from '@nestjs/common';
import { SuppliersService } from '../services/suppliers.service';
import {
  CreateSupplierDto,
  UpdateSupplierDto,
  SupplierResponseDto,
  PaymentTermsEnum,
} from '../dtos/supplier.dto';
import {
  CreatePODto,
  UpdatePOStatusDto,
  POResponseDto,
  POStatusEnum,
} from '../dtos/purchase-order.dto';
import {
  CreateQuotationDto,
  AcceptQuotationDto,
  RejectQuotationDto,
  CompareQuotationsDto,
  QuotationResponseDto,
} from '../dtos/quotation.dto';
import { RecordPaymentDto, PaymentResponseDto } from '../dtos/payment.dto';
import { Decimal } from 'decimal.js';

/**
 * Suppliers Management Controller
 *
 * Handles all procurement operations including:
 * - Supplier management (CRUD)
 * - Purchase orders
 * - Quotations
 * - Payment tracking
 * - Supplier analytics
 *
 * Multi-tenant: companyId is extracted from request context
 */
@Controller('procurement/suppliers')
export class SuppliersController {
  constructor(private readonly suppliersService: SuppliersService) {}

  // ============ SUPPLIER ENDPOINTS (4) ============

  /**
   * Endpoint 1: Create a new supplier
   * POST /procurement/suppliers
   */
  @Post()
  async createSupplier(
    @Param('companyId') companyId: string,
    @Body() dto: CreateSupplierDto,
  ): Promise<SupplierResponseDto> {
    const supplier = await this.suppliersService.createSupplier(
      companyId,
      dto.name,
      dto.contact,
      dto.email,
      dto.phone,
      dto.paymentTerms,
      dto.rating,
    );
    return this.mapSupplierResponse(supplier);
  }

  /**
   * Endpoint 2: Get supplier details
   * GET /procurement/suppliers/:supplierId
   */
  @Get(':supplierId')
  async getSupplier(
    @Param('companyId') companyId: string,
    @Param('supplierId') supplierId: string,
  ): Promise<SupplierResponseDto> {
    const supplier = await this.suppliersService.getSupplier(companyId, supplierId);
    return this.mapSupplierResponse(supplier);
  }

  /**
   * Endpoint 3: List all suppliers with pagination
   * GET /procurement/suppliers?limit=10&offset=0
   */
  @Get()
  async listSuppliers(
    @Param('companyId') companyId: string,
    @Query('limit') limit: string = '10',
    @Query('offset') offset: string = '0',
  ): Promise<{ suppliers: SupplierResponseDto[]; total: number }> {
    const limitNum = Math.min(parseInt(limit) || 10, 100);
    const offsetNum = Math.max(parseInt(offset) || 0, 0);

    const result = await this.suppliersService.listSuppliers(companyId, limitNum, offsetNum);

    return {
      suppliers: result.suppliers.map(s => this.mapSupplierResponse(s)),
      total: result.total,
    };
  }

  /**
   * Endpoint 4: Update supplier details
   * PUT /procurement/suppliers/:supplierId
   */
  @Put(':supplierId')
  async updateSupplier(
    @Param('companyId') companyId: string,
    @Param('supplierId') supplierId: string,
    @Body() dto: UpdateSupplierDto,
  ): Promise<SupplierResponseDto> {
    const supplier = await this.suppliersService.updateSupplier(companyId, supplierId, dto);
    return this.mapSupplierResponse(supplier);
  }

  /**
   * Deactivate supplier
   * DELETE /procurement/suppliers/:supplierId
   */
  @Delete(':supplierId')
  @HttpCode(HttpStatus.NO_CONTENT)
  async deactivateSupplier(
    @Param('companyId') companyId: string,
    @Param('supplierId') supplierId: string,
  ): Promise<void> {
    await this.suppliersService.deactivateSupplier(companyId, supplierId);
  }

  // ============ PURCHASE ORDER ENDPOINTS (3) ============

  /**
   * Endpoint 5: Create a purchase order
   * POST /procurement/suppliers/:supplierId/purchase-orders
   */
  @Post(':supplierId/purchase-orders')
  async createPO(
    @Param('companyId') companyId: string,
    @Param('supplierId') supplierId: string,
    @Body() dto: CreatePODto,
  ): Promise<POResponseDto> {
    // Validate supplierId matches
    if (dto.supplierId !== supplierId) {
      throw new BadRequestException('Supplier ID mismatch');
    }

    const po = await this.suppliersService.createPO(
      companyId,
      supplierId,
      dto.items.map(item => ({
        ...item,
        unitPrice: new Decimal(item.unitPrice),
      })),
    );

    return this.mapPOResponse(po);
  }

  /**
   * Endpoint 6: Update PO status
   * PUT /procurement/suppliers/purchase-orders/:poId/status
   */
  @Put('purchase-orders/:poId/status')
  async updatePOStatus(
    @Param('companyId') companyId: string,
    @Param('poId') poId: string,
    @Body() dto: UpdatePOStatusDto,
  ): Promise<POResponseDto> {
    const po = await this.suppliersService.updatePOStatus(companyId, poId, dto.status);
    return this.mapPOResponse(po);
  }

  /**
   * Endpoint 7: Get POs by status
   * GET /procurement/suppliers/purchase-orders?status=confirmed
   */
  @Get('purchase-orders')
  async getPOsByStatus(
    @Param('companyId') companyId: string,
    @Query('status') status: string,
  ): Promise<POResponseDto[]> {
    if (!status) {
      throw new BadRequestException('Status parameter is required');
    }

    const pos = await this.suppliersService.getPOsByStatus(companyId, status);
    return pos.map(po => this.mapPOResponse(po));
  }

  /**
   * Get POs for a specific supplier
   * GET /procurement/suppliers/:supplierId/purchase-orders
   */
  @Get(':supplierId/purchase-orders')
  async getSupplierPOs(
    @Param('companyId') companyId: string,
    @Param('supplierId') supplierId: string,
  ): Promise<POResponseDto[]> {
    const pos = await this.suppliersService.getSupplierPOs(companyId, supplierId);
    return pos.map(po => this.mapPOResponse(po));
  }

  // ============ QUOTATION ENDPOINTS (3) ============

  /**
   * Endpoint 8: Request quotation from supplier
   * POST /procurement/suppliers/:supplierId/quotations
   */
  @Post(':supplierId/quotations')
  async requestQuotation(
    @Param('companyId') companyId: string,
    @Param('supplierId') supplierId: string,
    @Body() dto: CreateQuotationDto,
  ): Promise<QuotationResponseDto> {
    const quotation = await this.suppliersService.requestQuotation(
      companyId,
      supplierId,
      dto.items.map(item => ({
        ...item,
        unitPrice: new Decimal(item.unitPrice),
      })),
      dto.validUntilDays,
    );

    return this.mapQuotationResponse(quotation);
  }

  /**
   * Endpoint 9: Accept quotation (convert to PO)
   * POST /procurement/suppliers/quotations/:quotationId/accept
   */
  @Post('quotations/:quotationId/accept')
  async acceptQuotation(
    @Param('companyId') companyId: string,
    @Param('quotationId') quotationId: string,
  ): Promise<POResponseDto> {
    const po = await this.suppliersService.acceptQuotation(companyId, quotationId);
    return this.mapPOResponse(po);
  }

  /**
   * Endpoint 10: Reject quotation
   * POST /procurement/suppliers/quotations/:quotationId/reject
   */
  @Post('quotations/:quotationId/reject')
  async rejectQuotation(
    @Param('companyId') companyId: string,
    @Param('quotationId') quotationId: string,
  ): Promise<QuotationResponseDto> {
    const quotation = await this.suppliersService.rejectQuotation(companyId, quotationId);
    return this.mapQuotationResponse(quotation);
  }

  /**
   * Compare quotations (multiple)
   * POST /procurement/suppliers/quotations/compare
   */
  @Post('quotations/compare')
  async compareQuotations(
    @Param('companyId') companyId: string,
    @Body() dto: CompareQuotationsDto,
  ): Promise<QuotationResponseDto[]> {
    const quotations = await this.suppliersService.compareQuotations(
      companyId,
      dto.quotationIds,
    );

    return quotations.map(q => this.mapQuotationResponse(q));
  }

  // ============ PAYMENT ENDPOINTS (2) ============

  /**
   * Endpoint 11: Record payment for PO
   * POST /procurement/suppliers/purchase-orders/:poId/payments
   */
  @Post('purchase-orders/:poId/payments')
  async recordPayment(
    @Param('companyId') companyId: string,
    @Param('poId') poId: string,
    @Body() dto: RecordPaymentDto,
  ): Promise<PaymentResponseDto> {
    if (dto.poId !== poId) {
      throw new BadRequestException('PO ID mismatch');
    }

    const payment = await this.suppliersService.recordPayment(
      companyId,
      poId,
      new Decimal(dto.amount),
      dto.paymentType,
      dto.invoiceNumber,
    );

    return this.mapPaymentResponse(payment);
  }

  /**
   * Endpoint 12: Get payment history for supplier
   * GET /procurement/suppliers/:supplierId/payments
   */
  @Get(':supplierId/payments')
  async getPaymentHistory(
    @Param('companyId') companyId: string,
    @Param('supplierId') supplierId: string,
  ): Promise<PaymentResponseDto[]> {
    const payments = await this.suppliersService.getPaymentHistory(companyId, supplierId);
    return payments.map(p => this.mapPaymentResponse(p));
  }

  // ============ ANALYTICS ENDPOINT ============

  /**
   * Get supplier performance metrics
   * GET /procurement/suppliers/:supplierId/metrics
   */
  @Get(':supplierId/metrics')
  async getSupplierMetrics(
    @Param('companyId') companyId: string,
    @Param('supplierId') supplierId: string,
  ) {
    return this.suppliersService.getSupplierMetrics(companyId, supplierId);
  }

  /**
   * Get top suppliers
   * GET /procurement/suppliers/top?by=rating&limit=10
   */
  @Get()
  async getTopSuppliers(
    @Param('companyId') companyId: string,
    @Query('by') by: 'rating' | 'frequency' | 'savings' = 'rating',
    @Query('limit') limit: string = '10',
  ) {
    const limitNum = Math.min(parseInt(limit) || 10, 100);
    const suppliers = await this.suppliersService.getTopSuppliers(companyId, by, limitNum);
    return suppliers.map(s => this.mapSupplierResponse(s));
  }

  // ============ RESPONSE MAPPERS ============

  private mapSupplierResponse(supplier: any): SupplierResponseDto {
    return {
      id: supplier.id,
      name: supplier.name,
      contact: supplier.contact,
      email: supplier.email,
      phone: supplier.phone,
      paymentTerms: supplier.paymentTerms,
      rating: supplier.rating instanceof Decimal ? supplier.rating.toNumber() : supplier.rating,
      address: supplier.address,
      city: supplier.city,
      country: supplier.country,
      isActive: supplier.isActive,
      createdAt: supplier.createdAt,
      updatedAt: supplier.updatedAt,
    };
  }

  private mapPOResponse(po: any): POResponseDto {
    return {
      id: po.id,
      poNumber: po.poNumber,
      supplierId: po.supplierId,
      items: po.items,
      totalAmount: po.totalAmount instanceof Decimal ? po.totalAmount : new Decimal(po.totalAmount),
      status: po.status,
      deliveryDate: po.deliveryDate,
      shippingAddress: po.shippingAddress,
      paymentsMade: po.paymentsMade,
      deductedAmount: po.deductedAmount,
      createdAt: po.createdAt,
      updatedAt: po.updatedAt,
    };
  }

  private mapQuotationResponse(quotation: any): QuotationResponseDto {
    return {
      id: quotation.id,
      quotationNumber: quotation.quotationNumber,
      supplierId: quotation.supplierId,
      items: quotation.items,
      totalAmount:
        quotation.totalAmount instanceof Decimal
          ? quotation.totalAmount
          : new Decimal(quotation.totalAmount),
      validUntil: quotation.validUntil,
      status: quotation.status,
      acceptedAt: quotation.acceptedAt,
      rejectedAt: quotation.rejectedAt,
      poId: quotation.poId,
      revisionNumber: quotation.revisionNumber,
      createdAt: quotation.createdAt,
      updatedAt: quotation.updatedAt,
    };
  }

  private mapPaymentResponse(payment: any): PaymentResponseDto {
    return {
      id: payment.id,
      poId: payment.poId,
      supplierId: payment.supplierId,
      invoiceNumber: payment.invoiceNumber,
      amount: payment.amount instanceof Decimal ? payment.amount : new Decimal(payment.amount),
      paymentType: payment.paymentType,
      paymentMethod: payment.paymentMethod,
      referenceNumber: payment.referenceNumber,
      status: payment.status,
      dueDate: payment.dueDate,
      paidDate: payment.paidDate,
      recordedAt: payment.recordedAt,
      updatedAt: payment.updatedAt,
    };
  }
}
