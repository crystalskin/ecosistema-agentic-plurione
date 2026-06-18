import { Injectable } from '@nestjs/common';
import axios from 'axios';

@Injectable()
export class CognitiveService {
  async analyzeText(text: string, sessionId: string) {
    try {
      const response = await axios.post('http://127.0.0.1:8000/api/v1/cognize', null, {
        params: { text, session_id: sessionId },
      });
      return response.data;
    } catch (error) {
      console.error('Error llamando a FastAPI:', error.message);
      throw new Error('Error al procesar el mensaje con IA');
    }
  }
}