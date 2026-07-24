# Multi-Channel Selling Service

A comprehensive TypeScript/NestJS service for syncing products and orders across multiple e-commerce marketplace channels (Shopee, Lazada, TikTok Shop) for Thai merchants.

## Overview

The Multi-Channel Selling Service provides a unified interface for:

- **Channel Management**: Configure API credentials and settings for multiple channels
- **Product Sync**: List products on multiple channels with different prices and inventory
- **Inventory Management**: Distribute stock across channels with automatic sync
- **Order Import**: Pull orders from marketplace channels and sync back to nirvacore
- **Pricing Strategy**: Apply different pricing rules per channel with cost multipliers, markups, and discounts
- **Multi-Tenant**: Complete isolation of data across companies

## Architecture

### Entities

#### ChannelConfig
Stores marketplace configuration per company.

```typescript
{
  id: UUID
  companyId: string
  channel: 'shopee' | 'lazada' | 'tiktok'
  credentials: {
    apiKey: string
    shopId: string
    sellerId?: string (Lazada)
    accessToken?: string (TikTok)
    refreshToken?: string (TikTok)
  }
  settings: {
    enableAutoSync?: boolean
    syncInterval?: number (minutes)
    defaultMargin?: Decimal (1.2 = 20% markup)
    enableInventoryDistribution?: boolean
    maxStockPerChannel?: number
    priceRules?: Map<Channel, PriceRuleData>
  }
  isActive: boolean
}
```

#### ChannelProduct
Maps internal products to marketplace listings with channel-specific pricing and inventory.

```typescript
{
  id: UUID
  companyId: string
  productId: string (internal SKU)
  channel: 'shopee' | 'lazada' | 'tiktok'
  externalProductId: string (marketplace product ID)
  channelSku?: string
  price: Decimal
  stock: number
  lastSyncedAt?: Date
}
```

#### Order
Marketplace orders synced to nirvacore.

```typescript
{
  id: UUID
  companyId: string
  channel: 'shopee' | 'lazada' | 'tiktok'
  externalOrderId: string
  buyerName: string
  buyerPhone?: string
  deliveryAddress: string
  items: [{
    externalProductId: string
    quantity: number
    price: Decimal
  }]
  totalPrice: Decimal
  status: 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled'
  orderDate: Date
  lastSyncedAt?: Date
}
```

### Service Methods

#### Channel Management

```typescript
// Add a new marketplace channel
addChannel(companyId, channel, credentials, settings): Promise<ChannelConfig>

// Get channel configuration
getChannelConfig(companyId, channel): Promise<ChannelConfig | null>

// Update channel settings
updateChannelSettings(companyId, channel, settings): Promise<ChannelConfig>

// List active channels
listActiveChannels(companyId): Promise<ChannelConfig[]>

// Deactivate a channel
deactivateChannel(companyId, channel): Promise<void>
```

#### Product Sync

```typescript
// Sync product to channel
syncProductToChannel(companyId, productId, channel, price, stock): Promise<ChannelProduct>

// Update price on channel
updateChannelProductPrice(companyId, productId, channel, newPrice): Promise<void>

// Update stock on channel
updateChannelProductStock(companyId, productId, channel, newStock): Promise<void>

// Get channel product details
getChannelProduct(companyId, productId, channel): Promise<ChannelProduct | null>

// Get all channel listings for a product
getChannelProductsByProduct(companyId, productId): Promise<ChannelProduct[]>
```

#### Inventory Management

```typescript
// Get channel inventory with pagination
getChannelInventory(companyId, channel, limit?, offset?): Promise<ChannelInventoryData>

// Distribute stock across all active channels proportionally
syncInventoryToAllChannels(companyId, productId, totalStock): Promise<void>

// Get inventory for all channels
getAllChannelInventory(companyId): Promise<Map<Channel, ChannelInventoryData>>
```

#### Order Sync

