import { Injectable, BadRequestException, NotFoundException, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, Between, MoreThanOrEqual, LessThanOrEqual } from 'typeorm';
import { Decimal } from 'decimal.js';
import { SalesAnalytics } from '../entities/sales-analytics.entity';
import { CustomerAnalytics } from '../entities/customer-analytics.entity';
import { ProductAnalytics } from '../entities/product-analytics.entity';
import { ProfitabilityAnalytics } from '../entities/profitability-analytics.entity';
import { Dashboard } from '../entities/dashboard.entity';
import {
  SalesDataDto,
  ChannelRevenueDto,
  SalesGrowthDto,
  CustomerMetricsDto,
  ProductMetricsDto,
  CohortDataDto,
  DashboardDataDto,
  ReportDto,
  BreakEvenAnalysisDto,
} from '../dtos/analytics.dto';

@Injectable()
export class BusinessIntelligenceService {
  private readonly logger = new Logger(BusinessIntelligenceService.name);

  constructor(
    @InjectRepository(SalesAnalytics)
    private salesAnalyticsRepo: Repository<SalesAnalytics>,
    @InjectRepository(CustomerAnalytics)
    private customerAnalyticsRepo: Repository<CustomerAnalytics>,
    @InjectRepository(ProductAnalytics)
    private productAnalyticsRepo: Repository<ProductAnalytics>,
    @InjectRepository(ProfitabilityAnalytics)
    private profitabilityAnalyticsRepo: Repository<ProfitabilityAnalytics>,
    @InjectRepository(Dashboard)
    private dashboardRepo: Repository<Dashboard>,
  ) {}

  // ============ Sales Analytics ============

  async getSalesRevenue(
    companyId: string,
    from: Date,
    to: Date,
    groupBy: 'day' | 'week' | 'month' = 'day',
  ): Promise<SalesDataDto[]> {
    if (from >= to) {
      throw new BadRequestException('From date must be before To date');
    }

    const analytics = await this.salesAnalyticsRepo.find({
      where: {
        companyId,
        dateStart: MoreThanOrEqual(from),
        dateEnd: LessThanOrEqualTo(to),
      },
      order: { dateStart: 'ASC' },
    });

    const grouped = this.groupByPeriod(analytics, groupBy);

    return grouped.map(item => ({
      date: item.dateStart,
      revenue: item.totalRevenue,
      orders: item.orderCount,
      customers: item.customerCount,
      averageOrderValue: item.averageOrderValue,
    }));
  }

  async getSalesGrowth(companyId: string, period: 'week' | 'month' | 'quarter' | 'year'): Promise<SalesGrowthDto> {
    const [start, end] = this.getPeriodDates(period);
    const [prevStart, prevEnd] = this.getPreviousPeriodDates(period);

    const currentData = await this.salesAnalyticsRepo.find({
      where: {
        companyId,
        dateStart: Between(start, end),
      },
    });

    const previousData = await this.salesAnalyticsRepo.find({
      where: {
        companyId,
        dateStart: Between(prevStart, prevEnd),
      },
    });

    const currentRevenue = currentData.reduce((sum, item) => sum.plus(item.totalRevenue), new Decimal(0));
    const previousRevenue = previousData.reduce((sum, item) => sum.plus(item.totalRevenue), new Decimal(0));

    const growth = currentRevenue.minus(previousRevenue);
    const growthPercentage = previousRevenue.isZero()
      ? new Decimal(0)
      : growth.dividedBy(previousRevenue).times(100);

    return {
      current: currentRevenue,
      previous: previousRevenue,
      growth,
      growthPercentage,
    };
  }

  async getRevenueByChannel(companyId: string, from: Date, to: Date): Promise<ChannelRevenueDto[]> {
    const analytics = await this.salesAnalyticsRepo.find({
      where: {
        companyId,
        dateStart: MoreThanOrEqual(from),
        dateEnd: LessThanOrEqualTo(to),
      },
    });

    const totalRevenue = analytics.reduce((sum, item) => sum.plus(item.totalRevenue), new Decimal(0));

    const channelMap = new Map<string, { revenue: Decimal; orders: number }>();

    analytics.forEach(item => {
      if (item.channel) {
        const existing = channelMap.get(item.channel) || { revenue: new Decimal(0), orders: 0 };
        channelMap.set(item.channel, {
          revenue: existing.revenue.plus(item.totalRevenue),
          orders: existing.orders + item.orderCount,
        });
      }
    });

    return Array.from(channelMap.entries()).map(([channel, data]) => ({
      channel,
      revenue: data.revenue,
      orderCount: data.orders,
      percentage: totalRevenue.isZero() ? new Decimal(0) : data.revenue.dividedBy(totalRevenue).times(100),
    }));
  }

