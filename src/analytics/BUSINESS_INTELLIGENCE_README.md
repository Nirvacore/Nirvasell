# Business Intelligence Service (BI Service)

A comprehensive analytics and business intelligence service for nirvacore-v1 built with NestJS and TypeORM. Provides advanced analytics capabilities for multi-tenant e-commerce platforms.

## Overview

The Business Intelligence Service offers complete analytics capabilities:

- **Sales Analytics**: Revenue trends, growth analysis, channel breakdown, AOV
- **Customer Analytics**: Lifetime value, retention rates, churn analysis, cohort analysis
- **Product Performance**: Top sellers, revenue contribution, slow movers, product metrics
- **Profitability Analysis**: Margin analysis, cost breakdown, profit by product/channel, break-even analysis
- **Custom Dashboards**: Configurable KPI dashboards with real-time data
- **Report Generation**: Multi-format reports (PDF/CSV) for all analytics categories
- **Multi-Tenant Isolation**: Complete data isolation per company

## Architecture

### Directory Structure

```
src/analytics/
├── controllers/
│   └── business-intelligence.controller.ts    # 12 API endpoints
├── services/
│   ├── business-intelligence.service.ts       # Core service logic (400+ lines)
│   └── business-intelligence.service.spec.ts  # 45+ comprehensive tests
├── entities/
│   ├── sales-analytics.entity.ts              # Sales data models
│   ├── customer-analytics.entity.ts           # Customer metrics
│   ├── product-analytics.entity.ts            # Product performance
│   ├── profitability-analytics.entity.ts      # Profitability metrics
│   └── dashboard.entity.ts                    # Dashboard configurations
├── dtos/
│   └── analytics.dto.ts                       # Data transfer objects
├── analytics.module.ts                        # Module definition
└── index.ts                                   # Public exports
```

### Entity Relationships

```
Dashboard
├── contains: Array of KPIs
└── references: Multiple analytics entities

Sales Analytics
├── by Company (multi-tenant)
├── by Channel
└── by Time Period

Customer Analytics
├── by Company (multi-tenant)
├── by Customer
└── by Cohort Month

Product Analytics
├── by Company (multi-tenant)
├── by Product
└── ranked by metrics

Profitability Analytics
├── by Company (multi-tenant)
├── by Product/Channel
└── by Time Period
```

## Key Features

### 1. Sales Analytics

#### Get Sales Revenue
```typescript
getSalesRevenue(companyId, from, to, groupBy: 'day'|'week'|'month')
```

- **Purpose**: Retrieve revenue data for a specified period
- **Grouping**: Automatic aggregation by time period
- **Returns**: Array of SalesDataDto with revenue, orders, customers, AOV

#### Get Sales Growth
```typescript
getSalesGrowth(companyId, period: 'week'|'month'|'quarter'|'year')
```

- **Purpose**: Compare current vs previous period
- **Calculations**: Growth amount and percentage
- **Returns**: SalesGrowthDto with current, previous, growth, and growth%

#### Get Revenue by Channel
```typescript
getRevenueByChannel(companyId, from, to)
```

- **Purpose**: Break down revenue by sales channel
- **Calculation**: Percentage contribution per channel
- **Returns**: Array of ChannelRevenueDto

#### Get Average Order Value
```typescript
getAverageOrderValue(companyId, from, to)
```

- **Purpose**: Calculate AOV for the period
- **Formula**: Total Revenue / Total Orders
- **Returns**: Decimal (AOV value)

### 2. Customer Analytics

#### Get Customer Lifetime Value
```typescript
getCustomerLifetimeValue(companyId, customerId)
```

- **Purpose**: Get total value a customer has generated
- **Use Case**: Customer segmentation, VIP identification
- **Returns**: Decimal (LTV amount)

#### Get Retention Rate
```typescript
getRetentionRate(companyId, days)
```

- **Purpose**: Measure customer loyalty
- **Calculation**: (Retained Customers / Starting Customers) × 100
- **Returns**: Number (percentage 0-100)

#### Get Churn Rate
```typescript
getChurnRate(companyId, days)
```

- **Purpose**: Identify customer loss
- **Formula**: 100 - Retention Rate
- **Returns**: Number (percentage 0-100)

#### Get Customer Cohort
```typescript
getCustomerCohort(companyId, cohortMonth: string)
```

- **Purpose**: Analyze cohort behavior over time
- **Period Format**: 'YYYY-MM'
- **Returns**: CohortDataDto with retention tracking

### 3. Product Performance

#### Get Top Products
```typescript
getTopProducts(companyId, limit, by: 'revenue'|'quantity'|'profit')
```

- **Purpose**: Identify best-performing products
- **Sorting Options**: Revenue, units sold, or profit
- **Limit**: 1-1000 products
- **Returns**: Array of ProductMetricsDto

