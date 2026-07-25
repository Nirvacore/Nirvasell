import { Controller, Post, Get, Put, Delete, Body, Param, Query, UseGuards, BadRequestException } from '@nestjs/common';
import { MultiChannelSellingService, Channel } from '../services/multi-channel-selling.service';
import { AddChannelDto, UpdateChannelSettingsDto, ChannelEnum } from '../dtos/channel.dto';
import { SyncProductDto, UpdateProductPriceDto, UpdateProductStockDto, DistributeInventoryDto } from '../dtos/product.dto';
import { ImportOrderDto, UpdateOrderStatusDto, OrderStatusEnum } from '../dtos/order.dto';
import { Decimal } from 'decimal.js';

/**
 * Multi-Channel Selling Controller
 *
 * Handles all operations for syncing products and orders across multiple marketplace channels
 * (Shopee, Lazada, TikTok Shop). Multi-tenant: companyId is extracted from request context.
 */
@Controller('commerce/multi-channel')
export class MultiChannelSellingController {
  constructor(private readonly multiChannelService: MultiChannelSellingService) {}

  // ============ Channel Management Endpoints ============

  /**
   * Add a new marketplace channel configuration
   */
  @Post('channels')
  async addChannel(@Param('companyId') companyId: string, @Body() dto: AddChannelDto) {
    return this.multiChannelService.addChannel(
      companyId,
      dto.channel as Channel,
      {
        apiKey: dto.credentials.apiKey,
        shopId: dto.credentials.shopId,
        sellerId: dto.credentials.sellerId,
        accessToken: dto.credentials.accessToken,
        refreshToken: dto.credentials.refreshToken,
      },
      dto.settings,
    );
  }

  /**
   * Get configuration for a specific channel
   */
  @Get('channels/:channel')
  async getChannelConfig(@Param('companyId') companyId: string, @Param('channel') channel: string) {
    const validChannel = Object.values(Channel).includes(channel as Channel);
    if (!validChannel) {
      throw new BadRequestException(`Invalid channel: ${channel}`);
    }
    return this.multiChannelService.getChannelConfig(companyId, channel as Channel);
  }

  /**
   * Update channel settings
   */
  @Put('channels/:channel/settings')
  async updateChannelSettings(
    @Param('companyId') companyId: string,
    @Param('channel') channel: string,
    @Body() dto: UpdateChannelSettingsDto,
  ) {
    const validChannel = Object.values(Channel).includes(channel as Channel);
    if (!validChannel) {
      throw new BadRequestException(`Invalid channel: ${channel}`);
    }
    return this.multiChannelService.updateChannelSettings(companyId, channel as Channel, dto);
  }

  /**
   * List all active channels for the company
   */
  @Get('channels')
  async listChannels(@Param('companyId') companyId: string) {
    return this.multiChannelService.listActiveChannels(companyId);
  }

  /**
   * Deactivate a channel
   */
  @Delete('channels/:channel')
  async deactivateChannel(@Param('companyId') companyId: string, @Param('channel') channel: string) {
    const validChannel = Object.values(Channel).includes(channel as Channel);
    if (!validChannel) {
      throw new BadRequestException(`Invalid channel: ${channel}`);
    }
    await this.multiChannelService.deactivateChannel(companyId, channel as Channel);
    return { message: `Channel ${channel} deactivated` };
  }

  // ============ Product Sync Endpoints ============

  /**
   * Sync a product to a specific channel
   */
  @Post('products/sync/:channel')
  async syncProduct(
    @Param('companyId') companyId: string,
    @Param('channel') channel: string,
    @Body() dto: SyncProductDto,
  ) {
    const validChannel = Object.values(Channel).includes(channel as Channel);
    if (!validChannel) {
      throw new BadRequestException(`Invalid channel: ${channel}`);
    }
    return this.multiChannelService.syncProductToChannel(
      companyId,
      dto.productId,
      channel as Channel,
      new Decimal(dto.price),
      dto.stock,
    );
  }

