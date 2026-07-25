import { Injectable, BadRequestException, NotFoundException, ConflictException, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Decimal } from 'decimal.js';
import { ChannelConfig } from '../entities/channel-config.entity';
import { ChannelProduct } from '../entities/channel-product.entity';
import { Order } from '../entities/order.entity';
import { Product } from '../entities/product.entity';

export enum Channel {
  SHOPEE = 'shopee',
  LAZADA = 'lazada',
  TIKTOK = 'tiktok',
}

export interface ChannelCredentials {
  apiKey: string;
  shopId: string;
  sellerId?: string;
  accessToken?: string;
  refreshToken?: string;
}

export interface ChannelSettings {
  enableAutoSync?: boolean;
  syncInterval?: number; // minutes
  defaultMargin?: Decimal;
  enableInventoryDistribution?: boolean;
  maxStockPerChannel?: number;
}

export interface ChannelProductData {
  externalProductId: string;
  price: Decimal;
  stock: number;
  channelSku?: string;
}

export interface OrderImportData {
  externalOrderId: string;
  buyerName: string;
  buyerPhone?: string;
  deliveryAddress: string;
  items: OrderItem[];
  totalPrice: Decimal;
  orderDate: Date;
  status: 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled';
}

export interface OrderItem {
  externalProductId: string;
  quantity: number;
  price: Decimal;
}

export interface ChannelInventoryData {
  products: ChannelProductData[];
  totalSKUs: number;
  lastSyncedAt: Date;
}

export interface PricingTier {
  channel: Channel;
  margin: Decimal;
  priceOverride?: Decimal;
}

export interface PriceRuleData {
  minPrice?: Decimal;
  maxPrice?: Decimal;
  costMultiplier?: Decimal;
  fixedMarkup?: Decimal;
  discountPercentage?: Decimal;
}

@Injectable()
export class MultiChannelSellingService {
  private readonly logger = new Logger(MultiChannelSellingService.name);
  private readonly CHANNELS = Object.values(Channel);

  constructor(
    @InjectRepository(ChannelConfig)
    private channelConfigRepo: Repository<ChannelConfig>,
    @InjectRepository(ChannelProduct)
    private channelProductRepo: Repository<ChannelProduct>,
    @InjectRepository(Order)
    private orderRepo: Repository<Order>,
    @InjectRepository(Product)
    private productRepo: Repository<Product>,
  ) {}

  // ============ Channel Management ============

  async addChannel(
    companyId: string,
    channel: Channel,
    credentials: ChannelCredentials,
    settings: ChannelSettings = {},
  ): Promise<ChannelConfig> {
    if (!this.CHANNELS.includes(channel)) {
      throw new BadRequestException(`Invalid channel: ${channel}`);
    }

    const existing = await this.channelConfigRepo.findOne({
      where: { companyId, channel },
    });

    if (existing) {
      throw new ConflictException(`Channel ${channel} already configured for this company`);
    }

    this.validateChannelCredentials(channel, credentials);

    const config = this.channelConfigRepo.create({
      companyId,
      channel,
      credentials,
      settings: {
        enableAutoSync: settings.enableAutoSync ?? true,
        syncInterval: settings.syncInterval ?? 60,
        defaultMargin: settings.defaultMargin?.toString() ?? '1.2',
        enableInventoryDistribution: settings.enableInventoryDistribution ?? true,
        maxStockPerChannel: settings.maxStockPerChannel ?? 1000,
      },
      isActive: true,
    });

    return this.channelConfigRepo.save(config);
  }

  async getChannelConfig(companyId: string, channel: Channel): Promise<ChannelConfig | null> {
    return this.channelConfigRepo.findOne({
      where: { companyId, channel },
    });
  }

  async updateChannelSettings(companyId: string, channel: Channel, settings: ChannelSettings): Promise<ChannelConfig> {
    const config = await this.getChannelConfig(companyId, channel);
    if (!config) {
      throw new NotFoundException(`Channel configuration not found for ${channel}`);
    }

    Object.assign(config.settings, {
      ...config.settings,
      ...settings,
      defaultMargin: settings.defaultMargin?.toString() ?? config.settings.defaultMargin,
    });

    return this.channelConfigRepo.save(config);
  }

