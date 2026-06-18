import { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';

function ChatPage() {
  const [messages, setMessages] = useState([
    { text: "Conectando con el agente...", sender: 'system' }
  ]);
  const [input, setInput] = useState('');
  const [showEscalate, setShowEscalate] = useState(false);
  const [botActivo, setBotActivo] = useState(true);
  const [escalateContext, setEscalateContext] = useState(null);
  const chatBoxRef = useRef(null);
  const socketRef = useRef(null);

  // Inicializar socket una sola vez
  useEffect(() => {
    socketRef.current = io("http://127.0.0.1:3000");
    const socket = socketRef.current;

    // Conexión exitosa
    socket.on("connect", () => {
      setMessages(prev => [...prev, { text: "🟢 Agente conectado. ¿En qué te puedo ayudar?", sender: 'system' }]);
    });

    // Escuchar respuesta de la IA (solo una vez por evento)
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

    // Escalamiento: backend detectó frustración
    socket.on("escalate_human", (data) => {
      setEscalateContext(data);
      setShowEscalate(true);
      setMessages(prev => [...prev, {
        text: "🔴 Detectamos frustración en tu mensaje. ¿Deseas hablar con un agente humano?",
        sender: 'system'
      }]);
    });

    // Confirmación de transferencia
    socket.on("transfer_confirmed", (data) => {
      setMessages(prev => [...prev, { text: `✅ ${data.message}`, sender: 'system' }]);
    });

    // Limpieza al desmontar (evita duplicados en StrictMode)
    return () => {
      socket.off("connect");
      socket.off("ai_response");
      socket.off("escalate_human");
      socket.off("transfer_confirmed");
      socket.disconnect();
    };
  }, []);

  // Auto-scroll
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
    </div>
  );
}

export default ChatPage;