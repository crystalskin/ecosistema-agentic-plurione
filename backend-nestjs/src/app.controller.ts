import { Controller, Get } from '@nestjs/common';
import { AppService } from './app.service';

@Controller()
export class AppController {
  constructor(private readonly appService: AppService) {}

  @Get()
  getHello(): string {
    return this.appService.getHello();
  }

  @Get('logs')
  async getLogs() {
    return await this.appService.getLogs();
  }

  @Get('ml-status')
  async getMLOpsStatus() {
    return await this.appService.getMLOpsStatus();
  }
}