```typescript
// Import order from marketplace
importOrderFromChannel(companyId, channel, externalOrderId, orderData): Promise<Order>

// Get channel orders with pagination
getChannelOrders(companyId, channel, limit?, offset?): Promise<{ orders: Order[], total: number }>

// Update order status
updateChannelOrderStatus(companyId, orderId, channel, status): Promise<void>

// Get orders by status
getOrdersByStatus(companyId, channel, status): Promise<Order[]>
```

#### Pricing Strategy

```typescript
// Get pricing tiers for all channels
getChannelPricingTiers(companyId): Promise<PricingTier[]>

// Set price rules for a channel
setPriceRuleByChannel(companyId, channel, rules): Promise<void>

// Calculate final price with rules applied
calculateChannelPrice(companyId, channel, baseCost): Promise<Decimal>
```

## Usage Examples

### Setting Up a Channel

```typescript
const service = app.get(MultiChannelSellingService);

// Add Shopee channel
await service.addChannel(
  'company-123',
  Channel.SHOPEE,
  {
    apiKey: 'shopee-api-key',
    shopId: 'shop-123',
  },
  {
    enableAutoSync: true,
    syncInterval: 60,
    defaultMargin: new Decimal('1.2'),
  }
);

// Add Lazada channel
await service.addChannel(
  'company-123',
  Channel.LAZADA,
  {
    apiKey: 'lazada-api-key',
    shopId: 'shop-456',
    sellerId: 'seller-789',
  },
  {
    enableAutoSync: true,
    syncInterval: 120,
  }
);

// Add TikTok Shop channel
await service.addChannel(
  'company-123',
  Channel.TIKTOK,
  {
    apiKey: 'tiktok-api-key',
    shopId: 'shop-999',
    accessToken: 'access-token',
    refreshToken: 'refresh-token',
  },
);
```

### Syncing Products

```typescript
// Sync product to Shopee at 100 THB, 50 units
const channelProduct = await service.syncProductToChannel(
  'company-123',
  'product-1',
  Channel.SHOPEE,
  new Decimal('100'),
  50,
);

// Update price on Lazada to 120 THB
await service.updateChannelProductPrice(
  'company-123',
  'product-1',
  Channel.LAZADA,
  new Decimal('120'),
);

// Update stock on TikTok to 30 units
await service.updateChannelProductStock(
  'company-123',
  'product-1',
  Channel.TIKTOK,
  30,
);

// Get current price/stock on Shopee
const channelProduct = await service.getChannelProduct(
  'company-123',
  'product-1',
  Channel.SHOPEE,
);
console.log(channelProduct.price, channelProduct.stock);
```

### Inventory Distribution

```typescript
// Distribute 300 total units across all 3 active channels
// Shopee: 100, Lazada: 100, TikTok: 100
await service.syncInventoryToAllChannels(
  'company-123',
  'product-1',
  300,
);

// Get inventory for all channels
const inventoryMap = await service.getAllChannelInventory('company-123');
inventoryMap.forEach((inventory, channel) => {
  console.log(`${channel}: ${inventory.totalSKUs} SKUs`);
});
```

### Pricing Strategy

```typescript
// Set up different pricing rules per channel
// Shopee: 1.5x cost multiplier (50% markup)
await service.setPriceRuleByChannel(
  'company-123',
  Channel.SHOPEE,
  {
    costMultiplier: new Decimal('1.5'),
  }
);

// Lazada: 1.3x multiplier + 50 THB fixed markup
await service.setPriceRuleByChannel(
  'company-123',
  Channel.LAZADA,
  {
    costMultiplier: new Decimal('1.3'),
    fixedMarkup: new Decimal('50'),
  }
);

// TikTok: 1.2x multiplier with 10% discount
await service.setPriceRuleByChannel(
  'company-123',
  Channel.TIKTOK,
  {
    costMultiplier: new Decimal('1.2'),
    discountPercentage: new Decimal('10'),
    minPrice: new Decimal('50'),
    maxPrice: new Decimal('500'),
  }
);

// Calculate prices for a product with 200 THB cost
const shopeePrice = await service.calculateChannelPrice(
  'company-123',
  Channel.SHOPEE,
  new Decimal('200'),
); // 300 THB

const lazadaPrice = await service.calculateChannelPrice(
  'company-123',
  Channel.LAZADA,
  new Decimal('200'),
); // 310 THB (260 + 50)

const tiktokPrice = await service.calculateChannelPrice(
  'company-123',
  Channel.TIKTOK,
  new Decimal('200'),
); // 216 THB (240 * 0.9)
```

