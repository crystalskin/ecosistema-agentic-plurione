import { Injectable, HttpException, HttpStatus } from '@nestjs/common';

@Injectable()
export class AppService {
  
  getHello(): string {
    return 'Backend NestJS funcionando!';
  }

  async getMLOpsStatus() {
    try {
      const response = await fetch('http://localhost:8000/api/ml-status');
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error conectando con ML Status:', error);
      throw new HttpException('Error al conectar con el motor de IA', HttpStatus.SERVICE_UNAVAILABLE);
    }
  }

  async getLogs() {
    const { Client } = require('pg');
    const client = new Client({
      host: 'localhost',
      port: 5432,
      database: 'aprendizaje_db',
      user: 'usuario_learning',
      password: 'password_secreto',
    });

    try {
      await client.connect();
      const res = await client.query('SELECT * FROM logs_interacciones ORDER BY fecha_captura DESC LIMIT 50');
      return res.rows;
    } catch (error) {
      console.error('Error en la base de datos:', error);
      return []; // Si falla la BD, devuelve vacío para que React no explote
    } finally {
      await client.end();
    }
  }
}