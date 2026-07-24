# Commerce Module - nirvacore-v1

Complete multi-channel selling service for syncing products and orders across Shopee, Lazada, and TikTok Shop (Thailand).

## Project Structure

```
src/commerce/
├── services/
│   ├── multi-channel-selling.service.ts       # Main service (395 lines)
│   └── multi-channel-selling.service.spec.ts  # Test suite (700+ lines, 60+ tests)
├── entities/
│   ├── channel-config.entity.ts               # Marketplace configuration
│   ├── channel-product.entity.ts              # Product listings per channel
│   ├── order.entity.ts                        # Orders from marketplaces
│   └── product.entity.ts                      # Internal product catalog
├── controllers/
│   └── multi-channel-selling.controller.ts    # REST API endpoints
├── dtos/
│   ├── channel.dto.ts                         # Channel management DTOs
│   ├── product.dto.ts                         # Product sync DTOs
│   └── order.dto.ts                           # Order DTOs
├── commerce.module.ts                         # NestJS module definition
├── index.ts                                   # Barrel export
├── MULTI_CHANNEL_SELLING.md                   # Detailed service documentation
└── README.md                                  # This file
```

## Features

### Channel Management
- Add/update/deactivate marketplace channels
- Store encrypted API credentials per channel
- Configure auto-sync settings and intervals
- Support for Shopee, Lazada, TikTok Shop

### Product Synchronization
- Sync products to multiple channels simultaneously
- Different price per channel
- Different inventory per channel
- Track external product IDs for each channel
- Update price and stock on demand

### Inventory Management
- Proportional distribution across channels
- Distribute 300 units across 3 channels = 100 per channel
- Automatic remainder handling
- Bulk sync to all active channels

### Order Management
- Import orders from marketplace channels
- Upsert semantics (update if external ID exists)
- Status tracking: pending → confirmed → shipped → delivered/cancelled
- Validate products exist on channel before import
- Sync order status back to marketplace

### Pricing Strategy
- Cost multiplier per channel (1.2x to 2.0x)
- Fixed markup per channel (+50 THB)
- Discount percentage per channel (-10%)
- Min/max price bounds
- Combine multiple rules together

### Multi-Tenant
- Complete isolation by companyId
- Each company has separate channels, products, orders
- Credentials stored securely per company

## Installation

```bash
# Install dependencies
npm install decimal.js typeorm @nestjs/typeorm @nestjs/common @nestjs/core

# Ensure TypeORM is configured in your app.module.ts
```

## Usage

### Import in Your App

```typescript
import { CommerceModule } from './commerce/commerce.module';

@Module({
  imports: [CommerceModule],
})
export class AppModule {}
```

### Use in Services

```typescript
import { MultiChannelSellingService } from './commerce/services/multi-channel-selling.service';

@Injectable()
export class MyService {
  constructor(private multiChannel: MultiChannelSellingService) {}

  async syncProduct() {
    const result = await this.multiChannel.syncProductToChannel(
      'company-id',
      'product-id',
      Channel.SHOPEE,
      new Decimal('100'),
      50
    );
  }
}
```

### REST Endpoints