  async getAverageOrderValue(companyId: string, from: Date, to: Date): Promise<Decimal> {
    const analytics = await this.salesAnalyticsRepo.find({
      where: {
        companyId,
        dateStart: MoreThanOrEqual(from),
        dateEnd: LessThanOrEqualTo(to),
      },
    });

    const totalRevenue = analytics.reduce((sum, item) => sum.plus(item.totalRevenue), new Decimal(0));
    const totalOrders = analytics.reduce((sum, item) => sum + item.orderCount, 0);

    return totalOrders === 0 ? new Decimal(0) : totalRevenue.dividedBy(totalOrders);
  }

  // ============ Customer Analytics ============

  async getCustomerLifetimeValue(companyId: string, customerId: string): Promise<Decimal> {
    const analytics = await this.customerAnalyticsRepo.findOne({
      where: { companyId, customerId },
    });

    if (!analytics) {
      throw new NotFoundException('Customer analytics not found');
    }

    return analytics.lifetimeValue;
  }

  async getRetentionRate(companyId: string, days: number = 30): Promise<number> {
    if (days <= 0) {
      throw new BadRequestException('Days must be positive');
    }

    const endDate = new Date();
    const startDate = new Date(endDate.getTime() - days * 24 * 60 * 60 * 1000);

    const retentions = await this.customerAnalyticsRepo.find({
      where: {
        companyId,
        updatedAt: MoreThanOrEqual(startDate),
      },
    });

    if (retentions.length === 0) return 0;

    const retainedCount = retentions.filter(r => r.retentionRate.greaterThan(0)).length;

    return (retainedCount / retentions.length) * 100;
  }

  async getChurnRate(companyId: string, days: number = 30): Promise<number> {
    if (days <= 0) {
      throw new BadRequestException('Days must be positive');
    }

    const retentionRate = await this.getRetentionRate(companyId, days);

    return 100 - retentionRate;
  }

  async getCustomerCohort(companyId: string, cohortMonth: string): Promise<CohortDataDto> {
    const analytics = await this.customerAnalyticsRepo.find({
      where: { companyId, cohortMonth },
    });

    if (analytics.length === 0) {
      throw new NotFoundException('No cohort data found for the specified month');
    }

    const startingCustomers = analytics.length;
    const retainedCount = analytics.filter(a => a.repeatPurchases > 0).length;
    const totalCohortRevenue = analytics.reduce((sum, a) => sum.plus(a.lifetimeValue), new Decimal(0));
    const avgRetentionRate = analytics.reduce((sum, a) => sum.plus(a.retentionRate), new Decimal(0)).dividedBy(analytics.length);

    return {
      month: cohortMonth,
      startingCustomers,
      retainingCustomers: retainedCount,
      retentionRate: new Decimal((retainedCount / startingCustomers) * 100),
      cohortRevenue: totalCohortRevenue,
      cohortProfit: totalCohortRevenue.times(new Decimal('0.3')), // Assume 30% profit margin
    };
  }

  // ============ Product Performance ============

  async getTopProducts(companyId: string, limit: number = 10, by: 'revenue' | 'quantity' | 'profit' = 'revenue'): Promise<ProductMetricsDto[]> {
    if (limit <= 0 || limit > 1000) {
      throw new BadRequestException('Limit must be between 1 and 1000');
    }

    let orderBy: any = {};
    switch (by) {
      case 'quantity':
        orderBy = { unitsSold: 'DESC' };
        break;
      case 'profit':
        orderBy = { totalProfit: 'DESC' };
        break;
      default:
        orderBy = { totalRevenue: 'DESC' };
    }

    const products = await this.productAnalyticsRepo.find({
      where: { companyId },
      order: orderBy,
      take: limit,
    });

    return products.map((p, index) => ({
      productId: p.productId,
      productName: p.productName,
      revenue: p.totalRevenue,
      unitsSold: p.unitsSold,
      profit: p.totalProfit,
      profitMargin: p.profitMargin,
      revenueContribution: p.revenueContribution,
      daysInStock: p.daysSinceLastSale,
    }));
  }

