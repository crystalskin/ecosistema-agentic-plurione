import { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';

// Colores de botones según el tipo de opción del flujo guiado
const TIPO_ESTILOS = {
  avanzar: { background: '#2e7d32', color: '#fff', border: 'none' },
  resolver: { background: '#1b5e20', color: '#fff', border: 'none' },
  escalar:  { background: '#c62828', color: '#fff', border: 'none' },
  abandonar: { background: 'transparent', color: '#757575', border: '1px solid #ccc' },
};

function ChatPage() {
  const [messages, setMessages] = useState([
    { text: "Conectando con el agente...", sender: 'system' }
  ]);
  const [input, setInput] = useState('');
  const [showEscalate, setShowEscalate] = useState(false);
  const [botActivo, setBotActivo] = useState(true);
  const [escalateContext, setEscalateContext] = useState(null);
  const [flujoGuiado, setFlujoGuiado] = useState(null); // { incidenciaId, pasoId, mensaje, opciones[] }
  const chatBoxRef = useRef(null);
  const socketRef = useRef(null);

  useEffect(() => {
    socketRef.current = io("http://127.0.0.1:3000");
    const socket = socketRef.current;

    socket.on("connect", () => {
      setMessages(prev => [...prev, { text: "🟢 Agente conectado. ¿En qué te puedo ayudar?", sender: 'system' }]);
    });

    socket.on("ai_response", (data) => {
      if (data.status === 'success') {
        const pensamiento = `[${data.data.payload.intent.label} | ${data.data.payload.sentiment.label}]`;
        const respuestaBot = data.data.payload.generated_response;
        setMessages(prev => [
          ...prev,
          { text: `🧠 ${pensamiento}`, sender: 'ai-think' },
          { text: `🤖 ${respuestaBot}`, sender: 'ai' }
        ]);
      }
    });

    // M5: escalamiento por frustración
    socket.on("escalate_human", (data) => {
      setFlujoGuiado(null); // cerrar flujo guiado si estaba activo
      setEscalateContext(data);
      setShowEscalate(true);
      setMessages(prev => [...prev, {
        text: "🔴 Detectamos que necesitas asistencia adicional. ¿Deseas hablar con un agente humano?",
        sender: 'system'
      }]);
    });

    socket.on("transfer_confirmed", (data) => {
      setMessages(prev => [...prev, { text: `✅ ${data.message}`, sender: 'system' }]);
    });

    // M3: servidor ofrece opciones guiadas
    socket.on("opciones_guiadas", (data) => {
      setMessages(prev => [...prev, {
        text: `🔧 ${data.mensaje}`,
        sender: 'ai'
      }]);
      setFlujoGuiado(data);
    });

    // M3: flujo terminó (resuelto o abandonado)
    socket.on("flujo_completado", (data) => {
      const icon = data.resultado === 'resuelto' ? '✅' : '↩️';
      setMessages(prev => [...prev, {
        text: `${icon} ${data.mensaje}`,
        sender: 'system'
      }]);
      setFlujoGuiado(null);
    });

    return () => {
      socket.off("connect");
      socket.off("ai_response");
      socket.off("escalate_human");
      socket.off("transfer_confirmed");
      socket.off("opciones_guiadas");
      socket.off("flujo_completado");
      socket.disconnect();
    };
  }, []);

  useEffect(() => {
    chatBoxRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleRequestHuman = () => {
    socketRef.current.emit("request_human", {
      session_id: "session-react-01",
      raw_text: escalateContext?.message ?? '',
      sentiment_score: escalateContext?.score ?? null,
      emotion: escalateContext?.emotion ?? null,
    });
    setShowEscalate(false);
    setBotActivo(false);
    setMessages(prev => [...prev, {
      text: "🧑‍💼 Solicitaste hablar con un agente. El bot se ha detenido.",
      sender: 'system'
    }]);
  };

  // M3: usuario eligió una opción del flujo guiado
  const handleOpcionGuiada = (opcion) => {
    setMessages(prev => [...prev, { text: opcion.texto, sender: 'user' }]);
    socketRef.current.emit("respuesta_guiada", {
      session_id: "session-react-01",
      opcionTexto: opcion.texto,
    });
    setFlujoGuiado(null); // el servidor responderá con opciones_guiadas o flujo_completado
  };

  const sendMessage = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    if (!botActivo) {
      setMessages(prev => [...prev, {
        text: "⏸️ El bot está en pausa. Esperando agente humano...",
        sender: 'system'
      }]);
      setInput('');
      return;
    }

    setMessages(prev => [...prev, { text: input, sender: 'user' }]);
    socketRef.current.emit("user_message", {
      text: input,
      session_id: "session-react-01"
    });
    setInput('');
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>Agente Inteligente PluriOne</h2>
        <span className="status-dot"></span> En línea
      </div>
      <div className="chat-box">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
        <div ref={chatBoxRef} />
      </div>

      {/* M5: barra de escalamiento */}
      {showEscalate && (
        <div style={{ padding: '0.5rem 1rem', background: '#fff3f3', borderTop: '1px solid #ffcccc', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button
            onClick={handleRequestHuman}
            style={{ background: '#c62828', color: '#fff', border: 'none', borderRadius: '6px', padding: '0.5rem 1.25rem', cursor: 'pointer', fontWeight: 600, fontSize: '0.9rem' }}
          >
            🧑‍💼 Hablar con un agente humano
          </button>
          <button
            onClick={() => setShowEscalate(false)}
            style={{ background: 'transparent', color: '#757575', border: '1px solid #ccc', borderRadius: '6px', padding: '0.5rem 0.75rem', cursor: 'pointer', fontSize: '0.85rem' }}
          >
            Continuar con el bot
          </button>
        </div>
      )}

      {/* M3: opciones guiadas — reemplaza el input mientras el flujo está activo */}
      {flujoGuiado ? (
        <div style={{ padding: '0.75rem 1rem', background: '#f1f8e9', borderTop: '2px solid #a5d6a7', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <p style={{ margin: 0, fontSize: '0.8rem', color: '#388e3c', fontWeight: 600 }}>
            🔧 Selecciona una opción:
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {flujoGuiado.opciones.map((op, i) => (
              <button
                key={i}
                onClick={() => handleOpcionGuiada(op)}
                style={{
                  ...TIPO_ESTILOS[op.tipo] ?? TIPO_ESTILOS.avanzar,
                  borderRadius: '6px',
                  padding: '0.45rem 1rem',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  whiteSpace: 'nowrap',
                }}
              >
                {op.texto}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <form className="chat-input" onSubmit={sendMessage}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Escribe tu mensaje..."
            autoFocus
          />
          <button type="submit">Enviar</button>
        </form>
      )}
    </div>
  );
}

export default ChatPage;