#### Get Product Metrics
```typescript
getProductMetrics(companyId, productId)
```

- **Purpose**: Detailed metrics for a specific product
- **Metrics**: Revenue, units, profit, margin, contribution
- **Returns**: ProductMetricsDto

#### Get Slow Movers
```typescript
getSlowMovers(companyId, threshold: number)
```

- **Purpose**: Identify stagnant inventory
- **Threshold**: Days since last sale (1-365)
- **Use Case**: Inventory optimization, clearance planning
- **Returns**: Array of ProductMetricsDto

#### Get Revenue Contribution
```typescript
getRevenueContribution(companyId)
```

- **Purpose**: Pareto analysis (80/20 rule)
- **Calculation**: Product Revenue / Total Revenue × 100%
- **Returns**: Array with productId and contribution%

### 4. Profitability Analysis

#### Get Profit Margin
```typescript
getProfitMargin(companyId, from, to)
```

- **Purpose**: Overall profitability measurement
- **Formula**: (Net Profit / Revenue) × 100%
- **Returns**: Decimal (percentage)

#### Get Profit by Product
```typescript
getProfitByProduct(companyId)
```

- **Purpose**: Product-level profitability ranking
- **Metrics**: Profit amount and margin per product
- **Returns**: Array with productId, profit, margin

#### Get Profit by Channel
```typescript
getProfitByChannel(companyId)
```

- **Purpose**: Channel performance comparison
- **Sorted**: By profit descending
- **Returns**: Array with channel and profit

#### Get Break-Even Analysis
```typescript
getBreakEvenAnalysis(companyId)
```

- **Purpose**: Determine profitability thresholds
- **Calculations**:
  - Break-even units = Fixed Costs / Contribution Margin
  - Break-even revenue = Break-even units × Selling Price
  - Safety margin = (Selling Price - Variable Cost) / Selling Price
- **Returns**: BreakEvenAnalysisDto

### 5. Custom Dashboards

#### Create Dashboard
```typescript
createDashboard(companyId, name, kpis)
```

- **Purpose**: Build custom analytics dashboard
- **KPI Types**: revenue, growth, retention, margin, custom
- **Configuration**: Per-KPI parameters
- **Returns**: Dashboard entity with settings

#### Get Dashboard Data
```typescript
getDashboardData(companyId, dashboardId)
```

- **Purpose**: Fetch calculated KPI values
- **Auto-Updates**: lastViewedAt timestamp
- **Returns**: DashboardDataDto with live KPI values

#### List Dashboards
```typescript
listDashboards(companyId)
```

- **Purpose**: View all active dashboards
- **Filtering**: Company and active status
- **Sorting**: By most recently updated
- **Returns**: Array of Dashboard entities

### 6. Report Generation

#### Generate Report
```typescript
generateReport(companyId, type, format, from?, to?)
```

- **Types**: sales, customer, product, profit
- **Formats**: pdf, csv
- **Date Range**: Optional (defaults to last 30 days)
- **Content**: Formatted report data
- **Returns**: ReportDto with file info

## API Endpoints

### 1. GET `/analytics/business-intelligence/sales/revenue`
Get sales revenue for a period with grouping options.

**Query Parameters:**
- `companyId` (required): Company identifier
- `from` (required): Start date (ISO string)
- `to` (required): End date (ISO string)
- `groupBy` (optional): 'day'|'week'|'month' (default: 'day')

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "date": "2024-07-23",
      "revenue": "10000.00",
      "orders": 25,
      "customers": 20,
      "averageOrderValue": "400.00"
    }
  ],
  "count": 1,
  "period": {...}
}
```

### 2. GET `/analytics/business-intelligence/sales/growth`
Get sales growth metrics comparing periods.

**Query Parameters:**
- `companyId` (required)
- `period` (optional): 'week'|'month'|'quarter'|'year' (default: 'month')

**Response:**
```json
{
  "success": true,
  "data": {
    "current": "50000.00",
    "previous": "45000.00",
    "growth": "5000.00",
    "growthPercentage": "11.11"
  },
  "period": "month"
}
```

### 3. GET `/analytics/business-intelligence/sales/by-channel`
Revenue breakdown by sales channel.

**Query Parameters:**
- `companyId` (required)
- `from` (required)
- `to` (required)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "channel": "shopee",
      "revenue": "30000.00",
      "orderCount": 75,
      "percentage": "60.00"
    },
    {
      "channel": "lazada",
      "revenue": "20000.00",
      "orderCount": 50,
      "percentage": "40.00"
    }
  ],
  "total": "50000.00",
  "channelCount": 2
}
```

### 4. GET `/analytics/business-intelligence/customers/analytics`
Customer retention and churn metrics.

**Query Parameters:**
- `companyId` (required)
- `days` (optional): Analysis period in days (default: 30)

