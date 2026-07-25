# Business Intelligence Service - Quick Start Guide

Get started with the Business Intelligence Service in 5 minutes!

## 1. Installation & Setup

### Step 1: Import AnalyticsModule

In your `app.module.ts`:

```typescript
import { AnalyticsModule } from './analytics/analytics.module';

@Module({
  imports: [
    TypeOrmModule.forRoot({
      // ... your database config
    }),
    AnalyticsModule, // Add this
  ],
})
export class AppModule {}
```

### Step 2: Run Database Migrations

The service automatically creates the required tables:

```bash
npm run typeorm migration:generate src/migrations/CreateAnalyticsTables
npm run typeorm migration:run
```

## 2. Basic Usage

### Inject Service

```typescript
import { BusinessIntelligenceService } from './analytics';

@Injectable()
export class MyService {
  constructor(private biService: BusinessIntelligenceService) {}
}
```

### Common Operations

#### Get Revenue

```typescript
const revenue = await this.biService.getSalesRevenue(
  'company-123',
  new Date('2024-07-01'),
  new Date('2024-07-31'),
  'day' // or 'week', 'month'
);
```

#### Get Growth Rate

```typescript
const growth = await this.biService.getSalesGrowth('company-123', 'month');
console.log(`Growth: ${growth.growthPercentage}%`);
```

#### Get Top Products

```typescript
const topProducts = await this.biService.getTopProducts(
  'company-123',
  10, // limit
  'revenue' // or 'quantity', 'profit'
);
```

#### Get Profitability

```typescript
const margin = await this.biService.getProfitMargin(
  'company-123',
  new Date('2024-07-01'),
  new Date('2024-07-31')
);
console.log(`Profit Margin: ${margin}%`);
```

## 3. API Quick Reference

### Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/analytics/business-intelligence/sales/revenue` | GET | Daily/weekly/monthly revenue |
| `/analytics/business-intelligence/sales/growth` | GET | Sales growth metrics |
| `/analytics/business-intelligence/sales/by-channel` | GET | Revenue by channel |
| `/analytics/business-intelligence/customers/analytics` | GET | Retention & churn |
| `/analytics/business-intelligence/products/top` | GET | Top performing products |
| `/analytics/business-intelligence/profitability/metrics` | GET | Profit analysis |
| `/analytics/business-intelligence/products/slow-movers` | GET | Slow-moving inventory |
| `/analytics/business-intelligence/dashboards/list` | GET | List dashboards |
| `/analytics/business-intelligence/dashboards/create` | POST | Create dashboard |
| `/analytics/business-intelligence/reports/generate` | POST | Generate reports |

### Example Requests

#### cURL Examples

```bash
# Get daily revenue
curl "http://localhost:3000/analytics/business-intelligence/sales/revenue?companyId=company-123&from=2024-07-01&to=2024-07-31&groupBy=day"

# Get sales growth
curl "http://localhost:3000/analytics/business-intelligence/sales/growth?companyId=company-123&period=month"

# Get top 10 products by revenue
curl "http://localhost:3000/analytics/business-intelligence/products/top?companyId=company-123&limit=10&sortBy=revenue"

# Get retention metrics
curl "http://localhost:3000/analytics/business-intelligence/customers/analytics?companyId=company-123&days=30"

# Get profitability metrics
curl "http://localhost:3000/analytics/business-intelligence/profitability/metrics?companyId=company-123&from=2024-07-01&to=2024-07-31"
```

#### TypeScript Examples

```typescript
// Get revenue
const response = await fetch(
  'http://localhost:3000/analytics/business-intelligence/sales/revenue?' +
  'companyId=company-123&from=2024-07-01&to=2024-07-31&groupBy=day'
);
const data = await response.json();

// Get top products
const productsResponse = await fetch(
  'http://localhost:3000/analytics/business-intelligence/products/top?' +
  'companyId=company-123&limit=10&sortBy=revenue'
);
const products = await productsResponse.json();

// Generate report
const reportResponse = await fetch(
  'http://localhost:3000/analytics/business-intelligence/reports/generate',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      companyId: 'company-123',
      type: 'sales',
      format: 'csv',
      from: '2024-07-01',
      to: '2024-07-31',
    }),
  }
);
const report = await reportResponse.json();
```

## 4. Real-World Scenarios

### Scenario 1: Track Monthly Revenue

```typescript
async trackMonthlyRevenue(companyId: string) {
  const currentMonth = new Date();
  const from = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1);
  const to = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 0);

  const revenue = await this.biService.getSalesRevenue(companyId, from, to, 'day');
  const growth = await this.biService.getSalesGrowth(companyId, 'month');

  return {
    dailyRevenue: revenue,
    monthlyGrowth: growth,
    totalRevenue: revenue.reduce((sum, day) => sum.plus(day.revenue), new Decimal(0)),
  };
}
```

### Scenario 2: Identify Best-Selling Products

```typescript
async identifyBestSellers(companyId: string) {
  const topByRevenue = await this.biService.getTopProducts(companyId, 5, 'revenue');
  const topByQuantity = await this.biService.getTopProducts(companyId, 5, 'quantity');
  const topByProfit = await this.biService.getTopProducts(companyId, 5, 'profit');

  return {
    topByRevenue,
    topByQuantity,
    topByProfit,
  };
}
```

