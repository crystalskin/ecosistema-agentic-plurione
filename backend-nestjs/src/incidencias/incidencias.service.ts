import { Injectable } from '@nestjs/common';
import { ARBOLES } from './arboles';

interface FlujoState {
  incidenciaId: string;
  pasoActual: string;
  tsInicio: Date;
}

export interface OpcionResponse {
  texto: string;
  tipo: 'avanzar' | 'resolver' | 'escalar' | 'abandonar';
}

export interface PasoResponse {
  incidenciaId: string;
  pasoId: string;
  mensaje: string;
  opciones: OpcionResponse[];
}

export type AccionTerminal = 'resolver' | 'escalar' | 'abandonar';

@Injectable()
export class IncidenciasService {
  private readonly CONFIDENCE_THRESHOLD = 0.45;
  private readonly flujosActivos = new Map<string, FlujoState>();

  /** Devuelve el ID del árbol cuyo trigger_intents contiene el intent dado, o null. */
  encontrarArbol(intent: string): string | null {
    for (const [id, arbol] of Object.entries(ARBOLES)) {
      if (arbol.trigger_intents.includes(intent)) return id;
    }
    return null;
  }

  get confidenceThreshold(): number {
    return this.CONFIDENCE_THRESHOLD;
  }

  tieneFlujActivo(sessionId: string): boolean {
    return this.flujosActivos.has(sessionId);
  }

  iniciarFlujo(sessionId: string, incidenciaId: string): PasoResponse {
    this.flujosActivos.set(sessionId, {
      incidenciaId,
      pasoActual: 'inicio',
      tsInicio: new Date(),
    });
    return this.buildPasoResponse(incidenciaId, 'inicio');
  }

  procesarRespuesta(
    sessionId: string,
    opcionTexto: string,
  ): { paso?: PasoResponse; accion?: AccionTerminal } {
    const estado = this.flujosActivos.get(sessionId);
    if (!estado) return { accion: 'abandonar' };

    const arbol = ARBOLES[estado.incidenciaId];
    if (!arbol) return { accion: 'abandonar' };

    const paso = arbol.pasos[estado.pasoActual];
    if (!paso) return { accion: 'abandonar' };

    const opcion = paso.opciones.find((o) => o.texto === opcionTexto);
    if (!opcion) {
      this.flujosActivos.delete(sessionId);
      return { accion: 'abandonar' };
    }

    if (opcion.accion) {
      this.flujosActivos.delete(sessionId);
      return { accion: opcion.accion };
    }

    if (opcion.siguiente) {
      const siguientePaso = arbol.pasos[opcion.siguiente];
      if (!siguientePaso) {
        this.flujosActivos.delete(sessionId);
        return { accion: 'abandonar' };
      }
      estado.pasoActual = opcion.siguiente;
      return { paso: this.buildPasoResponse(estado.incidenciaId, opcion.siguiente) };
    }

    return { accion: 'abandonar' };
  }

  limpiarFlujo(sessionId: string): void {
    this.flujosActivos.delete(sessionId);
  }

  private buildPasoResponse(incidenciaId: string, pasoId: string): PasoResponse {
    const paso = ARBOLES[incidenciaId].pasos[pasoId];
    return {
      incidenciaId,
      pasoId,
      mensaje: paso.mensaje,
      opciones: paso.opciones.map((o) => ({
        texto: o.texto,
        tipo: (o.accion ?? 'avanzar') as OpcionResponse['tipo'],
      })),
    };
  }
}