  async listActiveChannels(companyId: string): Promise<ChannelConfig[]> {
    return this.channelConfigRepo.find({
      where: { companyId, isActive: true },
      order: { createdAt: 'ASC' },
    });
  }

  async deactivateChannel(companyId: string, channel: Channel): Promise<void> {
    const config = await this.getChannelConfig(companyId, channel);
    if (!config) {
      throw new NotFoundException(`Channel configuration not found`);
    }
    config.isActive = false;
    await this.channelConfigRepo.save(config);
  }

  // ============ Product Sync ============

  async syncProductToChannel(
    companyId: string,
    productId: string,
    channel: Channel,
    price: Decimal,
    stock: number,
  ): Promise<ChannelProduct> {
    const config = await this.getChannelConfig(companyId, channel);
    if (!config) {
      throw new NotFoundException(`Channel ${channel} not configured`);
    }

    const product = await this.productRepo.findOne({
      where: { id: productId, companyId },
    });
    if (!product) {
      throw new NotFoundException(`Product not found`);
    }

    if (stock < 0) {
      throw new BadRequestException('Stock cannot be negative');
    }

    let channelProduct = await this.channelProductRepo.findOne({
      where: { productId, channel, companyId },
    });

    const externalProductId = await this.callChannelAPI(channel, 'sync', {
      productName: product.name,
      price: price.toString(),
      stock,
    });

    if (!channelProduct) {
      channelProduct = this.channelProductRepo.create({
        companyId,
        productId,
        channel,
        externalProductId,
        price,
        stock,
        lastSyncedAt: new Date(),
      });
    } else {
      channelProduct.externalProductId = externalProductId;
      channelProduct.price = price;
      channelProduct.stock = stock;
      channelProduct.lastSyncedAt = new Date();
    }

    return this.channelProductRepo.save(channelProduct);
  }

  async updateChannelProductPrice(companyId: string, productId: string, channel: Channel, newPrice: Decimal): Promise<void> {
    const channelProduct = await this.channelProductRepo.findOne({
      where: { productId, channel, companyId },
    });

    if (!channelProduct) {
      throw new NotFoundException(`Product not found on ${channel}`);
    }

    if (newPrice.lessThanOrEqualTo(0)) {
      throw new BadRequestException('Price must be greater than zero');
    }

    await this.callChannelAPI(channel, 'updatePrice', {
      externalProductId: channelProduct.externalProductId,
      price: newPrice.toString(),
    });

    channelProduct.price = newPrice;
    channelProduct.lastSyncedAt = new Date();
    await this.channelProductRepo.save(channelProduct);
  }

  async updateChannelProductStock(companyId: string, productId: string, channel: Channel, newStock: number): Promise<void> {
    const channelProduct = await this.channelProductRepo.findOne({
      where: { productId, channel, companyId },
    });

    if (!channelProduct) {
      throw new NotFoundException(`Product not found on ${channel}`);
    }

    if (newStock < 0) {
      throw new BadRequestException('Stock cannot be negative');
    }

    await this.callChannelAPI(channel, 'updateStock', {
      externalProductId: channelProduct.externalProductId,
      stock: newStock,
    });

    channelProduct.stock = newStock;
    channelProduct.lastSyncedAt = new Date();
    await this.channelProductRepo.save(channelProduct);
  }

  async getChannelProduct(companyId: string, productId: string, channel: Channel): Promise<ChannelProduct | null> {
    return this.channelProductRepo.findOne({
      where: { companyId, productId, channel },
    });
  }

  async getChannelProductsByProduct(companyId: string, productId: string): Promise<ChannelProduct[]> {
    return this.channelProductRepo.find({
      where: { companyId, productId },
      order: { createdAt: 'ASC' },
    });
  }

  // ============ Inventory Management ============

  async getChannelInventory(companyId: string, channel: Channel, limit = 50, offset = 0): Promise<ChannelInventoryData> {
    const products = await this.channelProductRepo.find({
      where: { companyId, channel },
      take: limit,
      skip: offset,
      order: { createdAt: 'DESC' },
    });

    return {
      products: products.map(p => ({
        externalProductId: p.externalProductId,
        price: p.price,
        stock: p.stock,
        channelSku: p.channelSku,
      })),
      totalSKUs: await this.channelProductRepo.count({
        where: { companyId, channel },
      }),
      lastSyncedAt: products.length > 0 ? products[0].lastSyncedAt : new Date(),
    };
  }

