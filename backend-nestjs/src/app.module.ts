import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { CognitiveModule } from './cognitive/cognitive.module';

@Module({
  imports: [
    // 1. Conexión a la base de datos
    TypeOrmModule.forRoot({
      type: 'postgres',
      host: 'localhost',
      port: 5432,
      username: 'invitado',       // ⚠️ VERIFICA EN TU DOCKER-COMPOSE.YML
      password: 'invitado_pass',  // ⚠️ VERIFICA EN TU DOCKER-COMPOSE.YML
      database: 'postgres',       // ⚠️ EL NOMBRE DE TU BASE DE DATOS
      autoLoadEntities: true,     // Crea la tabla automáticamente si no existe
      synchronize: true,          // (Solo para desarrollo, mantiene la tabla sincronizada con el código)
    }),
    // 2. Nuestro módulo
    CognitiveModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}