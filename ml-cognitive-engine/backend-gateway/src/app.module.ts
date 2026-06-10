import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { CognitiveModule } from './cognitive/cognitive.module';
import { ChatModule } from './chat/chat.module'; // <-- AGREGADO

@Module({
  imports: [
    TypeOrmModule.forRoot({
      type: 'postgres',
      host: 'localhost',
      port: 5432,
      username: 'usuario_learning',
      password: 'password_secreto',
      database: 'aprendizaje_db',
      autoLoadEntities: true,
      synchronize: true,
    }),
    CognitiveModule,
    ChatModule, // <-- AGREGADO
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}