### Order Import

```typescript
// Import order from Shopee
const order = await service.importOrderFromChannel(
  'company-123',
  Channel.SHOPEE,
  'shopee-order-123',
  {
    externalOrderId: 'shopee-order-123',
    buyerName: 'สมชาย ใจสว่าง',
    buyerPhone: '0812345678',
    deliveryAddress: 'กรุงเทพมหานคร',
    items: [
      {
        externalProductId: 'shopee-product-1',
        quantity: 2,
        price: new Decimal('100'),
      },
    ],
    totalPrice: new Decimal('200'),
    orderDate: new Date(),
    status: 'confirmed',
  }
);

// Get recent orders from channel
const { orders, total } = await service.getChannelOrders(
  'company-123',
  Channel.LAZADA,
  50,
  0,
);

// Update order status
await service.updateChannelOrderStatus(
  'company-123',
  order.id,
  Channel.SHOPEE,
  'shipped',
);

// Get pending orders
const pendingOrders = await service.getOrdersByStatus(
  'company-123',
  Channel.SHOPEE,
  'pending',
);
```

## Key Features

### 1. Multi-Tenant Isolation
All data is filtered by `companyId`. Credentials and inventory are completely isolated between companies.

### 2. Flexible Pricing
Apply different pricing strategies per channel:
- **Cost Multiplier**: 1.5x base cost
- **Fixed Markup**: Add fixed amount (e.g., +50 THB)
- **Discount Percentage**: Apply percentage discount (e.g., -10%)
- **Min/Max Bounds**: Enforce price limits per channel

### 3. Inventory Distribution
Proportionally distribute total stock across active channels:
- 300 units across 3 channels = 100 per channel
- Handles remainders (301 units = 101, 100, 100)
- Automatic error recovery on sync failures

### 4. Order Synchronization
- Upsert semantics: duplicate external IDs update existing orders
- Product validation: orders can only reference synced products
- Status tracking: pending → confirmed → shipped → delivered/cancelled

### 5. Error Handling
- Validation of channel credentials per channel type
- Business logic constraints (negative prices/stock rejected)
- Not found errors with helpful context
- Conflict detection (duplicate channels)

## Testing

The service includes 60+ comprehensive test cases covering:

- **Channel Management**: Add, update, get, list, deactivate
- **Product Sync**: Sync, price update, stock update, retrieval
- **Inventory Distribution**: Proportional distribution, edge cases, remainder handling
- **Order Import**: Import, upsert, status update, filtering
- **Pricing**: All rule types, combined rules, bounds enforcement
- **Multi-Tenant**: Data isolation across companies
- **Edge Cases**: Stock depletion, concurrent operations, large distributions

Run tests:
```bash
npm test src/commerce/services/multi-channel-selling.service.spec.ts
```

## Integration with NestJS

### Module Setup

```typescript
import { Module } from '@nestjs/common';
import { CommerceModule } from './commerce/commerce.module';

@Module({
  imports: [CommerceModule],
})
export class AppModule {}
```

### In a Service

```typescript
@Injectable()
export class MyService {
  constructor(private multiChannelService: MultiChannelSellingService) {}

  async handleOrderEvent(event: OrderEvent) {
    const order = await this.multiChannelService.importOrderFromChannel(...);
    // Process order...
  }
}
```

### In a Controller

```typescript
@Controller('api/commerce')
export class MyController {
  constructor(private multiChannelService: MultiChannelSellingService) {}

  @Post('sync-product')
  async syncProduct(@Body() dto: SyncProductDto) {
    return this.multiChannelService.syncProductToChannel(...);
  }
}
```

## Database Schema

