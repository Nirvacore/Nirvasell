import { Decimal } from 'decimal.js';

export class SalesDataDto {
  date: Date;
  revenue: Decimal;
  orders: number;
  customers: number;
  averageOrderValue: Decimal;
  growth?: Decimal;
}

export class ChannelRevenueDto {
  channel: string;
  revenue: Decimal;
  orderCount: number;
  percentage: Decimal;
}

export class SalesGrowthDto {
  current: Decimal;
  previous: Decimal;
  growth: Decimal;
  growthPercentage: Decimal;
}

export class CustomerMetricsDto {
  customerId: string;
  customerName?: string;
  lifetimeValue: Decimal;
  totalOrders: number;
  repeatOrders: number;
  firstPurchase: Date;
  lastPurchase: Date;
}

export class ProductMetricsDto {
  productId: string;
  productName: string;
  revenue: Decimal;
  unitsSold: number;
  profit: Decimal;
  profitMargin: Decimal;
  revenueContribution: Decimal;
  daysInStock?: number;
}

export class ProfitAnalysisDto {
  period: string;
  revenue: Decimal;
  costOfGoodsSold: Decimal;
  operatingExpenses: Decimal;
  grossProfit: Decimal;
  netProfit: Decimal;
  grossMargin: Decimal;
  netMargin: Decimal;
}

export class CohortDataDto {
  month: string;
  startingCustomers: number;
  retainingCustomers: number;
  retentionRate: Decimal;
  cohortRevenue: Decimal;
  cohortProfit: Decimal;
}

export class DashboardDataDto {
  dashboardId: string;
  name: string;
  kpis: Record<string, any>;
  generatedAt: Date;
}

export class ReportDto {
  id: string;
  companyId: string;
  type: 'sales' | 'customer' | 'product' | 'profit';
  format: 'pdf' | 'csv';
  content: string | Buffer;
  generatedAt: Date;
  fileSize: number;
}

export class BreakEvenAnalysisDto {
  fixedCosts: Decimal;
  variableCostPerUnit: Decimal;
  sellingPricePerUnit: Decimal;
  breakEvenUnits: number;
  breakEvenRevenue: Decimal;
  contributionMargin: Decimal;
  safetyMargin: Decimal;
}
