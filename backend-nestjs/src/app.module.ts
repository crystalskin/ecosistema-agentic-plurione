import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { CognitiveModule } from './cognitive/cognitive.module';
import { EscalamientoModule } from './escalamiento/escalamiento.module';
import { ChatGateway } from './chat/chat.gateway';

@Module({
  imports: [
    // 1. Conexión a la base de datos
    TypeOrmModule.forRoot({
      type: 'postgres',
      host: 'localhost',
      port: 5432,
      username: 'usuario_learning',
      password: 'password_secreto',
      database: 'aprendizaje_db',
      autoLoadEntities: true,     // Crea la tabla automáticamente si no existe
      synchronize: true,          // (Solo para desarrollo, mantiene la tabla sincronizada con el código)
    }),
    // 2. Nuestro módulo
    CognitiveModule,
    EscalamientoModule,
  ],
  controllers: [AppController],
  providers: [AppService, ChatGateway],
})
export class AppModule {}