  async getProductMetrics(companyId: string, productId: string): Promise<ProductMetricsDto> {
    const analytics = await this.productAnalyticsRepo.findOne({
      where: { companyId, productId },
    });

    if (!analytics) {
      throw new NotFoundException('Product analytics not found');
    }

    return {
      productId: analytics.productId,
      productName: analytics.productName,
      revenue: analytics.totalRevenue,
      unitsSold: analytics.unitsSold,
      profit: analytics.totalProfit,
      profitMargin: analytics.profitMargin,
      revenueContribution: analytics.revenueContribution,
      daysInStock: analytics.daysSinceLastSale,
    };
  }

  async getSlowMovers(companyId: string, threshold: number = 90): Promise<ProductMetricsDto[]> {
    if (threshold <= 0 || threshold > 365) {
      throw new BadRequestException('Threshold must be between 1 and 365 days');
    }

    const products = await this.productAnalyticsRepo.find({
      where: { companyId },
    });

    const slowMovers = products.filter(p => p.daysSinceLastSale && p.daysSinceLastSale >= threshold);

    return slowMovers.map(p => ({
      productId: p.productId,
      productName: p.productName,
      revenue: p.totalRevenue,
      unitsSold: p.unitsSold,
      profit: p.totalProfit,
      profitMargin: p.profitMargin,
      revenueContribution: p.revenueContribution,
      daysInStock: p.daysSinceLastSale,
    }));
  }

  async getRevenueContribution(companyId: string): Promise<Array<{ productId: string; contribution: Decimal }>> {
    const products = await this.productAnalyticsRepo.find({
      where: { companyId },
      order: { revenueContribution: 'DESC' },
    });

    return products.map(p => ({
      productId: p.productId,
      contribution: p.revenueContribution,
    }));
  }

  // ============ Profitability Analysis ============

  async getProfitMargin(companyId: string, from: Date, to: Date): Promise<Decimal> {
    const analytics = await this.profitabilityAnalyticsRepo.find({
      where: {
        companyId,
        dateStart: MoreThanOrEqual(from),
        dateEnd: LessThanOrEqualTo(to),
      },
    });

    if (analytics.length === 0) {
      return new Decimal(0);
    }

    const totalRevenue = analytics.reduce((sum, item) => sum.plus(item.revenue), new Decimal(0));
    const totalProfit = analytics.reduce((sum, item) => sum.plus(item.netProfit), new Decimal(0));

    return totalRevenue.isZero() ? new Decimal(0) : totalProfit.dividedBy(totalRevenue).times(100);
  }

  async getProfitByProduct(companyId: string): Promise<Array<{ productId: string; profit: Decimal; margin: Decimal }>> {
    const products = await this.productAnalyticsRepo.find({
      where: { companyId },
      order: { totalProfit: 'DESC' },
    });

    return products.map(p => ({
      productId: p.productId,
      profit: p.totalProfit,
      margin: p.profitMargin,
    }));
  }

  async getProfitByChannel(companyId: string): Promise<Array<{ channel: string; profit: Decimal }>> {
    const analytics = await this.profitabilityAnalyticsRepo.find({
      where: { companyId },
    });

    const channelMap = new Map<string, Decimal>();

    analytics.forEach(item => {
      if (item.channel) {
        const existing = channelMap.get(item.channel) || new Decimal(0);
        channelMap.set(item.channel, existing.plus(item.netProfit));
      }
    });

    return Array.from(channelMap.entries())
      .map(([channel, profit]) => ({ channel, profit }))
      .sort((a, b) => b.profit.minus(a.profit).toNumber());
  }

