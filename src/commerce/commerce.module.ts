import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { MultiChannelSellingService } from './services/multi-channel-selling.service';
import { ChannelConfig } from './entities/channel-config.entity';
import { ChannelProduct } from './entities/channel-product.entity';
import { Order } from './entities/order.entity';
import { Product } from './entities/product.entity';

@Module({
  imports: [
    TypeOrmModule.forFeature([
      ChannelConfig,
      ChannelProduct,
      Order,
      Product,
    ]),
  ],
  providers: [MultiChannelSellingService],
  exports: [MultiChannelSellingService],
})
export class CommerceModule {}