**Response:**
```json
{
  "success": true,
  "data": {
    "retentionRate": 75.5,
    "churnRate": 24.5,
    "analysisPeriodDays": 30
  }
}
```

### 5. GET `/analytics/business-intelligence/products/top`
Top performing products with sorting options.

**Query Parameters:**
- `companyId` (required)
- `limit` (optional): Max results 1-1000 (default: 10)
- `sortBy` (optional): 'revenue'|'quantity'|'profit' (default: 'revenue')

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "productId": "prod-123",
      "productName": "Premium Widget",
      "revenue": "50000.00",
      "unitsSold": 500,
      "profit": "15000.00",
      "profitMargin": "30.00",
      "revenueContribution": "25.00"
    }
  ],
  "count": 10,
  "sortedBy": "revenue"
}
```

### 6. GET `/analytics/business-intelligence/profitability/metrics`
Comprehensive profitability analysis.

**Query Parameters:**
- `companyId` (required)
- `from` (required)
- `to` (required)

**Response:**
```json
{
  "success": true,
  "data": {
    "overallMargin": "25.50",
    "byProduct": [
      {
        "productId": "prod-123",
        "profit": "15000.00",
        "margin": "30.00"
      }
    ],
    "byChannel": [
      {
        "channel": "shopee",
        "profit": "12000.00"
      }
    ]
  },
  "period": {...}
}
```

### 7. GET `/analytics/business-intelligence/products/slow-movers`
Identify slow-moving inventory.

**Query Parameters:**
- `companyId` (required)
- `threshold` (optional): Days without sales (default: 90)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "productId": "prod-456",
      "productName": "Legacy Item",
      "revenue": "1000.00",
      "unitsSold": 5,
      "profit": "200.00",
      "profitMargin": "20.00",
      "daysInStock": 120
    }
  ],
  "count": 5,
  "thresholdDays": 90
}
```

### 8. GET `/analytics/business-intelligence/dashboards/list`
List all active dashboards for company.

**Query Parameters:**
- `companyId` (required)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "dash-123",
      "companyId": "company-456",
      "name": "Executive Dashboard",
      "kpis": [...],
      "isActive": true,
      "lastViewedAt": "2024-07-23T10:30:00Z",
      "createdAt": "2024-07-01T00:00:00Z",
      "updatedAt": "2024-07-23T10:30:00Z"
    }
  ],
  "count": 1
}
```

### 9. POST `/analytics/business-intelligence/dashboards/create`
Create a new custom dashboard.

**Request Body:**
```json
{
  "companyId": "company-123",
  "name": "Sales Executive Dashboard",
  "kpis": [
    {
      "key": "monthly_revenue",
      "label": "Monthly Revenue",
      "type": "revenue"
    },
    {
      "key": "growth_rate",
      "label": "YoY Growth",
      "type": "growth",
      "params": {
        "period": "year"
      }
    },
    {
      "key": "retention_30d",
      "label": "30-Day Retention",
      "type": "retention",
      "params": {
        "days": 30
      }
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "dash-789",
    "name": "Sales Executive Dashboard",
    "kpis": [...]
  },
  "message": "Dashboard created successfully"
}
```

### 10. POST `/analytics/business-intelligence/reports/generate`
Generate analytics reports in multiple formats.

**Request Body:**
```json
{
  "companyId": "company-123",
  "type": "sales",
  "format": "csv",
  "from": "2024-07-01",
  "to": "2024-07-31"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "reportId": "rpt_1721743200000",
    "type": "sales",
    "format": "csv",
    "fileSize": 45678,
    "generatedAt": "2024-07-23T11:00:00Z"
  },
  "content": "date,revenue,orders,customers,aov\n2024-07-23,10000,25,20,400\n..."
}
```

## Usage Examples

### Basic Setup (AppModule)

```typescript
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AnalyticsModule } from './analytics/analytics.module';

@Module({
  imports: [
    TypeOrmModule.forRoot({
      type: 'postgres',
      host: 'localhost',
      port: 5432,
      username: 'user',
      password: 'password',
      database: 'nirvacore',
      entities: [__dirname + '/**/*.entity{.ts,.js}'],
      synchronize: false,
    }),
    AnalyticsModule,
  ],
})
export class AppModule {}
```

### Sales Analytics Example

```typescript
const companyId = 'company-123';
const from = new Date('2024-07-01');
const to = new Date('2024-07-31');

// Get daily revenue
const dailyRevenue = await biService.getSalesRevenue(companyId, from, to, 'day');

// Get monthly growth
const growth = await biService.getSalesGrowth(companyId, 'month');

// Get channel breakdown
const channels = await biService.getRevenueByChannel(companyId, from, to);
```

### Customer Analytics Example

```typescript
const customerId = 'cust-456';

// Get customer LTV
const ltv = await biService.getCustomerLifetimeValue(companyId, customerId);

