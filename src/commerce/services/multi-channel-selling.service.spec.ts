import { Test, TestingModule } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Decimal } from 'decimal.js';
import { MultiChannelSellingService, Channel, ChannelCredentials, ChannelSettings } from './multi-channel-selling.service';
import { ChannelConfig } from '../entities/channel-config.entity';
import { ChannelProduct } from '../entities/channel-product.entity';
import { Order } from '../entities/order.entity';
import { Product } from '../entities/product.entity';
import { BadRequestException, NotFoundException, ConflictException } from '@nestjs/common';

describe('MultiChannelSellingService', () => {
  let service: MultiChannelSellingService;
  let channelConfigRepo: Repository<ChannelConfig>;
  let channelProductRepo: Repository<ChannelProduct>;
  let orderRepo: Repository<Order>;
  let productRepo: Repository<Product>;

  const mockCompanyId = 'company-123';
  const mockProductId = 'product-456';
  const mockOrderId = 'order-789';

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        MultiChannelSellingService,
        {
          provide: getRepositoryToken(ChannelConfig),
          useValue: {
            findOne: jest.fn(),
            find: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
            count: jest.fn(),
          },
        },
        {
          provide: getRepositoryToken(ChannelProduct),
          useValue: {
            findOne: jest.fn(),
            find: jest.fn(),
            findAndCount: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
            count: jest.fn(),
            createQueryBuilder: jest.fn(),
          },
        },
        {
          provide: getRepositoryToken(Order),
          useValue: {
            findOne: jest.fn(),
            find: jest.fn(),
            findAndCount: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
            count: jest.fn(),
          },
        },
        {
          provide: getRepositoryToken(Product),
          useValue: {
            findOne: jest.fn(),
            find: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
          },
        },
      ],
    }).compile();

    service = module.get<MultiChannelSellingService>(MultiChannelSellingService);
    channelConfigRepo = module.get<Repository<ChannelConfig>>(getRepositoryToken(ChannelConfig));
    channelProductRepo = module.get<Repository<ChannelProduct>>(getRepositoryToken(ChannelProduct));
    orderRepo = module.get<Repository<Order>>(getRepositoryToken(Order));
    productRepo = module.get<Repository<Product>>(getRepositoryToken(Product));
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Channel Management', () => {
    describe('addChannel', () => {
      it('should add a new channel successfully', async () => {
        const credentials: ChannelCredentials = {
          apiKey: 'test-api-key',
          shopId: 'shop-123',
        };

        const mockChannelConfig = {
          id: 'config-1',
          companyId: mockCompanyId,
          channel: Channel.SHOPEE,
          credentials,
          settings: { enableAutoSync: true, syncInterval: 60, defaultMargin: '1.2' },
          isActive: true,
          createdAt: new Date(),
          updatedAt: new Date(),
        };

        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(null);
        jest.spyOn(channelConfigRepo, 'create').mockReturnValue(mockChannelConfig as any);
        jest.spyOn(channelConfigRepo, 'save').mockResolvedValue(mockChannelConfig as any);

        const result = await service.addChannel(mockCompanyId, Channel.SHOPEE, credentials);

        expect(result).toEqual(mockChannelConfig);
        expect(channelConfigRepo.findOne).toHaveBeenCalledWith({
          where: { companyId: mockCompanyId, channel: Channel.SHOPEE },
        });
      });

      it('should throw error for duplicate channel', async () => {
        const credentials: ChannelCredentials = {
          apiKey: 'test-api-key',
          shopId: 'shop-123',
        };

        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue({} as any);

        await expect(service.addChannel(mockCompanyId, Channel.SHOPEE, credentials)).rejects.toThrow(ConflictException);
      });

      it('should throw error for invalid channel', async () => {
        const credentials: ChannelCredentials = {
          apiKey: 'test-api-key',
          shopId: 'shop-123',
        };

        await expect(service.addChannel(mockCompanyId, 'invalid-channel' as any, credentials)).rejects.toThrow(
          BadRequestException,
        );
      });

      it('should throw error for missing Shopee credentials', async () => {
        const credentials: ChannelCredentials = {
          apiKey: '',
          shopId: 'shop-123',
        };

        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(null);

        await expect(service.addChannel(mockCompanyId, Channel.SHOPEE, credentials)).rejects.toThrow(
          BadRequestException,
        );
      });

      it('should throw error for missing Lazada sellerId', async () => {
        const credentials: ChannelCredentials = {
          apiKey: 'test-api-key',
          shopId: 'shop-123',
        };

        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(null);

        await expect(service.addChannel(mockCompanyId, Channel.LAZADA, credentials)).rejects.toThrow(
          BadRequestException,
        );
      });

      it('should throw error for missing TikTok tokens', async () => {
        const credentials: ChannelCredentials = {
          apiKey: 'test-api-key',
          shopId: 'shop-123',
        };

        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(null);

        await expect(service.addChannel(mockCompanyId, Channel.TIKTOK, credentials)).rejects.toThrow(
          BadRequestException,
        );
      });
    });

    describe('getChannelConfig', () => {
      it('should retrieve channel config', async () => {
        const mockConfig = { id: 'config-1', channel: Channel.SHOPEE } as any;
        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(mockConfig);

        const result = await service.getChannelConfig(mockCompanyId, Channel.SHOPEE);

        expect(result).toEqual(mockConfig);
      });

      it('should return null if channel not found', async () => {
        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(null);

        const result = await service.getChannelConfig(mockCompanyId, Channel.SHOPEE);

        expect(result).toBeNull();
      });
    });

    describe('updateChannelSettings', () => {
      it('should update channel settings', async () => {
        const mockConfig = {
          id: 'config-1',
          channel: Channel.SHOPEE,
          settings: { enableAutoSync: true, syncInterval: 60 },
        } as any;

        const newSettings: ChannelSettings = { syncInterval: 120 };

        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(mockConfig);
        jest.spyOn(channelConfigRepo, 'save').mockResolvedValue(mockConfig);

        const result = await service.updateChannelSettings(mockCompanyId, Channel.SHOPEE, newSettings);

        expect(result).toBeDefined();
        expect(channelConfigRepo.save).toHaveBeenCalled();
      });

      it('should throw error if channel not found', async () => {
        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(null);

        await expect(
          service.updateChannelSettings(mockCompanyId, Channel.SHOPEE, { syncInterval: 120 }),
        ).rejects.toThrow(NotFoundException);
      });
    });

    describe('listActiveChannels', () => {
      it('should list all active channels', async () => {
        const mockChannels = [
          { channel: Channel.SHOPEE, isActive: true },
          { channel: Channel.LAZADA, isActive: true },
        ] as any[];

        jest.spyOn(channelConfigRepo, 'find').mockResolvedValue(mockChannels);

        const result = await service.listActiveChannels(mockCompanyId);

        expect(result).toHaveLength(2);
        expect(channelConfigRepo.find).toHaveBeenCalledWith({
          where: { companyId: mockCompanyId, isActive: true },
          order: { createdAt: 'ASC' },
        });
      });
    });

    describe('deactivateChannel', () => {
      it('should deactivate a channel', async () => {
        const mockConfig = { channel: Channel.SHOPEE, isActive: true } as any;

        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(mockConfig);
        jest.spyOn(channelConfigRepo, 'save').mockResolvedValue(mockConfig);

        await service.deactivateChannel(mockCompanyId, Channel.SHOPEE);

        expect(mockConfig.isActive).toBeFalsy();
        expect(channelConfigRepo.save).toHaveBeenCalledWith(mockConfig);
      });
    });
  });

  describe('Product Sync', () => {
    describe('syncProductToChannel', () => {
      it('should sync product to channel', async () => {
        const mockConfig = { channel: Channel.SHOPEE } as any;
        const mockProduct = { id: mockProductId, name: 'Test Product' } as any;
        const price = new Decimal('100');
        const stock = 50;

        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(mockConfig);
        jest.spyOn(productRepo, 'findOne').mockResolvedValue(mockProduct);
        jest.spyOn(channelProductRepo, 'findOne').mockResolvedValue(null);
        jest.spyOn(channelProductRepo, 'create').mockReturnValue({} as any);
        jest.spyOn(channelProductRepo, 'save').mockResolvedValue({
          productId: mockProductId,
          channel: Channel.SHOPEE,
          externalProductId: 'shopee_123',
          price,
          stock,
        } as any);

        const result = await service.syncProductToChannel(
          mockCompanyId,
          mockProductId,
          Channel.SHOPEE,
          price,
          stock,
        );

        expect(result).toBeDefined();
        expect(result.externalProductId).toBeDefined();
      });

      it('should throw error if channel not configured', async () => {
        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(null);

        await expect(
          service.syncProductToChannel(mockCompanyId, mockProductId, Channel.SHOPEE, new Decimal('100'), 50),
        ).rejects.toThrow(NotFoundException);
      });

      it('should throw error if product not found', async () => {
        const mockConfig = { channel: Channel.SHOPEE } as any;
        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(mockConfig);
        jest.spyOn(productRepo, 'findOne').mockResolvedValue(null);

        await expect(
          service.syncProductToChannel(mockCompanyId, mockProductId, Channel.SHOPEE, new Decimal('100'), 50),
        ).rejects.toThrow(NotFoundException);
      });

      it('should throw error for negative stock', async () => {
        const mockConfig = { channel: Channel.SHOPEE } as any;
        const mockProduct = { id: mockProductId } as any;

        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(mockConfig);
        jest.spyOn(productRepo, 'findOne').mockResolvedValue(mockProduct);

        await expect(
          service.syncProductToChannel(mockCompanyId, mockProductId, Channel.SHOPEE, new Decimal('100'), -1),
        ).rejects.toThrow(BadRequestException);
      });

      it('should update existing channel product', async () => {
        const mockConfig = { channel: Channel.SHOPEE } as any;
        const mockProduct = { id: mockProductId } as any;
        const existingChannelProduct = {
          productId: mockProductId,
          channel: Channel.SHOPEE,
          price: new Decimal('80'),
        } as any;
        const newPrice = new Decimal('100');

        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(mockConfig);
        jest.spyOn(productRepo, 'findOne').mockResolvedValue(mockProduct);
        jest.spyOn(channelProductRepo, 'findOne').mockResolvedValue(existingChannelProduct);
        jest.spyOn(channelProductRepo, 'save').mockResolvedValue(existingChannelProduct);

        const result = await service.syncProductToChannel(
          mockCompanyId,
          mockProductId,
          Channel.SHOPEE,
          newPrice,
          50,
        );

        expect(result).toBeDefined();
      });
    });

    describe('updateChannelProductPrice', () => {
      it('should update product price on channel', async () => {
        const mockChannelProduct = {
          productId: mockProductId,
          channel: Channel.SHOPEE,
          price: new Decimal('100'),
          externalProductId: 'shopee_123',
        } as any;
        const newPrice = new Decimal('120');

        jest.spyOn(channelProductRepo, 'findOne').mockResolvedValue(mockChannelProduct);
        jest.spyOn(channelProductRepo, 'save').mockResolvedValue(mockChannelProduct);

        await service.updateChannelProductPrice(mockCompanyId, mockProductId, Channel.SHOPEE, newPrice);

        expect(channelProductRepo.save).toHaveBeenCalled();
      });

      it('should throw error if product not found on channel', async () => {
        jest.spyOn(channelProductRepo, 'findOne').mockResolvedValue(null);

        await expect(
          service.updateChannelProductPrice(mockCompanyId, mockProductId, Channel.SHOPEE, new Decimal('100')),
        ).rejects.toThrow(NotFoundException);
      });

      it('should throw error for zero or negative price', async () => {
        const mockChannelProduct = { productId: mockProductId } as any;
        jest.spyOn(channelProductRepo, 'findOne').mockResolvedValue(mockChannelProduct);

        await expect(
          service.updateChannelProductPrice(mockCompanyId, mockProductId, Channel.SHOPEE, new Decimal('0')),
        ).rejects.toThrow(BadRequestException);
      });
    });

    describe('updateChannelProductStock', () => {
      it('should update product stock on channel', async () => {
        const mockChannelProduct = {
          productId: mockProductId,
          channel: Channel.SHOPEE,
          stock: 50,
          externalProductId: 'shopee_123',
        } as any;

        jest.spyOn(channelProductRepo, 'findOne').mockResolvedValue(mockChannelProduct);
        jest.spyOn(channelProductRepo, 'save').mockResolvedValue(mockChannelProduct);

        await service.updateChannelProductStock(mockCompanyId, mockProductId, Channel.SHOPEE, 100);

        expect(channelProductRepo.save).toHaveBeenCalled();
      });

      it('should throw error for negative stock', async () => {
        const mockChannelProduct = { productId: mockProductId } as any;
        jest.spyOn(channelProductRepo, 'findOne').mockResolvedValue(mockChannelProduct);

        await expect(
          service.updateChannelProductStock(mockCompanyId, mockProductId, Channel.SHOPEE, -5),
        ).rejects.toThrow(BadRequestException);
      });
    });

    describe('getChannelProduct', () => {
      it('should retrieve channel product', async () => {
        const mockProduct = { productId: mockProductId, channel: Channel.SHOPEE } as any;
        jest.spyOn(channelProductRepo, 'findOne').mockResolvedValue(mockProduct);

        const result = await service.getChannelProduct(mockCompanyId, mockProductId, Channel.SHOPEE);

        expect(result).toEqual(mockProduct);
      });

      it('should return null if product not found', async () => {
        jest.spyOn(channelProductRepo, 'findOne').mockResolvedValue(null);

        const result = await service.getChannelProduct(mockCompanyId, mockProductId, Channel.SHOPEE);

        expect(result).toBeNull();
      });
    });

    describe('getChannelProductsByProduct', () => {
      it('should retrieve all channel listings for a product', async () => {
        const mockProducts = [
          { channel: Channel.SHOPEE, price: new Decimal('100') },
          { channel: Channel.LAZADA, price: new Decimal('110') },
        ] as any[];

        jest.spyOn(channelProductRepo, 'find').mockResolvedValue(mockProducts);

        const result = await service.getChannelProductsByProduct(mockCompanyId, mockProductId);

        expect(result).toHaveLength(2);
      });
    });
  });

  describe('Inventory Management', () => {
    describe('getChannelInventory', () => {
      it('should retrieve channel inventory', async () => {
        const mockProducts = [
          { externalProductId: 'ext_1', price: new Decimal('100'), stock: 50 },
        ] as any[];

        jest.spyOn(channelProductRepo, 'find').mockResolvedValue(mockProducts);
        jest.spyOn(channelProductRepo, 'count').mockResolvedValue(1);

        const result = await service.getChannelInventory(mockCompanyId, Channel.SHOPEE);

        expect(result.products).toHaveLength(1);
        expect(result.totalSKUs).toBe(1);
      });

      it('should support pagination', async () => {
        jest.spyOn(channelProductRepo, 'find').mockResolvedValue([]);
        jest.spyOn(channelProductRepo, 'count').mockResolvedValue(100);

        await service.getChannelInventory(mockCompanyId, Channel.SHOPEE, 10, 20);

        expect(channelProductRepo.find).toHaveBeenCalledWith({
          where: { companyId: mockCompanyId, channel: Channel.SHOPEE },
          take: 10,
          skip: 20,
          order: { createdAt: 'DESC' },
        });
      });
    });

    describe('syncInventoryToAllChannels', () => {
      it('should distribute stock across channels', async () => {
        const mockChannels = [
          { channel: Channel.SHOPEE, isActive: true },
          { channel: Channel.LAZADA, isActive: true },
        ] as any[];
        const mockChannelProducts = [
          { channel: Channel.SHOPEE, productId: mockProductId },
          { channel: Channel.LAZADA, productId: mockProductId },
        ] as any[];

        jest.spyOn(channelConfigRepo, 'find').mockResolvedValue(mockChannels);
        jest.spyOn(channelProductRepo, 'find').mockResolvedValue(mockChannelProducts);
        jest.spyOn(channelProductRepo, 'findOne').mockResolvedValue({} as any);
        jest.spyOn(channelProductRepo, 'save').mockResolvedValue({} as any);

        await service.syncInventoryToAllChannels(mockCompanyId, mockProductId, 100);

        expect(channelConfigRepo.find).toHaveBeenCalled();
      });

      it('should throw error for negative total stock', async () => {
        await expect(service.syncInventoryToAllChannels(mockCompanyId, mockProductId, -1)).rejects.toThrow(
          BadRequestException,
        );
      });

      it('should throw error if no active channels', async () => {
        jest.spyOn(channelConfigRepo, 'find').mockResolvedValue([]);

        await expect(service.syncInventoryToAllChannels(mockCompanyId, mockProductId, 100)).rejects.toThrow(
          BadRequestException,
        );
      });

      it('should throw error if product not synced to any channel', async () => {
        const mockChannels = [{ channel: Channel.SHOPEE }] as any[];
        jest.spyOn(channelConfigRepo, 'find').mockResolvedValue(mockChannels);
        jest.spyOn(channelProductRepo, 'find').mockResolvedValue([]);

        await expect(service.syncInventoryToAllChannels(mockCompanyId, mockProductId, 100)).rejects.toThrow(
          NotFoundException,
        );
      });

      it('should handle remainder when distributing stock', async () => {
        const mockChannels = [
          { channel: Channel.SHOPEE },
          { channel: Channel.LAZADA },
          { channel: Channel.TIKTOK },
        ] as any[];
        const mockChannelProducts = [
          { channel: Channel.SHOPEE, productId: mockProductId },
          { channel: Channel.LAZADA, productId: mockProductId },
          { channel: Channel.TIKTOK, productId: mockProductId },
        ] as any[];

        jest.spyOn(channelConfigRepo, 'find').mockResolvedValue(mockChannels);
        jest.spyOn(channelProductRepo, 'find').mockResolvedValue(mockChannelProducts);
        jest.spyOn(channelProductRepo, 'findOne').mockResolvedValue({} as any);
        jest.spyOn(channelProductRepo, 'save').mockResolvedValue({} as any);

        // 100 / 3 = 33 per channel, 1 remainder
        await service.syncInventoryToAllChannels(mockCompanyId, mockProductId, 100);

        expect(channelProductRepo.save).toHaveBeenCalled();
      });
    });

    describe('getAllChannelInventory', () => {
      it('should retrieve inventory for all active channels', async () => {
        const mockChannels = [
          { channel: Channel.SHOPEE, isActive: true },
          { channel: Channel.LAZADA, isActive: true },
        ] as any[];

        jest.spyOn(channelConfigRepo, 'find').mockResolvedValue(mockChannels);
        jest.spyOn(channelProductRepo, 'find').mockResolvedValue([]);
        jest.spyOn(channelProductRepo, 'count').mockResolvedValue(0);

        const result = await service.getAllChannelInventory(mockCompanyId);

        expect(result.size).toBe(2);
      });
    });
  });

  describe('Order Sync', () => {
    describe('importOrderFromChannel', () => {
      it('should import order from channel', async () => {
        const mockConfig = { channel: Channel.SHOPEE } as any;
        const mockChannelProduct = { externalProductId: 'ext_1' } as any;
        const orderData = {
          externalOrderId: 'ext_order_1',
          buyerName: 'John Doe',
          deliveryAddress: '123 Main St',
          items: [{ externalProductId: 'ext_1', quantity: 2, price: new Decimal('100') }],
          totalPrice: new Decimal('200'),
          orderDate: new Date(),
          status: 'confirmed' as const,
        };

        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(mockConfig);
        jest.spyOn(channelProductRepo, 'findOne').mockResolvedValue(mockChannelProduct);
        jest.spyOn(orderRepo, 'findOne').mockResolvedValue(null);
        jest.spyOn(orderRepo, 'create').mockReturnValue({} as any);
        jest.spyOn(orderRepo, 'save').mockResolvedValue({
          id: mockOrderId,
          externalOrderId: 'ext_order_1',
          status: 'confirmed',
        } as any);

        const result = await service.importOrderFromChannel(
          mockCompanyId,
          Channel.SHOPEE,
          'ext_order_1',
          orderData,
        );

        expect(result).toBeDefined();
      });

      it('should update existing order', async () => {
        const mockConfig = { channel: Channel.SHOPEE } as any;
        const existingOrder = { id: mockOrderId, status: 'pending' } as any;
        const orderData = {
          externalOrderId: 'ext_order_1',
          buyerName: 'John Doe',
          deliveryAddress: '123 Main St',
          items: [],
          totalPrice: new Decimal('200'),
          orderDate: new Date(),
          status: 'confirmed' as const,
        };

        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(mockConfig);
        jest.spyOn(orderRepo, 'findOne').mockResolvedValue(existingOrder);
        jest.spyOn(orderRepo, 'save').mockResolvedValue(existingOrder);

        const result = await service.importOrderFromChannel(
          mockCompanyId,
          Channel.SHOPEE,
          'ext_order_1',
          orderData,
        );

        expect(result.status).toBe('confirmed');
      });

      it('should throw error if channel not configured', async () => {
        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(null);

        await expect(
          service.importOrderFromChannel(mockCompanyId, Channel.SHOPEE, 'ext_1', {
            externalOrderId: 'ext_1',
            buyerName: 'John',
            deliveryAddress: 'addr',
            items: [],
            totalPrice: new Decimal('100'),
            orderDate: new Date(),
            status: 'pending',
          }),
        ).rejects.toThrow(NotFoundException);
      });

      it('should throw error if product not found on channel', async () => {
        const mockConfig = { channel: Channel.SHOPEE } as any;
        const orderData = {
          externalOrderId: 'ext_order_1',
          buyerName: 'John Doe',
          deliveryAddress: '123 Main St',
          items: [{ externalProductId: 'ext_unknown', quantity: 1, price: new Decimal('100') }],
          totalPrice: new Decimal('100'),
          orderDate: new Date(),
          status: 'pending' as const,
        };

        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(mockConfig);
        jest.spyOn(orderRepo, 'findOne').mockResolvedValue(null);
        jest.spyOn(channelProductRepo, 'findOne').mockResolvedValue(null);

        await expect(
          service.importOrderFromChannel(mockCompanyId, Channel.SHOPEE, 'ext_order_1', orderData),
        ).rejects.toThrow(NotFoundException);
      });
    });

    describe('getChannelOrders', () => {
      it('should retrieve channel orders', async () => {
        const mockOrders = [{ id: mockOrderId, channel: Channel.SHOPEE }] as any[];
        jest.spyOn(orderRepo, 'findAndCount').mockResolvedValue([mockOrders, 1]);

        const result = await service.getChannelOrders(mockCompanyId, Channel.SHOPEE);

        expect(result.orders).toHaveLength(1);
        expect(result.total).toBe(1);
      });

      it('should support pagination', async () => {
        jest.spyOn(orderRepo, 'findAndCount').mockResolvedValue([[], 100]);

        await service.getChannelOrders(mockCompanyId, Channel.SHOPEE, 20, 40);

        expect(orderRepo.findAndCount).toHaveBeenCalledWith({
          where: { companyId: mockCompanyId, channel: Channel.SHOPEE },
          take: 20,
          skip: 40,
          order: { orderDate: 'DESC' },
        });
      });
    });

    describe('updateChannelOrderStatus', () => {
      it('should update order status', async () => {
        const mockOrder = { id: mockOrderId, status: 'pending', externalOrderId: 'ext_1' } as any;
        jest.spyOn(orderRepo, 'findOne').mockResolvedValue(mockOrder);
        jest.spyOn(orderRepo, 'save').mockResolvedValue(mockOrder);

        await service.updateChannelOrderStatus(mockCompanyId, mockOrderId, Channel.SHOPEE, 'shipped');

        expect(mockOrder.status).toBe('shipped');
        expect(orderRepo.save).toHaveBeenCalledWith(mockOrder);
      });

      it('should throw error if order not found', async () => {
        jest.spyOn(orderRepo, 'findOne').mockResolvedValue(null);

        await expect(
          service.updateChannelOrderStatus(mockCompanyId, mockOrderId, Channel.SHOPEE, 'shipped'),
        ).rejects.toThrow(NotFoundException);
      });

      it('should throw error for invalid status', async () => {
        const mockOrder = { id: mockOrderId, status: 'pending' } as any;
        jest.spyOn(orderRepo, 'findOne').mockResolvedValue(mockOrder);

        await expect(
          service.updateChannelOrderStatus(mockCompanyId, mockOrderId, Channel.SHOPEE, 'invalid-status'),
        ).rejects.toThrow(BadRequestException);
      });

      it('should validate allowed statuses', async () => {
        const mockOrder = { id: mockOrderId, status: 'pending', externalOrderId: 'ext_1' } as any;
        jest.spyOn(orderRepo, 'findOne').mockResolvedValue(mockOrder);
        jest.spyOn(orderRepo, 'save').mockResolvedValue(mockOrder);

        const validStatuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled'];

        for (const status of validStatuses) {
          await service.updateChannelOrderStatus(mockCompanyId, mockOrderId, Channel.SHOPEE, status);
        }

        expect(orderRepo.save).toHaveBeenCalledTimes(5);
      });
    });

    describe('getOrdersByStatus', () => {
      it('should retrieve orders by status', async () => {
        const mockOrders = [{ status: 'shipped' }] as any[];
        jest.spyOn(orderRepo, 'find').mockResolvedValue(mockOrders);

        const result = await service.getOrdersByStatus(mockCompanyId, Channel.SHOPEE, 'shipped');

        expect(result).toHaveLength(1);
      });
    });
  });

  describe('Pricing Strategy', () => {
    describe('getChannelPricingTiers', () => {
      it('should retrieve pricing tiers for all channels', async () => {
        const mockChannels = [
          { channel: Channel.SHOPEE, settings: { defaultMargin: '1.2' } },
          { channel: Channel.LAZADA, settings: { defaultMargin: '1.25' } },
        ] as any[];

        jest.spyOn(channelConfigRepo, 'find').mockResolvedValue(mockChannels);

        const result = await service.getChannelPricingTiers(mockCompanyId);

        expect(result).toHaveLength(2);
        expect(result[0].margin.toString()).toBe('1.2');
      });
    });

    describe('setPriceRuleByChannel', () => {
      it('should set price rule for channel', async () => {
        const mockConfig = { channel: Channel.SHOPEE, settings: {} } as any;
        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(mockConfig);
        jest.spyOn(channelConfigRepo, 'save').mockResolvedValue(mockConfig);

        const rules = {
          minPrice: new Decimal('50'),
          maxPrice: new Decimal('500'),
          costMultiplier: new Decimal('1.5'),
        };

        await service.setPriceRuleByChannel(mockCompanyId, Channel.SHOPEE, rules);

        expect(channelConfigRepo.save).toHaveBeenCalled();
      });

      it('should throw error if channel not configured', async () => {
        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(null);

        await expect(
          service.setPriceRuleByChannel(mockCompanyId, Channel.SHOPEE, {
            minPrice: new Decimal('50'),
          }),
        ).rejects.toThrow(NotFoundException);
      });
    });

    describe('calculateChannelPrice', () => {
      it('should calculate price with default margin', async () => {
        const mockConfig = {
          channel: Channel.SHOPEE,
          settings: { defaultMargin: '1.2', priceRules: {} },
        } as any;

        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(mockConfig);

        const baseCost = new Decimal('100');
        const price = await service.calculateChannelPrice(mockCompanyId, Channel.SHOPEE, baseCost);

        expect(price.equals(new Decimal('120'))).toBe(true);
      });

      it('should apply cost multiplier rule', async () => {
        const mockConfig = {
          channel: Channel.SHOPEE,
          settings: {
            defaultMargin: '1.2',
            priceRules: {
              [Channel.SHOPEE]: { costMultiplier: '1.5' },
            },
          },
        } as any;

        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(mockConfig);

        const baseCost = new Decimal('100');
        const price = await service.calculateChannelPrice(mockCompanyId, Channel.SHOPEE, baseCost);

        expect(price.equals(new Decimal('150'))).toBe(true);
      });

      it('should apply fixed markup', async () => {
        const mockConfig = {
          channel: Channel.SHOPEE,
          settings: {
            defaultMargin: '1.2',
            priceRules: {
              [Channel.SHOPEE]: { fixedMarkup: '20' },
            },
          },
        } as any;

        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(mockConfig);

        const baseCost = new Decimal('100');
        const price = await service.calculateChannelPrice(mockCompanyId, Channel.SHOPEE, baseCost);

        expect(price.equals(new Decimal('140'))).toBe(true);
      });

      it('should apply discount percentage', async () => {
        const mockConfig = {
          channel: Channel.SHOPEE,
          settings: {
            defaultMargin: '1.2',
            priceRules: {
              [Channel.SHOPEE]: { discountPercentage: '10' },
            },
          },
        } as any;

        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(mockConfig);

        const baseCost = new Decimal('100');
        const price = await service.calculateChannelPrice(mockCompanyId, Channel.SHOPEE, baseCost);

        expect(price.equals(new Decimal('108'))).toBe(true);
      });

      it('should enforce minimum price bound', async () => {
        const mockConfig = {
          channel: Channel.SHOPEE,
          settings: {
            defaultMargin: '0.5',
            priceRules: {
              [Channel.SHOPEE]: { minPrice: '100' },
            },
          },
        } as any;

        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(mockConfig);

        const baseCost = new Decimal('100');
        const price = await service.calculateChannelPrice(mockCompanyId, Channel.SHOPEE, baseCost);

        expect(price.equals(new Decimal('100'))).toBe(true);
      });

      it('should enforce maximum price bound', async () => {
        const mockConfig = {
          channel: Channel.SHOPEE,
          settings: {
            defaultMargin: '2.0',
            priceRules: {
              [Channel.SHOPEE]: { maxPrice: '150' },
            },
          },
        } as any;

        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(mockConfig);

        const baseCost = new Decimal('100');
        const price = await service.calculateChannelPrice(mockCompanyId, Channel.SHOPEE, baseCost);

        expect(price.equals(new Decimal('150'))).toBe(true);
      });

      it('should throw error if channel not configured', async () => {
        jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(null);

        await expect(
          service.calculateChannelPrice(mockCompanyId, Channel.SHOPEE, new Decimal('100')),
        ).rejects.toThrow(NotFoundException);
      });
    });
  });

  describe('Multi-Tenant Isolation', () => {
    it('should isolate channels by company', async () => {
      const company1 = 'company-1';
      const company2 = 'company-2';

      jest.spyOn(channelConfigRepo, 'findOne').mockImplementation((options: any) => {
        if (options.where.companyId === company1) {
          return Promise.resolve({ channel: Channel.SHOPEE } as any);
        }
        return Promise.resolve(null);
      });

      const result1 = await service.getChannelConfig(company1, Channel.SHOPEE);
      const result2 = await service.getChannelConfig(company2, Channel.SHOPEE);

      expect(result1).toBeDefined();
      expect(result2).toBeNull();
    });

    it('should isolate products by company', async () => {
      const company1 = 'company-1';
      const company2 = 'company-2';

      jest.spyOn(channelProductRepo, 'findOne').mockImplementation((options: any) => {
        if (options.where.companyId === company1) {
          return Promise.resolve({ productId: mockProductId } as any);
        }
        return Promise.resolve(null);
      });

      const result1 = await service.getChannelProduct(company1, mockProductId, Channel.SHOPEE);
      const result2 = await service.getChannelProduct(company2, mockProductId, Channel.SHOPEE);

      expect(result1).toBeDefined();
      expect(result2).toBeNull();
    });

    it('should isolate orders by company', async () => {
      const company1 = 'company-1';
      const company2 = 'company-2';

      jest.spyOn(orderRepo, 'findAndCount').mockImplementation((options: any) => {
        if (options.where.companyId === company1) {
          return Promise.resolve([[{ id: mockOrderId }] as any, 1]);
        }
        return Promise.resolve([[], 0]);
      });

      const result1 = await service.getChannelOrders(company1, Channel.SHOPEE);
      const result2 = await service.getChannelOrders(company2, Channel.SHOPEE);

      expect(result1.total).toBe(1);
      expect(result2.total).toBe(0);
    });
  });

  describe('Edge Cases & Error Handling', () => {
    it('should handle stock depletion during sync', async () => {
      const mockConfig = { channel: Channel.SHOPEE } as any;
      const mockProduct = { id: mockProductId } as any;

      jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(mockConfig);
      jest.spyOn(productRepo, 'findOne').mockResolvedValue(mockProduct);
      jest.spyOn(channelProductRepo, 'findOne').mockResolvedValue(null);
      jest.spyOn(channelProductRepo, 'create').mockReturnValue({} as any);
      jest.spyOn(channelProductRepo, 'save').mockResolvedValue({ stock: 0 } as any);

      const result = await service.syncProductToChannel(
        mockCompanyId,
        mockProductId,
        Channel.SHOPEE,
        new Decimal('100'),
        0,
      );

      expect(result.stock).toBe(0);
    });

    it('should handle concurrent order imports', async () => {
      const mockConfig = { channel: Channel.SHOPEE } as any;
      const mockChannelProduct = { externalProductId: 'ext_1' } as any;

      jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(mockConfig);
      jest.spyOn(channelProductRepo, 'findOne').mockResolvedValue(mockChannelProduct);
      jest.spyOn(orderRepo, 'findOne').mockResolvedValue(null);
      jest.spyOn(orderRepo, 'create').mockReturnValue({} as any);
      jest.spyOn(orderRepo, 'save').mockResolvedValue({ id: 'order-1' } as any);

      const orderData = {
        externalOrderId: 'ext_1',
        buyerName: 'John',
        deliveryAddress: 'addr',
        items: [{ externalProductId: 'ext_1', quantity: 1, price: new Decimal('100') }],
        totalPrice: new Decimal('100'),
        orderDate: new Date(),
        status: 'pending' as const,
      };

      const promises = Array(5)
        .fill(null)
        .map(() => service.importOrderFromChannel(mockCompanyId, Channel.SHOPEE, 'ext_1', orderData));

      await Promise.all(promises);

      expect(orderRepo.save).toHaveBeenCalled();
    });

    it('should handle large inventory distributions', async () => {
      const mockChannels = [
        { channel: Channel.SHOPEE },
        { channel: Channel.LAZADA },
        { channel: Channel.TIKTOK },
      ] as any[];
      const mockChannelProducts = mockChannels.map(c => ({ channel: c.channel, productId: mockProductId })) as any[];

      jest.spyOn(channelConfigRepo, 'find').mockResolvedValue(mockChannels);
      jest.spyOn(channelProductRepo, 'find').mockResolvedValue(mockChannelProducts);
      jest.spyOn(channelProductRepo, 'findOne').mockResolvedValue({} as any);
      jest.spyOn(channelProductRepo, 'save').mockResolvedValue({} as any);

      await service.syncInventoryToAllChannels(mockCompanyId, mockProductId, 999999);

      expect(channelProductRepo.save).toHaveBeenCalled();
    });

    it('should handle price calculation with all rules combined', async () => {
      const mockConfig = {
        channel: Channel.SHOPEE,
        settings: {
          defaultMargin: '1.0',
          priceRules: {
            [Channel.SHOPEE]: {
              costMultiplier: '1.5',
              fixedMarkup: '10',
              discountPercentage: '5',
              minPrice: '100',
              maxPrice: '500',
            },
          },
        },
      } as any;

      jest.spyOn(channelConfigRepo, 'findOne').mockResolvedValue(mockConfig);

      const baseCost = new Decimal('100');
      const price = await service.calculateChannelPrice(mockCompanyId, Channel.SHOPEE, baseCost);

      // 100 * 1.5 = 150, + 10 = 160, - 5% = 152
      expect(price.greaterThanOrEqualTo(new Decimal('100'))).toBe(true);
      expect(price.lessThanOrEqualTo(new Decimal('500'))).toBe(true);
    });
  });

  describe('Multi-Channel Stats', () => {
    it('should retrieve stats for all channels', async () => {
      const mockChannels = [
        { channel: Channel.SHOPEE, isActive: true, createdAt: new Date() },
        { channel: Channel.LAZADA, isActive: true, createdAt: new Date() },
      ] as any[];

      jest.spyOn(channelConfigRepo, 'find').mockResolvedValue(mockChannels);
      jest.spyOn(channelProductRepo, 'count').mockResolvedValue(10);
      jest.spyOn(orderRepo, 'findAndCount').mockResolvedValue([[], 5]);
      jest.spyOn(channelProductRepo, 'createQueryBuilder').mockReturnValue({
        where: jest.fn().mockReturnThis(),
        andWhere: jest.fn().mockReturnThis(),
        select: jest.fn().mockReturnThis(),
        getRawOne: jest.fn().mockResolvedValue({ totalStock: 100 }),
      } as any);

      const result = await service.getMultiChannelStats(mockCompanyId);

      expect(Object.keys(result)).toContain(Channel.SHOPEE);
      expect(Object.keys(result)).toContain(Channel.LAZADA);
    });
  });
});
