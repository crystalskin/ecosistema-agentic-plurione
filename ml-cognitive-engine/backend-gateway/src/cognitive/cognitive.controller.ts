import { Controller, Get, Query } from '@nestjs/common';
import { CognitiveService } from './cognitive.service';

@Controller('api/cognitive')
export class CognitiveController {
  constructor(private readonly cognitiveService: CognitiveService) {}

  // Expondremos este endpoint: GET /api/cognitive/analyze?text=hola&session_id=123
  @Get('analyze')
  async analyze(@Query('text') text: string, @Query('session_id') sessionId: string) {
    return await this.cognitiveService.analyzeText(text, sessionId);
  }
}