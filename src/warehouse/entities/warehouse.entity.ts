import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, Index } from 'typeorm';

@Entity('warehouses')
@Index(['companyId'])
export class Warehouse {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  companyId: string;

  @Column()
  name: string;

  @Column()
  location: string;

  @Column({ type: 'decimal', precision: 12, scale: 2 })
  capacity: number; // Total storage capacity in units

  @Column({ type: 'decimal', precision: 12, scale: 2, default: 0 })
  usedCapacity: number;

  @Column({ default: true })
  isActive: boolean;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