  async syncInventoryToAllChannels(companyId: string, productId: string, totalStock: number): Promise<void> {
    if (totalStock < 0) {
      throw new BadRequestException('Total stock cannot be negative');
    }

    const channels = await this.listActiveChannels(companyId);
    if (channels.length === 0) {
      throw new BadRequestException('No active channels configured');
    }

    const channelProducts = await this.getChannelProductsByProduct(companyId, productId);
    if (channelProducts.length === 0) {
      throw new NotFoundException('Product not synced to any channel');
    }

    // Distribute stock proportionally across channels
    const stockPerChannel = Math.floor(totalStock / channels.length);
    const remainder = totalStock % channels.length;

    for (let i = 0; i < channels.length; i++) {
      const channel = channels[i];
      const channelProduct = channelProducts.find(cp => cp.channel === channel.channel);

      if (!channelProduct) continue;

      const stock = stockPerChannel + (i < remainder ? 1 : 0);
      try {
        await this.updateChannelProductStock(companyId, productId, channel.channel, stock);
      } catch (error) {
        this.logger.error(`Failed to sync stock to ${channel.channel}: ${error.message}`);
      }
    }
  }

  async getAllChannelInventory(companyId: string): Promise<Map<Channel, ChannelInventoryData>> {
    const channels = await this.listActiveChannels(companyId);
    const inventoryMap = new Map<Channel, ChannelInventoryData>();

    for (const config of channels) {
      const inventory = await this.getChannelInventory(companyId, config.channel);
      inventoryMap.set(config.channel, inventory);
    }

    return inventoryMap;
  }

  // ============ Order Sync ============

  async importOrderFromChannel(
    companyId: string,
    channel: Channel,
    externalOrderId: string,
    orderData: OrderImportData,
  ): Promise<Order> {
    const config = await this.getChannelConfig(companyId, channel);
    if (!config) {
      throw new NotFoundException(`Channel ${channel} not configured`);
    }

    const existingOrder = await this.orderRepo.findOne({
      where: { companyId, externalOrderId, channel },
    });

    if (existingOrder) {
      // Update existing order
      existingOrder.status = orderData.status;
      existingOrder.lastSyncedAt = new Date();
      return this.orderRepo.save(existingOrder);
    }

    // Validate products exist on channel
    for (const item of orderData.items) {
      const channelProduct = await this.channelProductRepo.findOne({
        where: { companyId, channel, externalProductId: item.externalProductId },
      });
      if (!channelProduct) {
        throw new NotFoundException(`Product ${item.externalProductId} not found on ${channel}`);
      }
    }

    const order = this.orderRepo.create({
      companyId,
      channel,
      externalOrderId,
      buyerName: orderData.buyerName,
      buyerPhone: orderData.buyerPhone,
      deliveryAddress: orderData.deliveryAddress,
      items: orderData.items,
      totalPrice: orderData.totalPrice,
      status: orderData.status,
      orderDate: orderData.orderDate,
      lastSyncedAt: new Date(),
    });

    return this.orderRepo.save(order);
  }

  async getChannelOrders(companyId: string, channel: Channel, limit = 50, offset = 0) {
    const [orders, total] = await this.orderRepo.findAndCount({
      where: { companyId, channel },
      take: limit,
      skip: offset,
      order: { orderDate: 'DESC' },
    });

    return { orders, total };
  }

  async updateChannelOrderStatus(companyId: string, orderId: string, channel: Channel, status: string): Promise<void> {
    const order = await this.orderRepo.findOne({
      where: { id: orderId, companyId, channel },
    });

    if (!order) {
      throw new NotFoundException('Order not found');
    }

    const validStatuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled'];
    if (!validStatuses.includes(status)) {
      throw new BadRequestException(`Invalid status: ${status}`);
    }

    order.status = status;
    order.lastSyncedAt = new Date();
    await this.orderRepo.save(order);

    // Sync back to channel
    await this.callChannelAPI(channel, 'updateOrderStatus', {
      externalOrderId: order.externalOrderId,
      status,
    });
  }

  async getOrdersByStatus(companyId: string, channel: Channel, status: string): Promise<Order[]> {
    return this.orderRepo.find({
      where: { companyId, channel, status },
      order: { orderDate: 'DESC' },
    });
  }

