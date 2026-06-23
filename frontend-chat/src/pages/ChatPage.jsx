import { useState, useEffect, useRef, useCallback } from 'react';
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

const newMsg = (text, sender) => ({ text, sender, ts: new Date() });

function formatTime(ts) {
  return ts.toLocaleTimeString('es-MX', { hour: 'numeric', minute: '2-digit', hour12: true });
}

function getTsStyle(sender) {
  return {
    marginTop: '4px',
    fontSize: '0.68rem',
    lineHeight: 1,
    color: sender === 'user' ? 'rgba(255,255,255,0.58)' : '#bdbdbd',
    textAlign: 'right',
  };
}

function ChatPage() {
  const [messages, setMessages] = useState([
    newMsg("Conectando con el agente...", 'system')
  ]);
  const [input, setInput] = useState('');
  const [showEscalate, setShowEscalate] = useState(false);
  const [botActivo, setBotActivo] = useState(true);
  const [escalateContext, setEscalateContext] = useState(null);
  const [flujoGuiado, setFlujoGuiado] = useState(null);
  const [botEscribiendo, setBotEscribiendo]             = useState(false);
  const [showInactivityWarning, setShowInactivityWarning] = useState(false);
  const [isInactive, setIsInactive]                       = useState(false);
  const [isConnected, setIsConnected]                     = useState(false);
  const chatBoxRef      = useRef(null);
  const inputRef        = useRef(null);
  const socketRef       = useRef(null);
  const warningTimerRef = useRef(null);   // dispara "¿Sigues ahí?" a los 5 min
  const inactiveTimerRef = useRef(null);  // dispara pausa a los 60 seg tras el aviso

  // PARA PROBAR: cambia las dos constantes de abajo a 10_000 / 5_000 (ms),
  // verifica, y restáuralas a 5*60_000 / 60_000 antes del commit.
  const INACTIVITY_WARNING_MS = 5 * 60_000;  // 5 min → aparece "¿Sigues ahí?"
  const INACTIVITY_PAUSE_MS   = 60_000;      // 60 seg → sesión en pausa

  const resetInactivityTimer = useCallback(() => {
    clearTimeout(warningTimerRef.current);
    clearTimeout(inactiveTimerRef.current);
    setShowInactivityWarning(false);
    setIsInactive(false);
    warningTimerRef.current = setTimeout(() => {
      setShowInactivityWarning(true);
      inactiveTimerRef.current = setTimeout(() => {
        setShowInactivityWarning(false);
        setIsInactive(true);
      }, INACTIVITY_PAUSE_MS);
    }, INACTIVITY_WARNING_MS);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    socketRef.current = io("http://127.0.0.1:3000");
    const socket = socketRef.current;

    socket.on("connect", () => {
      setMessages(prev => [...prev, newMsg("🟢 Agente conectado. ¿En qué te puedo ayudar?", 'system')]);
      setIsConnected(true);
      resetInactivityTimer();
    });

    socket.on("ai_response", (data) => {
      setBotEscribiendo(false);
      if (data.status === 'success') {
        const pensamiento = `[${data.data.payload.intent.label} | ${data.data.payload.sentiment.label}]`;
        const respuestaBot = data.data.payload.generated_response;
        setMessages(prev => [
          ...prev,
          newMsg(`🧠 ${pensamiento}`, 'ai-think'),
          newMsg(`🤖 ${respuestaBot}`, 'ai'),
        ]);
      }
    });

    // M5: escalamiento por frustración
    socket.on("escalate_human", (data) => {
      setBotEscribiendo(false);
      setFlujoGuiado(null);
      setEscalateContext(data);
      setShowEscalate(true);
      setMessages(prev => [...prev, newMsg("🔴 Detectamos que necesitas asistencia adicional. ¿Deseas hablar con un agente humano?", 'system')]);
    });

    socket.on("transfer_confirmed", (data) => {
      setBotEscribiendo(false);
      setMessages(prev => [...prev, newMsg(`✅ ${data.message}`, 'system')]);
    });

    // M3: servidor ofrece opciones guiadas
    socket.on("opciones_guiadas", (data) => {
      setBotEscribiendo(false);
      setMessages(prev => [...prev, newMsg(`🔧 ${data.mensaje}`, 'ai')]);
      setFlujoGuiado(data);
    });

    // M3: flujo terminó (resuelto o abandonado)
    socket.on("flujo_completado", (data) => {
      setBotEscribiendo(false);
      const icon = data.resultado === 'resuelto' ? '✅' : '↩️';
      setMessages(prev => [...prev, newMsg(`${icon} ${data.mensaje}`, 'system')]);
      setFlujoGuiado(null);
    });

    socket.on("disconnect", () => {
      setIsConnected(false);
    });

    return () => {
      socket.off("connect");
      socket.off("disconnect");
      socket.off("ai_response");
      socket.off("escalate_human");
      socket.off("transfer_confirmed");
      socket.off("opciones_guiadas");
      socket.off("flujo_completado");
      clearTimeout(warningTimerRef.current);
      clearTimeout(inactiveTimerRef.current);
      socket.disconnect();
    };
  }, [resetInactivityTimer]);

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
    setMessages(prev => [...prev, newMsg("🧑‍💼 Solicitaste hablar con un agente. El bot se ha detenido.", 'system')]);
  };

  // M3: usuario eligió una opción del flujo guiado
  const handleOpcionGuiada = (opcion) => {
    resetInactivityTimer();
    setMessages(prev => [...prev, newMsg(opcion.texto, 'user')]);
    socketRef.current.emit("respuesta_guiada", {
      session_id: "session-react-01",
      opcionTexto: opcion.texto,
    });
    setFlujoGuiado(null);
  };

  const sendMessage = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    resetInactivityTimer();
    if (!botActivo) {
      setMessages(prev => [...prev, newMsg("⏸️ El bot está en pausa. Esperando agente humano...", 'system')]);
      setInput('');
      inputRef.current?.focus();
      return;
    }

    setMessages(prev => [...prev, newMsg(input, 'user')]);
    socketRef.current.emit("user_message", {
      text: input,
      session_id: "session-react-01"
    });
    setInput('');
    setBotEscribiendo(true);
    inputRef.current?.focus();
  };

  return (
    <>
    <style>{`
      @keyframes typingBounce {
        0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
        30%            { transform: translateY(-5px); opacity: 1; }
      }
      @keyframes msgEnter {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0);   }
      }
      .msg-enter {
        animation: msgEnter 0.25s ease-out;
      }
      @media (prefers-reduced-motion: reduce) {
        .msg-enter { animation: none; }
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
                background: isConnected ? '#a5d6a7' : '#ef9a9a',
                display: 'inline-block', flexShrink: 0,
              }} />
              {isConnected ? 'En línea' : 'Reconectando…'}
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
              <div key={index} className="msg-enter" style={getMsgStyle(msg.sender)}>
                {msg.text}
                {(msg.sender === 'user' || msg.sender === 'ai') && msg.ts && (
                  <div style={getTsStyle(msg.sender)}>{formatTime(msg.ts)}</div>
                )}
              </div>
            ))
          }
          {/* Typing indicator */}
          {botEscribiendo && (
            <div className="msg-enter" style={{
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
        ) : null}

        {/* Banner de inactividad — aparece sobre el input, nunca bloquea */}
        {(showInactivityWarning || isInactive) && (
          <div style={{
            padding: '0.6rem 1.5rem',
            background: isInactive ? '#fff3e0' : '#fffde7',
            borderTop: `1px solid ${isInactive ? '#ffcc80' : '#fff176'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '0.5rem',
            flexShrink: 0,
            fontSize: '0.85rem',
            color: isInactive ? '#e65100' : '#f57f17',
            fontFamily: "'Inter','Segoe UI',sans-serif",
          }}>
            <span>
              {isInactive
                ? '⏸ Sesión en pausa — escribe para reactivar'
                : '💬 ¿Sigues ahí?'}
            </span>
            {!isInactive && (
              <button
                onClick={resetInactivityTimer}
                style={{
                  background: '#f9a825', color: '#fff', border: 'none',
                  borderRadius: '12px', padding: '0.3rem 0.9rem',
                  cursor: 'pointer', fontWeight: 600, fontSize: '0.8rem',
                  fontFamily: "'Inter','Segoe UI',sans-serif",
                  flexShrink: 0,
                }}
              >
                Sigo aquí ✓
              </button>
            )}
          </div>
        )}

        {flujoGuiado ? null : (
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
              ref={inputRef}
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
