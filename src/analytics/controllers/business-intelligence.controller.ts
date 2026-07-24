import { Controller, Get, Post, Body, Param, Query, BadRequestException, UseGuards } from '@nestjs/common';
import { BusinessIntelligenceService } from '../services/business-intelligence.service';
import { Decimal } from 'decimal.js';

@Controller('analytics/business-intelligence')
export class BusinessIntelligenceController {
  constructor(private readonly biService: BusinessIntelligenceService) {}

  /**
   * Endpoint 1: Get sales revenue for a specific period
   * Supports day/week/month grouping
   */
  @Get('sales/revenue')
  async getSalesRevenue(
    @Query('companyId') companyId: string,
    @Query('from') from: string,
    @Query('to') to: string,
    @Query('groupBy') groupBy: 'day' | 'week' | 'month' = 'day',
  ) {
    if (!companyId || !from || !to) {
      throw new BadRequestException('companyId, from, and to are required');
    }

    const fromDate = new Date(from);
    const toDate = new Date(to);

    const data = await this.biService.getSalesRevenue(companyId, fromDate, toDate, groupBy);

    return {
      success: true,
      data,
      count: data.length,
      period: { from: fromDate, to: toDate, groupBy },
    };
  }

  /**
   * Endpoint 2: Get sales growth metrics for a period
   * Compares current period vs previous period
   */
  @Get('sales/growth')
  async getSalesGrowth(
    @Query('companyId') companyId: string,
    @Query('period') period: 'week' | 'month' | 'quarter' | 'year' = 'month',
  ) {
    if (!companyId) {
      throw new BadRequestException('companyId is required');
    }

    const growth = await this.biService.getSalesGrowth(companyId, period);

    return {
      success: true,
      data: growth,
      period,
    };
  }

  /**
   * Endpoint 3: Get revenue breakdown by sales channel
   */
  @Get('sales/by-channel')
  async getRevenueByChannel(
    @Query('companyId') companyId: string,
    @Query('from') from: string,
    @Query('to') to: string,
  ) {
    if (!companyId || !from || !to) {
      throw new BadRequestException('companyId, from, and to are required');
    }

    const channels = await this.biService.getRevenueByChannel(companyId, new Date(from), new Date(to));

    return {
      success: true,
      data: channels,
      total: channels.reduce((sum, c) => sum.plus(c.revenue), new Decimal(0)),
      channelCount: channels.length,
    };
  }

  /**
   * Endpoint 4: Get customer analytics (LTV, retention, churn)
   */
  @Get('customers/analytics')
  async getCustomerAnalytics(
    @Query('companyId') companyId: string,
    @Query('days') days: string = '30',
  ) {
    if (!companyId) {
      throw new BadRequestException('companyId is required');
    }

    const daysNum = parseInt(days);
    const retention = await this.biService.getRetentionRate(companyId, daysNum);
    const churn = await this.biService.getChurnRate(companyId, daysNum);

    return {
      success: true,
      data: {
        retentionRate: retention,
        churnRate: churn,
        analysisPeriodDays: daysNum,
      },
    };
  }

  /**
   * Endpoint 5: Get top performing products
   * Supports sorting by revenue, quantity, or profit
   */
  @Get('products/top')
  async getTopProducts(
    @Query('companyId') companyId: string,
    @Query('limit') limit: string = '10',
    @Query('sortBy') sortBy: 'revenue' | 'quantity' | 'profit' = 'revenue',
  ) {
    if (!companyId) {
      throw new BadRequestException('companyId is required');
    }

    const limitNum = Math.min(parseInt(limit) || 10, 1000);
    const products = await this.biService.getTopProducts(companyId, limitNum, sortBy);

    return {
      success: true,
      data: products,
      count: products.length,
      sortedBy: sortBy,
    };
  }

  /**
   * Endpoint 6: Get profitability metrics
   * Includes margin, costs, and profit analysis
   */
  @Get('profitability/metrics')
  async getProfitabilityMetrics(
    @Query('companyId') companyId: string,
    @Query('from') from: string,
    @Query('to') to: string,
  ) {
    if (!companyId || !from || !to) {
      throw new BadRequestException('companyId, from, and to are required');
    }

    const fromDate = new Date(from);
    const toDate = new Date(to);

    const margin = await this.biService.getProfitMargin(companyId, fromDate, toDate);
    const byProduct = await this.biService.getProfitByProduct(companyId);
    const byChannel = await this.biService.getProfitByChannel(companyId);

    return {
      success: true,
      data: {
        overallMargin: margin,
        byProduct,
        byChannel,
      },
      period: { from: fromDate, to: toDate },
    };
  }

