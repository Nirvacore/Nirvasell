import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { BusinessIntelligenceService } from './services/business-intelligence.service';
import { BusinessIntelligenceController } from './controllers/business-intelligence.controller';
import { SalesAnalytics } from './entities/sales-analytics.entity';
import { CustomerAnalytics } from './entities/customer-analytics.entity';
import { ProductAnalytics } from './entities/product-analytics.entity';
import { ProfitabilityAnalytics } from './entities/profitability-analytics.entity';
import { Dashboard } from './entities/dashboard.entity';

@Module({
  imports: [
    TypeOrmModule.forFeature([
      SalesAnalytics,
      CustomerAnalytics,
      ProductAnalytics,
      ProfitabilityAnalytics,
      Dashboard,
    ]),
  ],
  controllers: [BusinessIntelligenceController],
  providers: [BusinessIntelligenceService],
  exports: [BusinessIntelligenceService],
})
export class AnalyticsModule {}