  async getBreakEvenAnalysis(companyId: string): Promise<BreakEvenAnalysisDto> {
    const analytics = await this.profitabilityAnalyticsRepo.find({
      where: { companyId },
    });

    if (analytics.length === 0) {
      throw new NotFoundException('No profitability data found');
    }

    const totalRevenue = analytics.reduce((sum, item) => sum.plus(item.revenue), new Decimal(0));
    const totalCogs = analytics.reduce((sum, item) => sum.plus(item.costOfGoodsSold), new Decimal(0));
    const totalOpEx = analytics.reduce((sum, item) => sum.plus(item.operatingExpenses), new Decimal(0));
    const totalUnits = analytics.reduce((sum, item) => sum + 1, 0);

    const avgSellingPrice = totalRevenue.dividedBy(totalUnits);
    const avgVariableCost = totalCogs.dividedBy(totalUnits);
    const fixedCosts = totalOpEx;
    const contributionMargin = avgSellingPrice.minus(avgVariableCost);

    const breakEvenUnits = fixedCosts.isZero() || contributionMargin.isZero() ? 0 : fixedCosts.dividedBy(contributionMargin).toNumber();

    return {
      fixedCosts,
      variableCostPerUnit: avgVariableCost,
      sellingPricePerUnit: avgSellingPrice,
      breakEvenUnits: Math.ceil(breakEvenUnits),
      breakEvenRevenue: avgSellingPrice.times(new Decimal(breakEvenUnits)),
      contributionMargin,
      safetyMargin: avgSellingPrice.minus(avgVariableCost).dividedBy(avgSellingPrice).times(100),
    };
  }

  // ============ Custom Dashboards ============

  async createDashboard(
    companyId: string,
    name: string,
    kpis: Array<{ key: string; label: string; type: string; params?: Record<string, any> }>,
  ): Promise<Dashboard> {
    if (!name || name.trim().length === 0) {
      throw new BadRequestException('Dashboard name is required');
    }

    if (!kpis || kpis.length === 0) {
      throw new BadRequestException('At least one KPI is required');
    }

    const dashboard = this.dashboardRepo.create({
      companyId,
      name,
      kpis,
      isActive: true,
    });

    return this.dashboardRepo.save(dashboard);
  }

  async getDashboardData(companyId: string, dashboardId: string): Promise<DashboardDataDto> {
    const dashboard = await this.dashboardRepo.findOne({
      where: { id: dashboardId, companyId },
    });

    if (!dashboard) {
      throw new NotFoundException('Dashboard not found');
    }

    const kpiData: Record<string, any> = {};

    for (const kpi of dashboard.kpis) {
      try {
        kpiData[kpi.key] = await this.calculateKpi(companyId, kpi);
      } catch (error) {
        this.logger.warn(`Failed to calculate KPI ${kpi.key}: ${error.message}`);
        kpiData[kpi.key] = null;
      }
    }

    dashboard.lastViewedAt = new Date();
    await this.dashboardRepo.save(dashboard);

    return {
      dashboardId: dashboard.id,
      name: dashboard.name,
      kpis: kpiData,
      generatedAt: new Date(),
    };
  }

  async listDashboards(companyId: string): Promise<Dashboard[]> {
    return this.dashboardRepo.find({
      where: { companyId, isActive: true },
      order: { updatedAt: 'DESC' },
    });
  }

  // ============ Report Generation ============

  async generateReport(
    companyId: string,
    type: 'sales' | 'customer' | 'product' | 'profit',
    format: 'pdf' | 'csv',
    from?: Date,
    to?: Date,
  ): Promise<ReportDto> {
    const reportId = `rpt_${Date.now()}`;
    const startDate = from || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    const endDate = to || new Date();

    let content: string;

    switch (type) {
      case 'sales':
        content = await this.generateSalesReport(companyId, startDate, endDate, format);
        break;
      case 'customer':
        content = await this.generateCustomerReport(companyId, startDate, endDate, format);
        break;
      case 'product':
        content = await this.generateProductReport(companyId, startDate, endDate, format);
        break;
      case 'profit':
        content = await this.generateProfitReport(companyId, startDate, endDate, format);
        break;
      default:
        throw new BadRequestException('Invalid report type');
    }

    return {
      id: reportId,
      companyId,
      type,
      format,
      content,
      generatedAt: new Date(),
      fileSize: Buffer.byteLength(content, 'utf8'),
    };
  }

  // ============ Private Helper Methods ============