See [MULTI_CHANNEL_SELLING.md](./MULTI_CHANNEL_SELLING.md#api-endpoints) for complete endpoint documentation.

## Key Methods

### Channel Setup
```typescript
// Add channel
await service.addChannel(companyId, channel, credentials, settings)

// List active channels
await service.listActiveChannels(companyId)

// Deactivate
await service.deactivateChannel(companyId, channel)
```

### Product Sync
```typescript
// Sync to channel
await service.syncProductToChannel(companyId, productId, channel, price, stock)

// Update price
await service.updateChannelProductPrice(companyId, productId, channel, newPrice)

// Update stock
await service.updateChannelProductStock(companyId, productId, channel, newStock)
```

### Inventory
```typescript
// Distribute across channels
await service.syncInventoryToAllChannels(companyId, productId, totalStock)

// Get channel inventory
await service.getChannelInventory(companyId, channel, limit, offset)
```

### Orders
```typescript
// Import order
await service.importOrderFromChannel(companyId, channel, externalOrderId, orderData)

// Update status
await service.updateChannelOrderStatus(companyId, orderId, channel, status)

// Get orders
await service.getChannelOrders(companyId, channel, limit, offset)
```

### Pricing
```typescript
// Set rules
await service.setPriceRuleByChannel(companyId, channel, rules)

// Calculate price
await service.calculateChannelPrice(companyId, channel, baseCost)
```

## Testing

```bash
# Run tests
npm test multi-channel-selling.service.spec.ts

# Run specific test suite
npm test -- --testNamePattern="Channel Management"

# Run with coverage
npm test -- --coverage
```

### Test Coverage

- ✅ 60+ test cases
- ✅ Channel CRUD operations
- ✅ Product sync to each channel
- ✅ Price & stock updates
- ✅ Inventory distribution (including remainder handling)
- ✅ Order import from each channel
- ✅ Channel-specific order status
- ✅ Multi-tenant isolation
- ✅ Price tier calculation with all rule types
- ✅ Edge cases: stock depletion, concurrent operations, large distributions
- ✅ Error handling & validation

## Database Schema

### channel_configs
Stores marketplace API credentials and settings.
- Unique constraint on (companyId, channel)
- Indexes on (companyId, isActive)

### channel_products  
Maps internal products to marketplace listings.
- Unique constraint on (companyId, productId, channel)
- Indexes on channel lookups and external product IDs

### orders
Marketplace orders synced to nirvacore.
- Unique constraint on (companyId, externalOrderId, channel)
- Indexes on channel and status lookups

### products
Internal product catalog.
- Unique constraint on SKU
- Indexed by companyId

## Error Handling

All methods include proper error handling:

```typescript
// Invalid channel
throw new BadRequestException('Invalid channel: invalid_channel')

// Duplicate channel
throw new ConflictException('Channel shopee already configured...')

// Not found
throw new NotFoundException('Channel shopee not configured')

// Invalid input
throw new BadRequestException('Price must be greater than zero')
```

## Design Patterns

### Repository Pattern
Uses TypeORM repositories for database access with clean abstraction.

### Service Layer
Business logic separated from HTTP layer. Easy to use in services, controllers, or job queues.

### Decimal Precision
Uses `decimal.js` for all monetary calculations to avoid floating-point errors.

### Multi-Tenant by Default
Every query filters by `companyId`. No cross-company data access.

### Upsert Semantics
Order import uses upsert logic - duplicate external IDs update existing orders.

## Configuration

Channel-specific settings:

```typescript
settings: {
  enableAutoSync: true,           // Auto-sync on schedule
  syncInterval: 60,               // Minutes between syncs
  defaultMargin: '1.2',           // 20% markup
  enableInventoryDistribution: true,  // Proportional distribution
  maxStockPerChannel: 1000,       // Per-channel stock cap
}
```

Price rules per channel:

```typescript
rules: {
  costMultiplier: '1.5',          // 1.5x base cost
  fixedMarkup: '50',              // +50 THB
  discountPercentage: '10',       // -10%
  minPrice: '50',                 // Floor price
  maxPrice: '500',                // Ceiling price
}
```

## Performance

- **Indexes**: All queries use indexed columns
- **Pagination**: Large result sets paginated (default 50)
- **Async**: Non-blocking operations
- **Decimal**: Precise monetary calculations
- **Error Recovery**: Handles failures gracefully

## Future Roadmap

- [ ] Webhook integration for real-time order updates
- [ ] Bulk operations (sync 100 products at once)
- [ ] Automatic price adjustment rules
- [ ] Product variant support
- [ ] Return/refund management
- [ ] Channel performance analytics
- [ ] Rate limiting per marketplace
- [ ] Retry logic with exponential backoff

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md)

## License

Part of nirvacore-v1. See LICENSE in project root.

## Support

For issues or questions:
1. Check [MULTI_CHANNEL_SELLING.md](./MULTI_CHANNEL_SELLING.md) for detailed documentation
2. Review test suite for usage examples
3. Check error messages in service logs