  /**
   * Update product price on a channel
   */
  @Put('products/:productId/price/:channel')
  async updateProductPrice(
    @Param('companyId') companyId: string,
    @Param('productId') productId: string,
    @Param('channel') channel: string,
    @Body() dto: UpdateProductPriceDto,
  ) {
    const validChannel = Object.values(Channel).includes(channel as Channel);
    if (!validChannel) {
      throw new BadRequestException(`Invalid channel: ${channel}`);
    }
    await this.multiChannelService.updateChannelProductPrice(
      companyId,
      productId,
      channel as Channel,
      new Decimal(dto.newPrice),
    );
    return { message: 'Price updated successfully' };
  }

  /**
   * Update product stock on a channel
   */
  @Put('products/:productId/stock/:channel')
  async updateProductStock(
    @Param('companyId') companyId: string,
    @Param('productId') productId: string,
    @Param('channel') channel: string,
    @Body() dto: UpdateProductStockDto,
  ) {
    const validChannel = Object.values(Channel).includes(channel as Channel);
    if (!validChannel) {
      throw new BadRequestException(`Invalid channel: ${channel}`);
    }
    await this.multiChannelService.updateChannelProductStock(
      companyId,
      productId,
      channel as Channel,
      dto.newStock,
    );
    return { message: 'Stock updated successfully' };
  }

  /**
   * Get channel product details
   */
  @Get('products/:productId/:channel')
  async getChannelProduct(
    @Param('companyId') companyId: string,
    @Param('productId') productId: string,
    @Param('channel') channel: string,
  ) {
    const validChannel = Object.values(Channel).includes(channel as Channel);
    if (!validChannel) {
      throw new BadRequestException(`Invalid channel: ${channel}`);
    }
    return this.multiChannelService.getChannelProduct(companyId, productId, channel as Channel);
  }

  /**
   * Get all channel listings for a product
   */
  @Get('products/:productId/channels')
  async getProductChannels(@Param('companyId') companyId: string, @Param('productId') productId: string) {
    return this.multiChannelService.getChannelProductsByProduct(companyId, productId);
  }

  // ============ Inventory Management Endpoints ============

  /**
   * Get channel inventory with pagination
   */
  @Get('inventory/:channel')
  async getChannelInventory(
    @Param('companyId') companyId: string,
    @Param('channel') channel: string,
    @Query('limit') limit = 50,
    @Query('offset') offset = 0,
  ) {
    const validChannel = Object.values(Channel).includes(channel as Channel);
    if (!validChannel) {
      throw new BadRequestException(`Invalid channel: ${channel}`);
    }
    return this.multiChannelService.getChannelInventory(companyId, channel as Channel, limit, offset);
  }

  /**
   * Distribute total stock across all active channels proportionally
   */
  @Post('inventory/distribute')
  async distributeInventory(@Param('companyId') companyId: string, @Body() dto: DistributeInventoryDto) {
    await this.multiChannelService.syncInventoryToAllChannels(companyId, dto.productId, dto.totalStock);
    return { message: 'Inventory distributed to all channels' };
  }

  /**
   * Get inventory stats for all channels
   */
  @Get('inventory')
  async getAllInventory(@Param('companyId') companyId: string) {
    return this.multiChannelService.getAllChannelInventory(companyId);
  }

  // ============ Order Sync Endpoints ============

  /**
   * Import order from a marketplace channel
   */
  @Post('orders/import/:channel')
  async importOrder(
    @Param('companyId') companyId: string,
    @Param('channel') channel: string,
    @Body() dto: ImportOrderDto,
  ) {
    const validChannel = Object.values(Channel).includes(channel as Channel);
    if (!validChannel) {
      throw new BadRequestException(`Invalid channel: ${channel}`);
    }
    return this.multiChannelService.importOrderFromChannel(companyId, channel as Channel, dto.externalOrderId, {
      externalOrderId: dto.externalOrderId,
      buyerName: dto.buyerName,
      buyerPhone: dto.buyerPhone,
      deliveryAddress: dto.deliveryAddress,
      items: dto.items.map(item => ({
        externalProductId: item.externalProductId,
        quantity: item.quantity,
        price: new Decimal(item.price),
      })),
      totalPrice: new Decimal(dto.totalPrice),
      orderDate: new Date(dto.orderDate),
      status: dto.status as any,
    });
  }