  private groupByPeriod(analytics: SalesAnalytics[], period: 'day' | 'week' | 'month'): SalesAnalytics[] {
    const grouped = new Map<string, SalesAnalytics>();

    analytics.forEach(item => {
      const key = this.getPeriodKey(item.dateStart, period);
      const existing = grouped.get(key);

      if (existing) {
        existing.totalRevenue = existing.totalRevenue.plus(item.totalRevenue);
        existing.orderCount += item.orderCount;
        existing.customerCount += item.customerCount;
      } else {
        grouped.set(key, { ...item });
      }
    });

    return Array.from(grouped.values());
  }

  private getPeriodKey(date: Date, period: 'day' | 'week' | 'month'): string {
    const d = new Date(date);

    switch (period) {
      case 'day':
        return d.toISOString().split('T')[0];
      case 'week':
        const weekStart = new Date(d);
        weekStart.setDate(d.getDate() - d.getDay());
        return weekStart.toISOString().split('T')[0];
      case 'month':
        return d.toISOString().substring(0, 7);
    }
  }

  private getPeriodDates(period: string): [Date, Date] {
    const end = new Date();
    const start = new Date();

    switch (period) {
      case 'week':
        start.setDate(end.getDate() - 7);
        break;
      case 'month':
        start.setMonth(end.getMonth() - 1);
        break;
      case 'quarter':
        start.setMonth(end.getMonth() - 3);
        break;
      case 'year':
        start.setFullYear(end.getFullYear() - 1);
        break;
    }

    return [start, end];
  }

  private getPreviousPeriodDates(period: string): [Date, Date] {
    const [start, end] = this.getPeriodDates(period);
    const prevEnd = new Date(start);
    const prevStart = new Date(prevEnd);

    const diffMs = end.getTime() - start.getTime();

    prevStart.setTime(prevEnd.getTime() - diffMs);

    return [prevStart, prevEnd];
  }

  private async calculateKpi(companyId: string, kpi: any): Promise<any> {
    switch (kpi.type) {
      case 'revenue':
        return this.getAverageOrderValue(companyId, new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), new Date());
      case 'growth':
        return this.getSalesGrowth(companyId, kpi.params?.period || 'month');
      case 'retention':
        return this.getRetentionRate(companyId, kpi.params?.days || 30);
      case 'margin':
        return this.getProfitMargin(companyId, new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), new Date());
      default:
        return null;
    }
  }

  private async generateSalesReport(companyId: string, from: Date, to: Date, format: 'pdf' | 'csv'): Promise<string> {
    const revenue = await this.getSalesRevenue(companyId, from, to, 'day');
    const channels = await this.getRevenueByChannel(companyId, from, to);
    const growth = await this.getSalesGrowth(companyId, 'month');

    if (format === 'csv') {
      return this.generateCsvReport({ revenue, channels, growth });
    }

    return JSON.stringify({ revenue, channels, growth });
  }

  private async generateCustomerReport(companyId: string, from: Date, to: Date, format: 'pdf' | 'csv'): Promise<string> {
    const retention = await this.getRetentionRate(companyId, 30);
    const churn = await this.getChurnRate(companyId, 30);

    if (format === 'csv') {
      return `retention_rate,${retention}\nchurn_rate,${churn}`;
    }

    return JSON.stringify({ retention, churn });
  }

  private async generateProductReport(companyId: string, from: Date, to: Date, format: 'pdf' | 'csv'): Promise<string> {
    const topProducts = await this.getTopProducts(companyId, 20, 'revenue');

    if (format === 'csv') {
      return this.generateCsvReport(topProducts);
    }

    return JSON.stringify(topProducts);
  }

  private async generateProfitReport(companyId: string, from: Date, to: Date, format: 'pdf' | 'csv'): Promise<string> {
    const margin = await this.getProfitMargin(companyId, from, to);
    const byProduct = await this.getProfitByProduct(companyId);
    const byChannel = await this.getProfitByChannel(companyId);

    if (format === 'csv') {
      return this.generateCsvReport({ margin, byProduct, byChannel });
    }

    return JSON.stringify({ margin, byProduct, byChannel });
  }

  private generateCsvReport(data: any): string {
    if (Array.isArray(data)) {
      if (data.length === 0) return '';
      const headers = Object.keys(data[0]);
      const csv = [headers.join(','), ...data.map(row => headers.map(h => row[h]).join(','))];
      return csv.join('\n');
    }

    const entries = Object.entries(data).map(([key, value]) => `${key},${JSON.stringify(value)}`);
    return entries.join('\n');
  }
}