### channel_configs
```sql
CREATE TABLE channel_configs (
  id UUID PRIMARY KEY,
  companyId VARCHAR NOT NULL,
  channel VARCHAR NOT NULL,
  credentials JSONB NOT NULL,
  settings JSONB,
  isActive BOOLEAN DEFAULT true,
  createdAt TIMESTAMP,
  updatedAt TIMESTAMP,
  UNIQUE(companyId, channel)
);

CREATE INDEX ON channel_configs(companyId, isActive);
```

### channel_products
```sql
CREATE TABLE channel_products (
  id UUID PRIMARY KEY,
  companyId VARCHAR NOT NULL,
  productId VARCHAR NOT NULL,
  channel VARCHAR NOT NULL,
  externalProductId VARCHAR NOT NULL,
  channelSku VARCHAR,
  price DECIMAL(12, 2) NOT NULL,
  stock INT NOT NULL,
  lastSyncedAt TIMESTAMP,
  createdAt TIMESTAMP,
  updatedAt TIMESTAMP,
  UNIQUE(companyId, productId, channel)
);

CREATE INDEX ON channel_products(companyId, channel);
CREATE INDEX ON channel_products(externalProductId, channel);
```

### orders
```sql
CREATE TABLE orders (
  id UUID PRIMARY KEY,
  companyId VARCHAR NOT NULL,
  channel VARCHAR NOT NULL,
  externalOrderId VARCHAR NOT NULL,
  buyerName VARCHAR NOT NULL,
  buyerPhone VARCHAR,
  deliveryAddress TEXT NOT NULL,
  items JSONB NOT NULL,
  totalPrice DECIMAL(12, 2) NOT NULL,
  status VARCHAR NOT NULL,
  orderDate TIMESTAMP NOT NULL,
  lastSyncedAt TIMESTAMP,
  createdAt TIMESTAMP,
  updatedAt TIMESTAMP,
  UNIQUE(companyId, externalOrderId, channel)
);

CREATE INDEX ON orders(companyId, channel);
CREATE INDEX ON orders(companyId, status);
```

## Performance Considerations

1. **Indexing**: All queries use indexed columns for fast lookup
2. **Pagination**: Large result sets are paginated (default 50 items)
3. **Decimal Precision**: All prices use Decimal.js for precise calculations
4. **Batch Operations**: Inventory distribution works across channels
5. **Async Handling**: Channel API calls are non-blocking

## Future Enhancements

1. **Bulk Operations**: Sync multiple products/orders in one call
2. **Webhook Integration**: Real-time order notifications from channels
3. **Rate Limiting**: Respect marketplace API rate limits
4. **Retry Logic**: Automatic retry with exponential backoff
5. **Analytics**: Sales velocity, channel performance metrics
6. **Automation**: Auto-sync schedules, price adjustment rules
7. **Product Variants**: Support different product variants per channel
8. **Return Management**: Handle returns and refunds per channel

## API Endpoints

All endpoints are prefixed with `/commerce/multi-channel`.

### Channels
- `POST /channels` - Add channel
- `GET /channels` - List active channels
- `GET /channels/:channel` - Get channel config
- `PUT /channels/:channel/settings` - Update settings
- `DELETE /channels/:channel` - Deactivate channel

### Products
- `POST /products/sync/:channel` - Sync product
- `GET /products/:productId/:channel` - Get product details
- `GET /products/:productId/channels` - Get all channel listings
- `PUT /products/:productId/price/:channel` - Update price
- `PUT /products/:productId/stock/:channel` - Update stock

### Inventory
- `GET /inventory` - Get all channel inventory
- `GET /inventory/:channel` - Get channel inventory
- `POST /inventory/distribute` - Distribute stock across channels

### Orders
- `POST /orders/import/:channel` - Import order
- `GET /orders/:channel` - Get channel orders
- `GET /orders/:channel/status/:status` - Get orders by status
- `PUT /orders/:orderId/status/:channel` - Update order status

### Pricing
- `GET /pricing/tiers` - Get pricing tiers
- `POST /pricing/rules/:channel` - Set price rules
- `GET /pricing/calculate/:channel` - Calculate final price

### Analytics
- `GET /stats` - Get multi-channel statistics

## License

Part of nirvacore-v1. See project LICENSE.
