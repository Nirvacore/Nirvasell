# Procurement Module (Supplier Management Service)

Comprehensive supplier management and procurement operations for nirvacore-v1. This module handles supplier lifecycle management, purchase orders, quotation management, and payment tracking with full multi-tenant isolation.

## Features

### 1. Supplier Management (CRUD)
- Create, retrieve, update, and deactivate suppliers
- Store supplier profiles: name, contact, email, phone, payment terms, rating
- Support for payment terms: COD, Net30, Net60, Net90
- Rating system (1-5 stars)
- Supplier contact and address information
- Tax ID storage

### 2. Purchase Order Management
- Create POs from supplier catalog
- Auto-generate PO numbers with timestamps
- Track PO items with descriptions, quantities, unit prices
- Multiple PO statuses: draft, submitted, confirmed, shipped, received, cancelled
- Track payment progress and deductions
- Shipping address and delivery date tracking

### 3. Quotation Management
- Request quotations from suppliers
- Auto-generated quotation numbers
- Set quotation validity periods
- Quotation statuses: pending, accepted, rejected, expired
- Convert accepted quotations to purchase orders
- Quotation comparison for cost analysis
- Revision tracking

### 4. Payment Tracking
- Record payments against purchase orders
- Multiple payment types: deposit, partial, full, settlement
- Payment methods: bank transfer, check, cash, credit
- Invoice tracking with supplier reference numbers
- Outstanding balance calculation
- Payment history per supplier

### 5. Supplier Performance Analytics
- Total PO count per supplier
- Total spending metrics
- Average delivery time calculation
- On-time delivery rate percentage
- Quality scores based on supplier ratings
- Top suppliers ranking by rating, frequency, or spending

## Architecture

### Entities

#### Supplier
```typescript
- id: UUID
- companyId: string (multi-tenant isolation)
- name: string
- contact: string (person name)
- email: string (unique per company)
- phone: string
- paymentTerms: 'cod' | 'net30' | 'net60' | 'net90'
- rating: Decimal (1-5)
- address?: string
- city?: string
- country?: string
- taxId?: string
- isActive: boolean
- createdAt/updatedAt: Date
```

#### PurchaseOrder
```typescript
- id: UUID
- companyId: string
- supplierId: string (FK)
- poNumber: string (auto-generated)
- items: Array of {productId?, description, quantity, unitPrice, totalPrice}
- totalAmount: Decimal
- status: 'draft' | 'submitted' | 'confirmed' | 'shipped' | 'received' | 'cancelled'
- deliveryDate?: Date
- shippingAddress?: string
- notes?: string
- paymentsMade: number (tracking total paid)
- deductedAmount: number (tax, fees)
- createdAt/updatedAt: Date
```

#### Quotation
```typescript
- id: UUID
- companyId: string
- supplierId: string
- quotationNumber: string (auto-generated)
- items: Array of {description, quantity, unitPrice, totalPrice}
- totalAmount: Decimal
- validUntil: Date
- status: 'pending' | 'accepted' | 'rejected' | 'expired'
- acceptedAt?: Date
- rejectedAt?: Date
- poId?: string (reference to converted PO)
- notes?: string
- revisionNumber: number
- createdAt/updatedAt: Date
```

#### Payment
```typescript
- id: UUID
- companyId: string
- poId: string
- supplierId: string
- invoiceNumber: string
- amount: Decimal
- paymentType: 'deposit' | 'partial' | 'full' | 'settlement'
- paymentMethod?: 'bank_transfer' | 'check' | 'cash' | 'credit'
- referenceNumber?: string
- status: 'pending' | 'processed' | 'failed'
- dueDate?: Date
- paidDate?: Date
- notes?: string
- recordedAt/updatedAt: Date
```

## API Endpoints

### Supplier Management (4 endpoints)
1. **POST** `/procurement/suppliers` - Create supplier
2. **GET** `/procurement/suppliers/:supplierId` - Get supplier details
3. **GET** `/procurement/suppliers?limit=10&offset=0` - List suppliers with pagination
4. **PUT** `/procurement/suppliers/:supplierId` - Update supplier details

### Purchase Orders (3 endpoints)
5. **POST** `/procurement/suppliers/:supplierId/purchase-orders` - Create PO
6. **PUT** `/procurement/suppliers/purchase-orders/:poId/status` - Update PO status
7. **GET** `/procurement/suppliers/purchase-orders?status=confirmed` - Get POs by status

### Quotations (3 endpoints)
8. **POST** `/procurement/suppliers/:supplierId/quotations` - Request quotation
9. **POST** `/procurement/suppliers/quotations/:quotationId/accept` - Accept quotation
10. **POST** `/procurement/suppliers/quotations/:quotationId/reject` - Reject quotation

### Payments (2 endpoints)
11. **POST** `/procurement/suppliers/purchase-orders/:poId/payments` - Record payment
12. **GET** `/procurement/suppliers/:supplierId/payments` - Get payment history

### Analytics
- **GET** `/procurement/suppliers/:supplierId/metrics` - Supplier performance metrics
- **GET** `/procurement/suppliers/top?by=rating&limit=10` - Top suppliers ranking

## Service Methods

### Supplier CRUD
```typescript
createSupplier(companyId, name, contact, email, phone, paymentTerms, rating?): Promise<Supplier>
getSupplier(companyId, supplierId): Promise<Supplier>
listSuppliers(companyId, limit?, offset?): Promise<{suppliers, total}>
updateSupplier(companyId, supplierId, updates): Promise<Supplier>
deactivateSupplier(companyId, supplierId): Promise<Supplier>
```