### Scenario 3: Monitor Profitability

```typescript
async monitorProfitability(companyId: string) {
  const margin = await this.biService.getProfitMargin(
    companyId,
    new Date('2024-07-01'),
    new Date('2024-07-31')
  );

  const byProduct = await this.biService.getProfitByProduct(companyId);
  const byChannel = await this.biService.getProfitByChannel(companyId);

  if (margin.lessThan(new Decimal('20'))) {
    // Alert: Profit margin below target
  }

  return { margin, byProduct, byChannel };
}
```

### Scenario 4: Customer Health Check

```typescript
async checkCustomerHealth(companyId: string) {
  const retention = await this.biService.getRetentionRate(companyId, 30);
  const churn = await this.biService.getChurnRate(companyId, 30);

  const status = {
    retention,
    churn,
    healthy: retention > 70,
  };

  if (churn > 30) {
    // Alert: High churn rate
  }

  return status;
}
```

### Scenario 5: Inventory Management

```typescript
async optimizeInventory(companyId: string) {
  // Find slow-moving products
  const slowMovers = await this.biService.getSlowMovers(companyId, 90);

  // Find fast movers
  const topSellers = await this.biService.getTopProducts(companyId, 20, 'quantity');

  return {
    recommendation: 'Clear slow movers, increase inventory for top sellers',
    slowMovers,
    topSellers,
  };
}
```

### Scenario 6: Create Executive Dashboard

```typescript
async createExecutiveDashboard(companyId: string) {
  const dashboard = await this.biService.createDashboard(
    companyId,
    'Executive Dashboard',
    [
      {
        key: 'monthly_revenue',
        label: 'Monthly Revenue',
        type: 'revenue',
      },
      {
        key: 'growth_rate',
        label: 'Growth Rate',
        type: 'growth',
        params: { period: 'month' },
      },
      {
        key: 'customer_retention',
        label: 'Customer Retention',
        type: 'retention',
        params: { days: 30 },
      },
      {
        key: 'profit_margin',
        label: 'Profit Margin',
        type: 'margin',
      },
    ]
  );

  // Get live dashboard data
  const data = await this.biService.getDashboardData(companyId, dashboard.id);

  return data;
}
```

## 5. Testing Your Setup

### Basic Test

```typescript
import { Test } from '@nestjs/testing';
import { BusinessIntelligenceService } from './analytics';

describe('Business Intelligence Service', () => {
  let service: BusinessIntelligenceService;

  beforeEach(async () => {
    const module = await Test.createTestingModule({
      imports: [AnalyticsModule],
    }).compile();

    service = module.get(BusinessIntelligenceService);
  });

  it('should retrieve sales revenue', async () => {
    const result = await service.getSalesRevenue(
      'test-company',
      new Date('2024-07-01'),
      new Date('2024-07-31')
    );

    expect(Array.isArray(result)).toBe(true);
  });
});
```

## 6. Configuration Options

### Database Connection

```typescript
// .env
DATABASE_TYPE=postgres
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USERNAME=user
DATABASE_PASSWORD=password
DATABASE_NAME=nirvacore
```

### Service Options

The service automatically configures itself based on database availability. No additional configuration needed!

## 7. Troubleshooting

### Issue: "SalesAnalytics entity not found"

**Solution**: Ensure `AnalyticsModule` is imported in `AppModule`:

```typescript
@Module({
  imports: [AnalyticsModule],
})
export class AppModule {}
```

### Issue: "companyId is required"

**Solution**: Always pass a valid company ID:

```typescript
// ❌ Wrong
await service.getSalesRevenue(null, from, to);

// ✅ Correct
await service.getSalesRevenue('company-123', from, to);
```

### Issue: No data returned

**Solution**: Ensure analytics data exists in database:

```typescript
// Check if data exists
const count = await salesAnalyticsRepo.count({ where: { companyId } });
console.log(`Found ${count} records`);
```

### Issue: Date range errors

**Solution**: Use ISO date format:

```typescript
// ✅ Correct
const from = new Date('2024-07-01'); // ISO format
const to = new Date('2024-07-31');

// Verify dates
console.log(from.toISOString()); // 2024-07-01T00:00:00.000Z
```

## 8. Next Steps

1. **Read Full Documentation**: See `BUSINESS_INTELLIGENCE_README.md`
2. **Explore Examples**: Check service methods in `business-intelligence.service.ts`
3. **Test Suite**: Review `business-intelligence.service.spec.ts` for patterns
4. **API Reference**: Use controller endpoints documented in main README
5. **Production Deployment**: Configure indexes and caching strategies

## 9. Performance Tips

### For Best Performance:

1. **Always specify date ranges** - Avoid querying entire dataset
2. **Use pagination** - Set appropriate `limit` values
3. **Cache dashboards** - Reuse dashboard configs
4. **Batch reports** - Generate reports during off-peak hours
5. **Index frequently queried fields** - Already configured in entities

### Example Optimized Query:

```typescript
// ❌ Slow - querying entire dataset
const allData = await service.getTopProducts(companyId, 10000);

// ✅ Fast - limited results
const topData = await service.getTopProducts(companyId, 50);
```

## Support

For issues, questions, or feature requests:

1. Check this quick start guide
2. Review full documentation
3. Examine test cases
4. Check error messages and troubleshooting section

Good luck! 🚀