  /**
   * Get orders from a specific channel with pagination
   */
  @Get('orders/:channel')
  async getChannelOrders(
    @Param('companyId') companyId: string,
    @Param('channel') channel: string,
    @Query('limit') limit = 50,
    @Query('offset') offset = 0,
  ) {
    const validChannel = Object.values(Channel).includes(channel as Channel);
    if (!validChannel) {
      throw new BadRequestException(`Invalid channel: ${channel}`);
    }
    return this.multiChannelService.getChannelOrders(companyId, channel as Channel, limit, offset);
  }

  /**
   * Update order status on a channel
   */
  @Put('orders/:orderId/status/:channel')
  async updateOrderStatus(
    @Param('companyId') companyId: string,
    @Param('orderId') orderId: string,
    @Param('channel') channel: string,
    @Body() dto: UpdateOrderStatusDto,
  ) {
    const validChannel = Object.values(Channel).includes(channel as Channel);
    if (!validChannel) {
      throw new BadRequestException(`Invalid channel: ${channel}`);
    }
    const validStatus = Object.values(OrderStatusEnum).includes(dto.status);
    if (!validStatus) {
      throw new BadRequestException(`Invalid status: ${dto.status}`);
    }
    await this.multiChannelService.updateChannelOrderStatus(companyId, orderId, channel as Channel, dto.status);
    return { message: 'Order status updated successfully' };
  }

  /**
   * Get orders by status on a channel
   */
  @Get('orders/:channel/status/:status')
  async getOrdersByStatus(
    @Param('companyId') companyId: string,
    @Param('channel') channel: string,
    @Param('status') status: string,
  ) {
    const validChannel = Object.values(Channel).includes(channel as Channel);
    if (!validChannel) {
      throw new BadRequestException(`Invalid channel: ${channel}`);
    }
    return this.multiChannelService.getOrdersByStatus(companyId, channel as Channel, status);
  }

  // ============ Pricing Strategy Endpoints ============

  /**
   * Get pricing tiers for all configured channels
   */
  @Get('pricing/tiers')
  async getPricingTiers(@Param('companyId') companyId: string) {
    return this.multiChannelService.getChannelPricingTiers(companyId);
  }

  /**
   * Set price rules for a specific channel
   */
  @Post('pricing/rules/:channel')
  async setPriceRules(
    @Param('companyId') companyId: string,
    @Param('channel') channel: string,
    @Body() rules: any,
  ) {
    const validChannel = Object.values(Channel).includes(channel as Channel);
    if (!validChannel) {
      throw new BadRequestException(`Invalid channel: ${channel}`);
    }
    await this.multiChannelService.setPriceRuleByChannel(companyId, channel as Channel, {
      minPrice: rules.minPrice ? new Decimal(rules.minPrice) : undefined,
      maxPrice: rules.maxPrice ? new Decimal(rules.maxPrice) : undefined,
      costMultiplier: rules.costMultiplier ? new Decimal(rules.costMultiplier) : undefined,
      fixedMarkup: rules.fixedMarkup ? new Decimal(rules.fixedMarkup) : undefined,
      discountPercentage: rules.discountPercentage ? new Decimal(rules.discountPercentage) : undefined,
    });
    return { message: 'Price rules updated successfully' };
  }

  /**
   * Calculate price for a product on a specific channel
   */
  @Get('pricing/calculate/:channel')
  async calculatePrice(
    @Param('companyId') companyId: string,
    @Param('channel') channel: string,
    @Query('baseCost') baseCost: string,
  ) {
    const validChannel = Object.values(Channel).includes(channel as Channel);
    if (!validChannel) {
      throw new BadRequestException(`Invalid channel: ${channel}`);
    }
    const price = await this.multiChannelService.calculateChannelPrice(
      companyId,
      channel as Channel,
      new Decimal(baseCost),
    );
    return { channel, baseCost, calculatedPrice: price.toString() };
  }

  // ============ Analytics Endpoints ============

  /**
   * Get multi-channel statistics and performance metrics
   */
  @Get('stats')
  async getMultiChannelStats(@Param('companyId') companyId: string) {
    return this.multiChannelService.getMultiChannelStats(companyId);
  }
}