### Purchase Orders
```typescript
createPO(companyId, supplierId, items[]): Promise<PurchaseOrder>
updatePOStatus(companyId, poId, status): Promise<PurchaseOrder>
getPOsByStatus(companyId, status): Promise<PurchaseOrder[]>
getSupplierPOs(companyId, supplierId): Promise<PurchaseOrder[]>
```

### Quotations
```typescript
requestQuotation(companyId, supplierId, items[], validUntilDays?): Promise<Quotation>
acceptQuotation(companyId, quotationId): Promise<PurchaseOrder>
rejectQuotation(companyId, quotationId): Promise<Quotation>
compareQuotations(companyId, quotationIds[]): Promise<Quotation[]>
```

### Payments
```typescript
recordPayment(companyId, poId, amount, paymentType, invoiceNumber): Promise<Payment>
getPaymentHistory(companyId, supplierId): Promise<Payment[]>
calculateOutstandingBalance(po): Decimal
```

### Analytics
```typescript
getSupplierMetrics(companyId, supplierId): Promise<SupplierMetrics>
getTopSuppliers(companyId, by?: 'rating'|'frequency'|'savings', limit?): Promise<Supplier[]>
```

## Multi-Tenancy

All operations are filtered by `companyId` for complete data isolation:
- Suppliers are unique per company
- POs, quotations, and payments are company-specific
- Unique constraint on email per company
- All queries include `companyId` filter

## Key Validations

### Supplier Creation
- Payment terms must be valid (cod, net30, net60, net90)
- Rating must be between 1-5
- Email must be unique per company
- No duplicate email addresses

### Purchase Orders
- Must contain at least one item
- Items must have positive quantities
- Total amount is calculated from item prices

### Quotations
- Must contain at least one item
- Can only be accepted if status is 'pending'
- Cannot accept expired quotations
- Can only be rejected if status is 'pending'
- Minimum 2 quotations required for comparison

### Payments
- Payment amount cannot exceed outstanding balance
- Payment type must be valid (deposit, partial, full, settlement)
- Invoice number is required
- Outstanding balance = totalAmount - paymentsMade - deductedAmount

## Error Handling

The service throws specific exceptions:
- **BadRequestException**: Invalid input, violated business rules
- **NotFoundException**: Resource not found in company context
- **ConflictException**: Unique constraint violations (duplicate email)

## Testing

Comprehensive test suite with 50+ tests covering:
- CRUD operations (15 tests)
- Purchase orders (10 tests)
- Quotations (8 tests)
- Payments (8 tests)
- Analytics (5+ tests)
- Error cases and validations

Run tests:
```bash
npm test -- suppliers.service.spec.ts
```

## Module Registration

Add to main app module:
```typescript
import { ProcurementModule } from './procurement/procurement.module';

@Module({
  imports: [
    // ... other modules
    ProcurementModule,
  ],
})
export class AppModule {}
```

## Usage Example

```typescript
// Create supplier
const supplier = await suppliersService.createSupplier(
  'company-123',
  'Acme Supplies',
  'John Smith',
  'john@acme.com',
  '+1234567890',
  'net30',
  4.5
);

// Create PO
const po = await suppliersService.createPO(
  'company-123',
  supplier.id,
  [
    { description: 'Widget A', quantity: 100, unitPrice: new Decimal(10) },
    { description: 'Widget B', quantity: 50, unitPrice: new Decimal(20) }
  ]
);

// Request quotation
const quotation = await suppliersService.requestQuotation(
  'company-123',
  supplier.id,
  [
    { description: 'Service Package', quantity: 1, unitPrice: new Decimal(5000) }
  ],
  30 // valid for 30 days
);

// Record payment
const payment = await suppliersService.recordPayment(
  'company-123',
  po.id,
  new Decimal(2000),
  'partial',
  'INV-2024-001'
);

// Get metrics
const metrics = await suppliersService.getSupplierMetrics('company-123', supplier.id);
console.log(`Total spent: $${metrics.totalSpent}`);
console.log(`On-time delivery rate: ${metrics.onTimeDeliveryRate}%`);
```

## Files Structure

```
src/procurement/
├── entities/
│   ├── supplier.entity.ts
│   ├── purchase-order.entity.ts
│   ├── quotation.entity.ts
│   └── payment.entity.ts
├── services/
│   ├── suppliers.service.ts
│   └── suppliers.service.spec.ts (50+ tests)
├── controllers/
│   └── suppliers.controller.ts (12 endpoints)
├── dtos/
│   ├── supplier.dto.ts
│   ├── purchase-order.dto.ts
│   ├── quotation.dto.ts
│   └── payment.dto.ts
├── procurement.module.ts
├── index.ts
└── README.md
```

## Performance Considerations

- Indexes on `companyId`, `status`, `supplierId` for fast queries
- Pagination support for large supplier lists (default limit: 10, max: 100)
- Decimal.js for accurate financial calculations
- Query optimization with proper sorting and filtering

## Future Enhancements

- Supplier tier system (gold, silver, bronze)
- Automated invoice reconciliation
- Supplier notifications
- Purchase order forecasting
- Bulk operations for multiple suppliers
- Supplier performance scoring algorithm
- Integration with accounting systems
