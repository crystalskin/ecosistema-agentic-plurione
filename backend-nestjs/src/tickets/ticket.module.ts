import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { TicketEntity } from './ticket.entity';
import { TicketService } from './ticket.service';
import { TicketController } from './ticket.controller';

@Module({
  imports: [TypeOrmModule.forFeature([TicketEntity])],
  controllers: [TicketController],
  providers: [TicketService],
  exports: [TicketService],
})
export class TicketModule {}
