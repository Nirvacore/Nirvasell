import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, Index } from 'typeorm';

@Entity('suppliers')
@Index(['companyId', 'name'])
@Index(['companyId', 'email'], { unique: true })
export class Supplier {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  companyId: string;

  @Column()
  name: string;

  @Column()
  contact: string; // Contact person name

  @Column()
  email: string;

  @Column()
  phone: string;

  @Column()
  paymentTerms: string; // 'cod' | 'net30' | 'net60' | 'net90'

  @Column('decimal', { precision: 3, scale: 2, default: 3.0 })
  rating: number; // 1-5 stars

  @Column({ nullable: true })
  address?: string;

  @Column({ nullable: true })
  city?: string;

  @Column({ nullable: true })
  country?: string;

  @Column({ nullable: true })
  taxId?: string;

  @Column({ default: true })
  isActive: boolean;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
