// Services
export { BusinessIntelligenceService } from './services/business-intelligence.service';

// Controllers
export { BusinessIntelligenceController } from './controllers/business-intelligence.controller';

// Entities
export { SalesAnalytics } from './entities/sales-analytics.entity';
export { CustomerAnalytics } from './entities/customer-analytics.entity';
export { ProductAnalytics } from './entities/product-analytics.entity';
export { ProfitabilityAnalytics } from './entities/profitability-analytics.entity';
export { Dashboard } from './entities/dashboard.entity';

// DTOs
export {
  SalesDataDto,
  ChannelRevenueDto,
  SalesGrowthDto,
  CustomerMetricsDto,
  ProductMetricsDto,
  ProfitAnalysisDto,
  CohortDataDto,
  DashboardDataDto,
  ReportDto,
  BreakEvenAnalysisDto,
} from './dtos/analytics.dto';

// Module
export { AnalyticsModule } from './analytics.module';
