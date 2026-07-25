import { Module } from '@nestjs/common';
import { PrismaService } from '@nestjs/prisma';
import { SuppliersService } from './services/suppliers.service';
import { SuppliersController } from './controllers/suppliers.controller';

@Module({
  providers: [SuppliersService, PrismaService],
  controllers: [SuppliersController],
  exports: [SuppliersService],
})
export class ProcurementModule {}