  /**
   * Endpoint 7: Get slow-moving products
   * Identifies inventory that hasn't sold recently
   */
  @Get('products/slow-movers')
  async getSlowMovers(
    @Query('companyId') companyId: string,
    @Query('threshold') threshold: string = '90',
  ) {
    if (!companyId) {
      throw new BadRequestException('companyId is required');
    }

    const thresholdDays = parseInt(threshold);
    const slowMovers = await this.biService.getSlowMovers(companyId, thresholdDays);

    return {
      success: true,
      data: slowMovers,
      count: slowMovers.length,
      thresholdDays,
    };
  }

  /**
   * Endpoint 8: List and get dashboard data
   */
  @Get('dashboards/list')
  async listDashboards(@Query('companyId') companyId: string) {
    if (!companyId) {
      throw new BadRequestException('companyId is required');
    }

    const dashboards = await this.biService.listDashboards(companyId);

    return {
      success: true,
      data: dashboards,
      count: dashboards.length,
    };
  }

  /**
   * Endpoint 9: Create a custom dashboard with configurable KPIs
   */
  @Post('dashboards/create')
  async createDashboard(
    @Body()
    createDashboardDto: {
      companyId: string;
      name: string;
      kpis: Array<{
        key: string;
        label: string;
        type: string;
        params?: Record<string, any>;
      }>;
    },
  ) {
    if (!createDashboardDto.companyId || !createDashboardDto.name || !createDashboardDto.kpis) {
      throw new BadRequestException('companyId, name, and kpis are required');
    }

    const dashboard = await this.biService.createDashboard(
      createDashboardDto.companyId,
      createDashboardDto.name,
      createDashboardDto.kpis,
    );

    return {
      success: true,
      data: dashboard,
      message: 'Dashboard created successfully',
    };
  }

  /**
   * Endpoint 10: Generate reports in PDF or CSV format
   * Supports sales, customer, product, and profitability reports
   */
  @Post('reports/generate')
  async generateReport(
    @Body()
    generateReportDto: {
      companyId: string;
      type: 'sales' | 'customer' | 'product' | 'profit';
      format: 'pdf' | 'csv';
      from?: string;
      to?: string;
    },
  ) {
    if (!generateReportDto.companyId || !generateReportDto.type || !generateReportDto.format) {
      throw new BadRequestException('companyId, type, and format are required');
    }

    const fromDate = generateReportDto.from ? new Date(generateReportDto.from) : undefined;
    const toDate = generateReportDto.to ? new Date(generateReportDto.to) : undefined;

    const report = await this.biService.generateReport(
      generateReportDto.companyId,
      generateReportDto.type,
      generateReportDto.format,
      fromDate,
      toDate,
    );

    return {
      success: true,
      data: {
        reportId: report.id,
        type: report.type,
        format: report.format,
        fileSize: report.fileSize,
        generatedAt: report.generatedAt,
      },
      content: report.content,
    };
  }

  /**
   * Bonus Endpoint: Get break-even analysis
   * Useful for profitability planning
   */
  @Get('profitability/break-even')
  async getBreakEvenAnalysis(@Query('companyId') companyId: string) {
    if (!companyId) {
      throw new BadRequestException('companyId is required');
    }

    const analysis = await this.biService.getBreakEvenAnalysis(companyId);

    return {
      success: true,
      data: analysis,
    };
  }

  /**
   * Bonus Endpoint: Get customer lifetime value
   */
  @Get('customers/:customerId/ltv')
  async getCustomerLTV(
    @Query('companyId') companyId: string,
    @Param('customerId') customerId: string,
  ) {
    if (!companyId || !customerId) {
      throw new BadRequestException('companyId and customerId are required');
    }

    const ltv = await this.biService.getCustomerLifetimeValue(companyId, customerId);

    return {
      success: true,
      data: {
        customerId,
        lifetimeValue: ltv,
      },
    };
  }

  /**
   * Bonus Endpoint: Get dashboard with calculated KPIs
   */
  @Get('dashboards/:dashboardId/data')
  async getDashboardData(
    @Query('companyId') companyId: string,
    @Param('dashboardId') dashboardId: string,
  ) {
    if (!companyId || !dashboardId) {
      throw new BadRequestException('companyId and dashboardId are required');
    }

    const dashboardData = await this.biService.getDashboardData(companyId, dashboardId);

    return {
      success: true,
      data: dashboardData,
    };
  }
}