  // ============ Pricing Strategy ============

  async getChannelPricingTiers(companyId: string): Promise<PricingTier[]> {
    const channels = await this.listActiveChannels(companyId);

    return channels.map(config => ({
      channel: config.channel,
      margin: new Decimal(config.settings.defaultMargin || '1.2'),
      priceOverride: config.settings.priceOverride,
    }));
  }

  async setPriceRuleByChannel(companyId: string, channel: Channel, rules: PriceRuleData): Promise<void> {
    const config = await this.getChannelConfig(companyId, channel);
    if (!config) {
      throw new NotFoundException(`Channel ${channel} not configured`);
    }

    const priceRules = config.settings.priceRules || {};
    priceRules[channel] = {
      minPrice: rules.minPrice?.toString(),
      maxPrice: rules.maxPrice?.toString(),
      costMultiplier: rules.costMultiplier?.toString(),
      fixedMarkup: rules.fixedMarkup?.toString(),
      discountPercentage: rules.discountPercentage?.toString(),
    };

    config.settings.priceRules = priceRules;
    await this.channelConfigRepo.save(config);
  }

  async calculateChannelPrice(
    companyId: string,
    channel: Channel,
    baseCost: Decimal,
  ): Promise<Decimal> {
    const config = await this.getChannelConfig(companyId, channel);
    if (!config) {
      throw new NotFoundException(`Channel ${channel} not configured`);
    }

    const rules = config.settings.priceRules?.[channel];
    let price = baseCost;

    // Apply multiplier or markup
    if (rules?.costMultiplier) {
      price = baseCost.times(new Decimal(rules.costMultiplier));
    } else {
      price = baseCost.times(new Decimal(config.settings.defaultMargin || '1.2'));
    }

    if (rules?.fixedMarkup) {
      price = price.plus(new Decimal(rules.fixedMarkup));
    }

    // Apply discount
    if (rules?.discountPercentage) {
      const discount = price.times(new Decimal(rules.discountPercentage).dividedBy(100));
      price = price.minus(discount);
    }

    // Enforce min/max bounds
    if (rules?.minPrice && price.lessThan(new Decimal(rules.minPrice))) {
      price = new Decimal(rules.minPrice);
    }

    if (rules?.maxPrice && price.greaterThan(new Decimal(rules.maxPrice))) {
      price = new Decimal(rules.maxPrice);
    }

    return price;
  }

  // ============ Utilities ============

  private validateChannelCredentials(channel: Channel, credentials: ChannelCredentials): void {
    if (!credentials.apiKey || !credentials.shopId) {
      throw new BadRequestException(`Missing required credentials for ${channel}`);
    }

    if (channel === Channel.LAZADA && !credentials.sellerId) {
      throw new BadRequestException('Lazada requires sellerId');
    }

    if (channel === Channel.TIKTOK) {
      if (!credentials.accessToken || !credentials.refreshToken) {
        throw new BadRequestException('TikTok requires accessToken and refreshToken');
      }
    }
  }

  private async callChannelAPI(channel: Channel, action: string, payload: any): Promise<string> {
    // This is a stub for actual channel API calls
    // In production, implement actual integrations for each channel
    this.logger.debug(`Calling ${channel} API: ${action} with payload: ${JSON.stringify(payload)}`);

    // Return a mock external ID for sync operations
    if (action === 'sync') {
      return `${channel}_${Date.now()}`;
    }

    return '';
  }

  async getMultiChannelStats(companyId: string) {
    const channels = await this.listActiveChannels(companyId);
    const stats = {};

    for (const config of channels) {
      const productCount = await this.channelProductRepo.count({
        where: { companyId, channel: config.channel },
      });

      const [orders, orderCount] = await this.orderRepo.findAndCount({
        where: { companyId, channel: config.channel },
      });

      const totalStock = await this.channelProductRepo
        .createQueryBuilder('cp')
        .where('cp.companyId = :companyId', { companyId })
        .andWhere('cp.channel = :channel', { channel: config.channel })
        .select('SUM(cp.stock)', 'totalStock')
        .getRawOne();

      stats[config.channel] = {
        isActive: config.isActive,
        productCount,
        orderCount,
        totalStock: totalStock?.totalStock || 0,
        configuredAt: config.createdAt,
      };
    }

    return stats;
  }
}
