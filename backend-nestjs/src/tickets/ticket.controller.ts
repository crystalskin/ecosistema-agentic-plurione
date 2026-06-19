import { Controller, Post, Body, BadRequestException } from '@nestjs/common';
import { TicketService } from './ticket.service';

@Controller('api/tickets')
export class TicketController {
  constructor(private readonly ticketService: TicketService) {}

  @Post('clasificar')
  async clasificar(@Body() body: { texto: string }) {
    if (!body.texto?.trim()) {
      throw new BadRequestException("El campo 'texto' es obligatorio.");
    }
    return this.ticketService.clasificarYGuardar(body.texto);
  }
}
