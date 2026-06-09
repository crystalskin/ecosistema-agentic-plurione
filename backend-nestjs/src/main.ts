import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  
  // Habilitar CORS para que React pueda leer los datos
  app.enableCors();
  
  await app.listen(3000);
}
bootstrap();