// Get retention metrics
const retention = await biService.getRetentionRate(companyId, 30);
const churn = await biService.getChurnRate(companyId, 30);

// Analyze cohort
const cohort = await biService.getCustomerCohort(companyId, '2024-07');
```

### Product Analytics Example

```typescript
// Top products by revenue
const topProducts = await biService.getTopProducts(companyId, 20, 'revenue');

// Slow movers (no sales in 90+ days)
const slowMovers = await biService.getSlowMovers(companyId, 90);

// Revenue contribution (Pareto analysis)
const contribution = await biService.getRevenueContribution(companyId);
```

### Profitability Analysis Example

```typescript
// Overall margin
const margin = await biService.getProfitMargin(companyId, from, to);

// Profit by product
const byProduct = await biService.getProfitByProduct(companyId);

// Break-even analysis
const breakEven = await biService.getBreakEvenAnalysis(companyId);
```

### Dashboard Example

```typescript
// Create dashboard
const dashboard = await biService.createDashboard(companyId, 'Executive Dashboard', [
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
]);

// Get dashboard with live data
const dashboardData = await biService.getDashboardData(companyId, dashboard.id);
```

### Report Generation Example

```typescript
// Generate sales report as CSV
const report = await biService.generateReport(
  companyId,
  'sales',
  'csv',
  new Date('2024-07-01'),
  new Date('2024-07-31'),
);

// Generate profit report as PDF
const profitReport = await biService.generateReport(
  companyId,
  'profit',
  'pdf',
  new Date('2024-07-01'),
  new Date('2024-07-31'),
);
```

## Multi-Tenant Isolation

All queries automatically filter by `companyId` to ensure complete data isolation:

```typescript
// This will only return data for company-123
const data = await biService.getSalesRevenue('company-123', from, to);

// This will only return data for company-456
const data2 = await biService.getSalesRevenue('company-456', from, to);
```

## Performance Considerations

### Indexing Strategy
All entities have indexes on frequently queried fields:
- `SalesAnalytics`: Indexed on `(companyId, dateStart)` and `(companyId, channel)`
- `CustomerAnalytics`: Indexed on `(companyId, customerId)` and `(companyId, cohortMonth)`
- `ProductAnalytics`: Indexed on `(companyId, productId)` and `(companyId, rank)`
- `ProfitabilityAnalytics`: Multiple indexes for filtering options

### Query Optimization
- Use specific date ranges to limit result sets
- Leverage `limit` parameter in top products queries
- Dashboard KPI calculations are cached via `lastViewedAt` tracking
- Reports use aggregation queries for better performance

### Scaling Recommendations
1. **Archive old analytics**: Archive analytics older than 2 years
2. **Materialized views**: Consider materialized views for complex metrics
3. **Cache layer**: Implement Redis for frequently accessed KPIs
4. **Batch processing**: Use background jobs for daily analytics calculations

## Calculation Formulas

### Retention Rate
```
(Customers in period N who also purchased in N-1) / (Customers in N-1) × 100
```

### Churn Rate
```
100 - Retention Rate
```

### Revenue Contribution
```
(Product Revenue / Total Revenue) × 100%
```

### Profit Margin
```
(Revenue - COGS) / Revenue × 100%
```

### Average Order Value
```
Total Revenue / Total Orders
```

### Break-Even Units
```
Fixed Costs / (Selling Price Per Unit - Variable Cost Per Unit)
```

## Testing

Run comprehensive test suite (45+ tests):

```bash
npm test -- business-intelligence.service.spec.ts
```

Tests cover:
- ✅ All analytical calculations
- ✅ Error handling and validation
- ✅ Multi-tenant data isolation
- ✅ Edge cases (empty datasets, large datasets, decimal precision)
- ✅ Report generation in multiple formats
- ✅ Dashboard creation and retrieval

## Error Handling

All endpoints include proper error handling:

- **BadRequestException**: Invalid parameters or validation errors
- **NotFoundException**: Missing data or resources
- **InternalServerErrorException**: Database or calculation errors

### Common Errors

```json
{
  "statusCode": 400,
  "message": "companyId, from, and to are required",
  "error": "Bad Request"
}
```

## Future Enhancements

- [ ] Predictive analytics (ML-based forecasting)
- [ ] Custom metric definitions
- [ ] Real-time alerting system
- [ ] Advanced segmentation
- [ ] Attribution modeling
- [ ] A/B testing framework
- [ ] Automated report scheduling
- [ ] Export to BI tools (Tableau, Looker)
- [ ] API webhooks for analytics events
- [ ] Custom SQL queries interface

## Contributing

1. Add new entity in `entities/` directory
2. Extend service with new methods
3. Add controller endpoint
4. Write comprehensive tests
5. Update this documentation

## License

Copyright © 2024 Nirvasell. All rights reserved.
