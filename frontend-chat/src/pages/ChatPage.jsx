import { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';

// Colores de botones según el tipo de opción del flujo guiado
const TIPO_ESTILOS = {
  avanzar:  { background: '#2e7d32', color: '#fff', border: 'none' },
  resolver: { background: '#1b5e20', color: '#fff', border: 'none' },
  escalar:  { background: '#c62828', color: '#fff', border: 'none' },
  abandonar: { background: 'transparent', color: '#757575', border: '1px solid #ccc' },
};

// Cambiar a true para ver etiquetas del clasificador durante desarrollo
const MOSTRAR_DEBUG = false;

function dotStyle(i) {
  return {
    display: 'inline-block',
    width: '7px',
    height: '7px',
    borderRadius: '50%',
    background: '#43a047',
    animation: 'typingBounce 1.2s ease-in-out infinite',
    animationDelay: `${i * 0.2}s`,
  };
}

function getMsgStyle(sender) {
  const base = {
    fontFamily: "'Inter','Segoe UI',system-ui,sans-serif",
    fontSize: '0.9rem',
    lineHeight: 1.55,
    padding: '0.6rem 1rem',
    borderRadius: '12px',
    maxWidth: '78%',
    wordBreak: 'break-word',
  };
  switch (sender) {
    case 'user':
      return { ...base, background: '#2e7d32', color: '#fff',
               alignSelf: 'flex-end', borderBottomRightRadius: '3px' };
    case 'ai':
      return { ...base, background: '#fff', color: '#212121',
               boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
               alignSelf: 'flex-start', borderBottomLeftRadius: '3px' };
    case 'system':
      return { ...base, background: '#e8f5e9', color: '#2e7d32',
               fontSize: '0.8rem', alignSelf: 'center', maxWidth: '90%',
               textAlign: 'center', borderRadius: '20px', padding: '0.4rem 1rem' };
    case 'ai-think':
      return { ...base, background: '#fff8e1', color: '#f57c00',
               fontSize: '0.75rem', alignSelf: 'flex-start',
               border: '1px solid #ffe082', padding: '0.3rem 0.75rem' };
    default:
      return base;
  }
}

function ChatPage() {
  const [messages, setMessages] = useState([
    { text: "Conectando con el agente...", sender: 'system' }
  ]);
  const [input, setInput] = useState('');
  const [showEscalate, setShowEscalate] = useState(false);
  const [botActivo, setBotActivo] = useState(true);
  const [escalateContext, setEscalateContext] = useState(null);
  const [flujoGuiado, setFlujoGuiado] = useState(null);
  const [botEscribiendo, setBotEscribiendo] = useState(false);
  const chatBoxRef = useRef(null);
  const socketRef = useRef(null);

  useEffect(() => {
    socketRef.current = io("http://127.0.0.1:3000");
    const socket = socketRef.current;

    socket.on("connect", () => {
      setMessages(prev => [...prev, { text: "🟢 Agente conectado. ¿En qué te puedo ayudar?", sender: 'system' }]);
    });

    socket.on("ai_response", (data) => {
      setBotEscribiendo(false);
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
      setBotEscribiendo(false);
      setFlujoGuiado(null);
      setEscalateContext(data);
      setShowEscalate(true);
      setMessages(prev => [...prev, {
        text: "🔴 Detectamos que necesitas asistencia adicional. ¿Deseas hablar con un agente humano?",
        sender: 'system'
      }]);
    });

    socket.on("transfer_confirmed", (data) => {
      setBotEscribiendo(false);
      setMessages(prev => [...prev, { text: `✅ ${data.message}`, sender: 'system' }]);
    });

    // M3: servidor ofrece opciones guiadas
    socket.on("opciones_guiadas", (data) => {
      setBotEscribiendo(false);
      setMessages(prev => [...prev, {
        text: `🔧 ${data.mensaje}`,
        sender: 'ai'
      }]);
      setFlujoGuiado(data);
    });

    // M3: flujo terminó (resuelto o abandonado)
    socket.on("flujo_completado", (data) => {
      setBotEscribiendo(false);
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
  }, [messages, botEscribiendo]);

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
    setFlujoGuiado(null);
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
    setBotEscribiendo(true);
  };

  return (
    <>
    <style>{`
      @keyframes typingBounce {
        0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
        30%            { transform: translateY(-5px); opacity: 1; }
      }
    `}</style>
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#f0f4f1',
      padding: '1.5rem',
      boxSizing: 'border-box',
      fontFamily: "'Inter','Segoe UI',system-ui,sans-serif",
    }}>
      {/* Tarjeta del chat */}
      <div style={{
        width: '100%',
        maxWidth: '680px',
        height: '82vh',
        maxHeight: '820px',
        display: 'flex',
        flexDirection: 'column',
        borderRadius: '16px',
        boxShadow: '0 4px 28px rgba(0,0,0,0.13)',
        overflow: 'hidden',
        background: '#fff',
      }}>

        {/* HEADER */}
        <div style={{
          background: 'linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%)',
          padding: '1.25rem 1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.85rem',
          flexShrink: 0,
        }}>
          <div style={{
            width: '40px', height: '40px', borderRadius: '50%',
            background: 'rgba(255,255,255,0.15)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '1.2rem', flexShrink: 0,
          }}>
            🤖
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
            <span style={{
              color: '#fff', fontWeight: 700, fontSize: '1.05rem',
              letterSpacing: '-0.01em', lineHeight: 1.2,
            }}>
              Agente Inteligente PluriOne
            </span>
            <span style={{
              color: 'rgba(255,255,255,0.78)', fontSize: '0.8rem',
              display: 'flex', alignItems: 'center', gap: '0.4rem',
            }}>
              <span style={{
                width: '8px', height: '8px', borderRadius: '50%',
                background: '#a5d6a7', display: 'inline-block', flexShrink: 0,
              }} />
              En línea
            </span>
          </div>
        </div>

        {/* MENSAJES */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '1.25rem 1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.6rem',
          background: '#f8fdf8',
        }}>
          {messages
            .filter(msg => MOSTRAR_DEBUG || msg.sender !== 'ai-think')
            .map((msg, index) => (
              <div key={index} style={getMsgStyle(msg.sender)}>
                {msg.text}
              </div>
            ))
          }
          {/* Typing indicator */}
          {botEscribiendo && (
            <div style={{
              background: '#fff',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              alignSelf: 'flex-start',
              borderRadius: '12px',
              borderBottomLeftRadius: '3px',
              padding: '0.6rem 1rem',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}>
              <span style={dotStyle(0)} />
              <span style={dotStyle(1)} />
              <span style={dotStyle(2)} />
            </div>
          )}
          <div ref={chatBoxRef} />
        </div>

        {/* M5: barra de escalamiento */}
        {showEscalate && (
          <div style={{
            padding: '0.85rem 1.5rem',
            background: '#fff3f3',
            borderTop: '2px solid #ef9a9a',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            flexWrap: 'wrap',
            flexShrink: 0,
          }}>
            <button
              onClick={handleRequestHuman}
              style={{
                background: '#c62828', color: '#fff', border: 'none',
                borderRadius: '8px', padding: '0.6rem 1.25rem',
                cursor: 'pointer', fontWeight: 600, fontSize: '0.875rem',
                fontFamily: "'Inter','Segoe UI',sans-serif",
              }}
            >
              🧑‍💼 Hablar con un agente humano
            </button>
            <button
              onClick={() => setShowEscalate(false)}
              style={{
                background: 'transparent', color: '#757575',
                border: '1px solid #ccc', borderRadius: '8px',
                padding: '0.6rem 1rem', cursor: 'pointer',
                fontSize: '0.85rem',
                fontFamily: "'Inter','Segoe UI',sans-serif",
              }}
            >
              Continuar con el bot
            </button>
          </div>
        )}

        {/* M3: opciones guiadas / input normal */}
        {flujoGuiado ? (
          <div style={{
            padding: '1rem 1.5rem',
            background: '#f1f8e9',
            borderTop: '2px solid #a5d6a7',
            flexShrink: 0,
          }}>
            <p style={{
              margin: '0 0 0.6rem', fontSize: '0.78rem', color: '#388e3c',
              fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em',
            }}>
              Selecciona una opción:
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {flujoGuiado.opciones.map((op, i) => (
                <button
                  key={i}
                  onClick={() => handleOpcionGuiada(op)}
                  style={{
                    ...TIPO_ESTILOS[op.tipo] ?? TIPO_ESTILOS.avanzar,
                    borderRadius: '8px',
                    padding: '0.5rem 1.1rem',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                    fontWeight: 500,
                    fontFamily: "'Inter','Segoe UI',sans-serif",
                  }}
                >
                  {op.texto}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <form
            onSubmit={sendMessage}
            style={{
              padding: '1rem 1.5rem',
              background: '#fff',
              borderTop: '1px solid #e8f5e9',
              display: 'flex',
              gap: '0.75rem',
              alignItems: 'center',
              flexShrink: 0,
            }}
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Escribe tu mensaje..."
              autoFocus
              style={{
                flex: 1,
                padding: '0.65rem 1rem',
                border: '1.5px solid #c8e6c9',
                borderRadius: '24px',
                outline: 'none',
                fontSize: '0.9rem',
                fontFamily: "'Inter','Segoe UI',sans-serif",
                background: '#fafdf8',
                color: '#212121',
              }}
            />
            <button
              type="submit"
              style={{
                background: '#2e7d32',
                color: '#fff',
                border: 'none',
                borderRadius: '24px',
                padding: '0.65rem 1.4rem',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.875rem',
                fontFamily: "'Inter','Segoe UI',sans-serif",
                flexShrink: 0,
              }}
            >
              Enviar
            </button>
          </form>
        )}
      </div>
    </div>
    </>
  );
}

export default ChatPage;
