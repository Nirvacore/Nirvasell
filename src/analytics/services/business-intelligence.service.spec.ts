import { Test, TestingModule } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Decimal } from 'decimal.js';
import { BusinessIntelligenceService } from './business-intelligence.service';
import { SalesAnalytics } from '../entities/sales-analytics.entity';
import { CustomerAnalytics } from '../entities/customer-analytics.entity';
import { ProductAnalytics } from '../entities/product-analytics.entity';
import { ProfitabilityAnalytics } from '../entities/profitability-analytics.entity';
import { Dashboard } from '../entities/dashboard.entity';
import { BadRequestException, NotFoundException } from '@nestjs/common';

describe('BusinessIntelligenceService', () => {
  let service: BusinessIntelligenceService;
  let salesAnalyticsRepo: Repository<SalesAnalytics>;
  let customerAnalyticsRepo: Repository<CustomerAnalytics>;
  let productAnalyticsRepo: Repository<ProductAnalytics>;
  let profitabilityAnalyticsRepo: Repository<ProfitabilityAnalytics>;
  let dashboardRepo: Repository<Dashboard>;

  const mockCompanyId = 'company-123';
  const mockCustomerId = 'customer-456';
  const mockProductId = 'product-789';

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        BusinessIntelligenceService,
        {
          provide: getRepositoryToken(SalesAnalytics),
          useValue: {
            find: jest.fn(),
            findOne: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
          },
        },
        {
          provide: getRepositoryToken(CustomerAnalytics),
          useValue: {
            find: jest.fn(),
            findOne: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
          },
        },
        {
          provide: getRepositoryToken(ProductAnalytics),
          useValue: {
            find: jest.fn(),
            findOne: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
          },
        },
        {
          provide: getRepositoryToken(ProfitabilityAnalytics),
          useValue: {
            find: jest.fn(),
            findOne: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
          },
        },
        {
          provide: getRepositoryToken(Dashboard),
          useValue: {
            find: jest.fn(),
            findOne: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
          },
        },
      ],
    }).compile();

    service = module.get<BusinessIntelligenceService>(BusinessIntelligenceService);
    salesAnalyticsRepo = module.get<Repository<SalesAnalytics>>(getRepositoryToken(SalesAnalytics));
    customerAnalyticsRepo = module.get<Repository<CustomerAnalytics>>(getRepositoryToken(CustomerAnalytics));
    productAnalyticsRepo = module.get<Repository<ProductAnalytics>>(getRepositoryToken(ProductAnalytics));
    profitabilityAnalyticsRepo = module.get<Repository<ProfitabilityAnalytics>>(getRepositoryToken(ProfitabilityAnalytics));
    dashboardRepo = module.get<Repository<Dashboard>>(getRepositoryToken(Dashboard));
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Sales Analytics', () => {
    describe('getSalesRevenue', () => {
      it('should retrieve sales revenue by day', async () => {
        const now = new Date();
        const mockAnalytics = [
          {
            dateStart: now,
            dateEnd: now,
            totalRevenue: new Decimal('1000'),
            orderCount: 10,
            customerCount: 8,
            averageOrderValue: new Decimal('100'),
            companyId: mockCompanyId,
          } as any,
        ];

        jest.spyOn(salesAnalyticsRepo, 'find').mockResolvedValue(mockAnalytics);

        const result = await service.getSalesRevenue(mockCompanyId, now, new Date(now.getTime() + 86400000), 'day');

        expect(result).toHaveLength(1);
        expect(result[0].revenue.toString()).toBe('1000');
      });

      it('should throw error if from date is after to date', async () => {
        const now = new Date();
        const tomorrow = new Date(now.getTime() + 86400000);

        await expect(service.getSalesRevenue(mockCompanyId, tomorrow, now, 'day')).rejects.toThrow(BadRequestException);
      });

      it('should support weekly grouping', async () => {
        const now = new Date();
        jest.spyOn(salesAnalyticsRepo, 'find').mockResolvedValue([]);

        await service.getSalesRevenue(mockCompanyId, now, new Date(now.getTime() + 604800000), 'week');

        expect(salesAnalyticsRepo.find).toHaveBeenCalled();
      });

      it('should support monthly grouping', async () => {
        const now = new Date();
        jest.spyOn(salesAnalyticsRepo, 'find').mockResolvedValue([]);

        await service.getSalesRevenue(mockCompanyId, now, new Date(now.getTime() + 2592000000), 'month');

        expect(salesAnalyticsRepo.find).toHaveBeenCalled();
      });
    });

    describe('getSalesGrowth', () => {
      it('should calculate monthly sales growth', async () => {
        const mockCurrentData = [
          {
            totalRevenue: new Decimal('5000'),
            orderCount: 50,
            customerCount: 40,
          } as any,
        ];
        const mockPreviousData = [
          {
            totalRevenue: new Decimal('4000'),
            orderCount: 40,
            customerCount: 35,
          } as any,
        ];

        jest.spyOn(salesAnalyticsRepo, 'find').mockResolvedValueOnce(mockCurrentData).mockResolvedValueOnce(mockPreviousData);

        const result = await service.getSalesGrowth(mockCompanyId, 'month');

        expect(result.current.toString()).toBe('5000');
        expect(result.previous.toString()).toBe('4000');
        expect(result.growth.toString()).toBe('1000');
      });

      it('should handle zero previous revenue for growth calculation', async () => {
        jest.spyOn(salesAnalyticsRepo, 'find').mockResolvedValueOnce([{ totalRevenue: new Decimal('1000') } as any]).mockResolvedValueOnce([]);

        const result = await service.getSalesGrowth(mockCompanyId, 'week');

        expect(result.growthPercentage.toString()).toBe('0');
      });

      it('should support quarterly growth analysis', async () => {
        jest.spyOn(salesAnalyticsRepo, 'find').mockResolvedValue([]);

        await service.getSalesGrowth(mockCompanyId, 'quarter');

        expect(salesAnalyticsRepo.find).toHaveBeenCalled();
      });

      it('should support yearly growth analysis', async () => {
        jest.spyOn(salesAnalyticsRepo, 'find').mockResolvedValue([]);

        await service.getSalesGrowth(mockCompanyId, 'year');

        expect(salesAnalyticsRepo.find).toHaveBeenCalled();
      });
    });

    describe('getRevenueByChannel', () => {
      it('should retrieve revenue breakdown by channel', async () => {
        const now = new Date();
        const mockAnalytics = [
          {
            channel: 'shopee',
            totalRevenue: new Decimal('3000'),
            orderCount: 30,
            dateStart: now,
            dateEnd: now,
          } as any,
          {
            channel: 'lazada',
            totalRevenue: new Decimal('2000'),
            orderCount: 20,
            dateStart: now,
            dateEnd: now,
          } as any,
        ];

        jest.spyOn(salesAnalyticsRepo, 'find').mockResolvedValue(mockAnalytics);

        const result = await service.getRevenueByChannel(mockCompanyId, now, new Date(now.getTime() + 86400000));

        expect(result).toHaveLength(2);
        expect(result[0].channel).toBe('shopee');
        expect(result[0].revenue.toString()).toBe('3000');
      });

      it('should calculate percentage contribution correctly', async () => {
        const now = new Date();
        const mockAnalytics = [
          {
            channel: 'shopee',
            totalRevenue: new Decimal('5000'),
            orderCount: 50,
            dateStart: now,
            dateEnd: now,
          } as any,
          {
            channel: 'lazada',
            totalRevenue: new Decimal('5000'),
            orderCount: 50,
            dateStart: now,
            dateEnd: now,
          } as any,
        ];

        jest.spyOn(salesAnalyticsRepo, 'find').mockResolvedValue(mockAnalytics);

        const result = await service.getRevenueByChannel(mockCompanyId, now, new Date(now.getTime() + 86400000));

        expect(result[0].percentage.toString()).toBe('50');
      });
    });

    describe('getAverageOrderValue', () => {
      it('should calculate average order value', async () => {
        const now = new Date();
        const mockAnalytics = [
          {
            totalRevenue: new Decimal('1000'),
            orderCount: 10,
            dateStart: now,
            dateEnd: now,
          } as any,
        ];

        jest.spyOn(salesAnalyticsRepo, 'find').mockResolvedValue(mockAnalytics);

        const result = await service.getAverageOrderValue(mockCompanyId, now, new Date(now.getTime() + 86400000));

        expect(result.toString()).toBe('100');
      });

      it('should handle zero orders', async () => {
        const now = new Date();
        jest.spyOn(salesAnalyticsRepo, 'find').mockResolvedValue([]);

        const result = await service.getAverageOrderValue(mockCompanyId, now, new Date(now.getTime() + 86400000));

        expect(result.toString()).toBe('0');
      });
    });
  });

  describe('Customer Analytics', () => {
    describe('getCustomerLifetimeValue', () => {
      it('should retrieve customer lifetime value', async () => {
        const mockAnalytics = {
          customerId: mockCustomerId,
          lifetimeValue: new Decimal('5000'),
          companyId: mockCompanyId,
        } as any;

        jest.spyOn(customerAnalyticsRepo, 'findOne').mockResolvedValue(mockAnalytics);

        const result = await service.getCustomerLifetimeValue(mockCompanyId, mockCustomerId);

        expect(result.toString()).toBe('5000');
      });

      it('should throw error if customer not found', async () => {
        jest.spyOn(customerAnalyticsRepo, 'findOne').mockResolvedValue(null);

        await expect(service.getCustomerLifetimeValue(mockCompanyId, mockCustomerId)).rejects.toThrow(NotFoundException);
      });
    });

    describe('getRetentionRate', () => {
      it('should calculate retention rate', async () => {
        const mockAnalytics = [
          {
            retentionRate: new Decimal('80'),
            companyId: mockCompanyId,
          } as any,
          {
            retentionRate: new Decimal('75'),
            companyId: mockCompanyId,
          } as any,
        ];

        jest.spyOn(customerAnalyticsRepo, 'find').mockResolvedValue(mockAnalytics);

        const result = await service.getRetentionRate(mockCompanyId, 30);

        expect(result).toBe(100);
      });

      it('should throw error for invalid days', async () => {
        await expect(service.getRetentionRate(mockCompanyId, -5)).rejects.toThrow(BadRequestException);
      });

      it('should return 0 for no data', async () => {
        jest.spyOn(customerAnalyticsRepo, 'find').mockResolvedValue([]);

        const result = await service.getRetentionRate(mockCompanyId, 30);

        expect(result).toBe(0);
      });
    });

    describe('getChurnRate', () => {
      it('should calculate churn rate', async () => {
        jest.spyOn(customerAnalyticsRepo, 'find').mockResolvedValue([{ retentionRate: new Decimal('80') } as any]);

        const result = await service.getChurnRate(mockCompanyId, 30);

        expect(result).toBeLessThanOrEqual(100);
        expect(result).toBeGreaterThanOrEqual(0);
      });

      it('should be inverse of retention rate', async () => {
        const mockAnalytics = [{ retentionRate: new Decimal('70') } as any];
        jest.spyOn(customerAnalyticsRepo, 'find').mockResolvedValue(mockAnalytics);

        const retention = await service.getRetentionRate(mockCompanyId, 30);
        const churn = await service.getChurnRate(mockCompanyId, 30);

        expect(retention + churn).toBe(100);
      });
    });

    describe('getCustomerCohort', () => {
      it('should retrieve cohort data', async () => {
        const mockAnalytics = [
          {
            cohortMonth: '2024-01',
            lifetimeValue: new Decimal('5000'),
            repeatPurchases: 2,
            retentionRate: new Decimal('80'),
          } as any,
        ];

        jest.spyOn(customerAnalyticsRepo, 'find').mockResolvedValue(mockAnalytics);

        const result = await service.getCustomerCohort(mockCompanyId, '2024-01');

        expect(result.month).toBe('2024-01');
        expect(result.startingCustomers).toBe(1);
      });

      it('should throw error if no cohort data found', async () => {
        jest.spyOn(customerAnalyticsRepo, 'find').mockResolvedValue([]);

        await expect(service.getCustomerCohort(mockCompanyId, '2024-01')).rejects.toThrow(NotFoundException);
      });
    });
  });

  describe('Product Performance', () => {
    describe('getTopProducts', () => {
      it('should retrieve top products by revenue', async () => {
        const mockProducts = [
          {
            productId: 'prod-1',
            productName: 'Product 1',
            totalRevenue: new Decimal('10000'),
            unitsSold: 100,
            totalProfit: new Decimal('3000'),
            profitMargin: new Decimal('30'),
            revenueContribution: new Decimal('50'),
          } as any,
        ];

        jest.spyOn(productAnalyticsRepo, 'find').mockResolvedValue(mockProducts);

        const result = await service.getTopProducts(mockCompanyId, 10, 'revenue');

        expect(result).toHaveLength(1);
        expect(result[0].productName).toBe('Product 1');
      });

      it('should support top products by quantity', async () => {
        jest.spyOn(productAnalyticsRepo, 'find').mockResolvedValue([]);

        await service.getTopProducts(mockCompanyId, 10, 'quantity');

        expect(productAnalyticsRepo.find).toHaveBeenCalled();
      });

      it('should support top products by profit', async () => {
        jest.spyOn(productAnalyticsRepo, 'find').mockResolvedValue([]);

        await service.getTopProducts(mockCompanyId, 10, 'profit');

        expect(productAnalyticsRepo.find).toHaveBeenCalled();
      });

      it('should throw error for invalid limit', async () => {
        await expect(service.getTopProducts(mockCompanyId, -5)).rejects.toThrow(BadRequestException);
      });

      it('should enforce maximum limit', async () => {
        await expect(service.getTopProducts(mockCompanyId, 2000)).rejects.toThrow(BadRequestException);
      });
    });

    describe('getProductMetrics', () => {
      it('should retrieve product metrics', async () => {
        const mockProduct = {
          productId: mockProductId,
          productName: 'Test Product',
          totalRevenue: new Decimal('5000'),
          unitsSold: 50,
          totalProfit: new Decimal('1500'),
          profitMargin: new Decimal('30'),
          revenueContribution: new Decimal('25'),
          daysSinceLastSale: 10,
        } as any;

        jest.spyOn(productAnalyticsRepo, 'findOne').mockResolvedValue(mockProduct);

        const result = await service.getProductMetrics(mockCompanyId, mockProductId);

        expect(result.productName).toBe('Test Product');
        expect(result.revenue.toString()).toBe('5000');
      });

      it('should throw error if product not found', async () => {
        jest.spyOn(productAnalyticsRepo, 'findOne').mockResolvedValue(null);

        await expect(service.getProductMetrics(mockCompanyId, mockProductId)).rejects.toThrow(NotFoundException);
      });
    });

    describe('getSlowMovers', () => {
      it('should identify slow moving products', async () => {
        const mockProducts = [
          {
            productId: 'prod-1',
            productName: 'Slow Product',
            daysSinceLastSale: 120,
            totalRevenue: new Decimal('1000'),
            unitsSold: 10,
            totalProfit: new Decimal('300'),
            profitMargin: new Decimal('30'),
            revenueContribution: new Decimal('5'),
          } as any,
        ];

        jest.spyOn(productAnalyticsRepo, 'find').mockResolvedValue(mockProducts);

        const result = await service.getSlowMovers(mockCompanyId, 90);

        expect(result).toHaveLength(1);
        expect(result[0].daysInStock).toBe(120);
      });

      it('should throw error for invalid threshold', async () => {
        await expect(service.getSlowMovers(mockCompanyId, -10)).rejects.toThrow(BadRequestException);
      });

      it('should enforce maximum threshold', async () => {
        await expect(service.getSlowMovers(mockCompanyId, 400)).rejects.toThrow(BadRequestException);
      });
    });

    describe('getRevenueContribution', () => {
      it('should calculate revenue contribution by product', async () => {
        const mockProducts = [
          {
            productId: 'prod-1',
            revenueContribution: new Decimal('50'),
          } as any,
          {
            productId: 'prod-2',
            revenueContribution: new Decimal('30'),
          } as any,
        ];

        jest.spyOn(productAnalyticsRepo, 'find').mockResolvedValue(mockProducts);

        const result = await service.getRevenueContribution(mockCompanyId);

        expect(result).toHaveLength(2);
        expect(result[0].contribution.toString()).toBe('50');
      });
    });
  });

  describe('Profitability Analysis', () => {
    describe('getProfitMargin', () => {
      it('should calculate profit margin', async () => {
        const now = new Date();
        const mockAnalytics = [
          {
            revenue: new Decimal('10000'),
            netProfit: new Decimal('2000'),
            dateStart: now,
            dateEnd: now,
          } as any,
        ];

        jest.spyOn(profitabilityAnalyticsRepo, 'find').mockResolvedValue(mockAnalytics);

        const result = await service.getProfitMargin(mockCompanyId, now, new Date(now.getTime() + 86400000));

        expect(result.toString()).toBe('20');
      });

      it('should return 0 for no data', async () => {
        const now = new Date();
        jest.spyOn(profitabilityAnalyticsRepo, 'find').mockResolvedValue([]);

        const result = await service.getProfitMargin(mockCompanyId, now, new Date(now.getTime() + 86400000));

        expect(result.toString()).toBe('0');
      });
    });

    describe('getProfitByProduct', () => {
      it('should retrieve profit breakdown by product', async () => {
        const mockProducts = [
          {
            productId: 'prod-1',
            totalProfit: new Decimal('5000'),
            profitMargin: new Decimal('25'),
          } as any,
        ];

        jest.spyOn(productAnalyticsRepo, 'find').mockResolvedValue(mockProducts);

        const result = await service.getProfitByProduct(mockCompanyId);

        expect(result).toHaveLength(1);
        expect(result[0].profit.toString()).toBe('5000');
      });
    });

    describe('getProfitByChannel', () => {
      it('should retrieve profit breakdown by channel', async () => {
        const mockAnalytics = [
          {
            channel: 'shopee',
            netProfit: new Decimal('3000'),
          } as any,
          {
            channel: 'lazada',
            netProfit: new Decimal('2000'),
          } as any,
        ];

        jest.spyOn(profitabilityAnalyticsRepo, 'find').mockResolvedValue(mockAnalytics);

        const result = await service.getProfitByChannel(mockCompanyId);

        expect(result).toHaveLength(2);
        expect(result[0].channel).toBe('shopee');
      });
    });

    describe('getBreakEvenAnalysis', () => {
      it('should calculate break even point', async () => {
        const mockAnalytics = [
          {
            revenue: new Decimal('10000'),
            costOfGoodsSold: new Decimal('6000'),
            operatingExpenses: new Decimal('2000'),
          } as any,
        ];

        jest.spyOn(profitabilityAnalyticsRepo, 'find').mockResolvedValue(mockAnalytics);

        const result = await service.getBreakEvenAnalysis(mockCompanyId);

        expect(result.breakEvenUnits).toBeGreaterThan(0);
        expect(result.fixedCosts.toString()).toBe('2000');
      });

      it('should throw error if no data found', async () => {
        jest.spyOn(profitabilityAnalyticsRepo, 'find').mockResolvedValue([]);

        await expect(service.getBreakEvenAnalysis(mockCompanyId)).rejects.toThrow(NotFoundException);
      });
    });
  });

  describe('Custom Dashboards', () => {
    describe('createDashboard', () => {
      it('should create a new dashboard', async () => {
        const kpis = [{ key: 'revenue', label: 'Total Revenue', type: 'revenue' }];
        const mockDashboard = {
          id: 'dash-1',
          companyId: mockCompanyId,
          name: 'Sales Dashboard',
          kpis,
          isActive: true,
        } as any;

        jest.spyOn(dashboardRepo, 'create').mockReturnValue(mockDashboard);
        jest.spyOn(dashboardRepo, 'save').mockResolvedValue(mockDashboard);

        const result = await service.createDashboard(mockCompanyId, 'Sales Dashboard', kpis);

        expect(result.name).toBe('Sales Dashboard');
        expect(result.kpis).toHaveLength(1);
      });

      it('should throw error for empty name', async () => {
        const kpis = [{ key: 'revenue', label: 'Total Revenue', type: 'revenue' }];

        await expect(service.createDashboard(mockCompanyId, '', kpis)).rejects.toThrow(BadRequestException);
      });

      it('should throw error for empty KPIs', async () => {
        await expect(service.createDashboard(mockCompanyId, 'Test Dashboard', [])).rejects.toThrow(BadRequestException);
      });
    });

    describe('getDashboardData', () => {
      it('should retrieve dashboard with calculated KPIs', async () => {
        const mockDashboard = {
          id: 'dash-1',
          name: 'Sales Dashboard',
          kpis: [{ key: 'revenue', label: 'Total Revenue', type: 'revenue' }],
          companyId: mockCompanyId,
        } as any;

        jest.spyOn(dashboardRepo, 'findOne').mockResolvedValue(mockDashboard);
        jest.spyOn(dashboardRepo, 'save').mockResolvedValue(mockDashboard);
        jest.spyOn(salesAnalyticsRepo, 'find').mockResolvedValue([]);

        const result = await service.getDashboardData(mockCompanyId, 'dash-1');

        expect(result.dashboardId).toBe('dash-1');
        expect(result.name).toBe('Sales Dashboard');
      });

      it('should throw error if dashboard not found', async () => {
        jest.spyOn(dashboardRepo, 'findOne').mockResolvedValue(null);

        await expect(service.getDashboardData(mockCompanyId, 'invalid-dash')).rejects.toThrow(NotFoundException);
      });
    });

    describe('listDashboards', () => {
      it('should list all active dashboards', async () => {
        const mockDashboards = [
          { id: 'dash-1', name: 'Sales Dashboard', isActive: true } as any,
          { id: 'dash-2', name: 'Customer Dashboard', isActive: true } as any,
        ];

        jest.spyOn(dashboardRepo, 'find').mockResolvedValue(mockDashboards);

        const result = await service.listDashboards(mockCompanyId);

        expect(result).toHaveLength(2);
      });
    });
  });

  describe('Report Generation', () => {
    describe('generateReport', () => {
      it('should generate sales report in CSV format', async () => {
        jest.spyOn(salesAnalyticsRepo, 'find').mockResolvedValue([]);

        const result = await service.generateReport(mockCompanyId, 'sales', 'csv');

        expect(result.type).toBe('sales');
        expect(result.format).toBe('csv');
        expect(result.content).toBeDefined();
      });

      it('should generate customer report', async () => {
        jest.spyOn(customerAnalyticsRepo, 'find').mockResolvedValue([]);

        const result = await service.generateReport(mockCompanyId, 'customer', 'csv');

        expect(result.type).toBe('customer');
      });

      it('should generate product report', async () => {
        jest.spyOn(productAnalyticsRepo, 'find').mockResolvedValue([]);

        const result = await service.generateReport(mockCompanyId, 'product', 'csv');

        expect(result.type).toBe('product');
      });

      it('should generate profit report', async () => {
        jest.spyOn(profitabilityAnalyticsRepo, 'find').mockResolvedValue([]);

        const result = await service.generateReport(mockCompanyId, 'profit', 'csv');

        expect(result.type).toBe('profit');
      });

      it('should support PDF format', async () => {
        jest.spyOn(salesAnalyticsRepo, 'find').mockResolvedValue([]);

        const result = await service.generateReport(mockCompanyId, 'sales', 'pdf');

        expect(result.format).toBe('pdf');
      });

      it('should throw error for invalid report type', async () => {
        await expect(service.generateReport(mockCompanyId, 'invalid' as any, 'csv')).rejects.toThrow(BadRequestException);
      });

      it('should use default date range', async () => {
        jest.spyOn(salesAnalyticsRepo, 'find').mockResolvedValue([]);

        const result = await service.generateReport(mockCompanyId, 'sales', 'csv');

        expect(result.generatedAt).toBeDefined();
      });
    });
  });

  describe('Multi-Tenant Isolation', () => {
    it('should isolate sales data by company', async () => {
      const company1 = 'company-1';
      const company2 = 'company-2';

      jest.spyOn(salesAnalyticsRepo, 'find').mockImplementation((options: any) => {
        if (options.where.companyId === company1) {
          return Promise.resolve([{ totalRevenue: new Decimal('5000') } as any]);
        }
        return Promise.resolve([]);
      });

      const result1 = await service.getSalesRevenue(company1, new Date(), new Date());
      const result2 = await service.getSalesRevenue(company2, new Date(), new Date());

      expect(result1.length).toBeGreaterThan(0);
      expect(result2.length).toBe(0);
    });

    it('should isolate customer data by company', async () => {
      const company1 = 'company-1';
      const company2 = 'company-2';

      jest.spyOn(customerAnalyticsRepo, 'findOne').mockImplementation((options: any) => {
        if (options.where.companyId === company1) {
          return Promise.resolve({ lifetimeValue: new Decimal('5000') } as any);
        }
        return Promise.resolve(null);
      });

      const result1 = await service.getCustomerLifetimeValue(company1, 'cust-1');
      const result2 = service.getCustomerLifetimeValue(company2, 'cust-1');

      expect(result1).toBeDefined();
      await expect(result2).rejects.toThrow();
    });

    it('should isolate product data by company', async () => {
      const company1 = 'company-1';
      const company2 = 'company-2';

      jest.spyOn(productAnalyticsRepo, 'find').mockImplementation((options: any) => {
        if (options.where.companyId === company1) {
          return Promise.resolve([{ productId: 'prod-1', revenueContribution: new Decimal('50') } as any]);
        }
        return Promise.resolve([]);
      });

      const result1 = await service.getRevenueContribution(company1);
      const result2 = await service.getRevenueContribution(company2);

      expect(result1.length).toBeGreaterThan(0);
      expect(result2.length).toBe(0);
    });
  });

  describe('Edge Cases & Error Handling', () => {
    it('should handle empty datasets gracefully', async () => {
      jest.spyOn(salesAnalyticsRepo, 'find').mockResolvedValue([]);

      const result = await service.getAverageOrderValue(mockCompanyId, new Date(), new Date());

      expect(result.toString()).toBe('0');
    });

    it('should handle large datasets', async () => {
      const largeDataset = Array(10000).fill({
        totalRevenue: new Decimal('100'),
        orderCount: 1,
        customerCount: 1,
      }) as any;

      jest.spyOn(productAnalyticsRepo, 'find').mockResolvedValue(largeDataset);

      const result = await service.getTopProducts(mockCompanyId, 100);

      expect(result.length).toBeLessThanOrEqual(100);
    });

    it('should handle precision in decimal calculations', async () => {
      const mockAnalytics = [
        {
          totalRevenue: new Decimal('1000.50'),
          orderCount: 3,
          dateStart: new Date(),
          dateEnd: new Date(),
        } as any,
      ];

      jest.spyOn(salesAnalyticsRepo, 'find').mockResolvedValue(mockAnalytics);

      const result = await service.getAverageOrderValue(mockCompanyId, new Date(), new Date());

      expect(result.toDecimalPlaces(2).toNumber()).toBeCloseTo(333.5, 1);
    });

    it('should validate date ranges consistently', async () => {
      const now = new Date();
      const past = new Date(now.getTime() - 86400000);

      jest.spyOn(salesAnalyticsRepo, 'find').mockResolvedValue([]);

      await service.getSalesRevenue(mockCompanyId, past, now);

      expect(salesAnalyticsRepo.find).toHaveBeenCalled();
    });
  });
});
