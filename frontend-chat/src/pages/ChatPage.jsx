import { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';

function ChatPage() {
  const [messages, setMessages] = useState([
    { text: "Conectando con el agente...", sender: 'system' }
  ]);
  const [input, setInput] = useState('');
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

    // Limpieza al desmontar (evita duplicados en StrictMode)
    return () => {
      socket.off("connect");
      socket.off("ai_response");
      socket.disconnect();
    };
  }, []);

  // Auto-scroll
  useEffect(() => {
    chatBoxRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = (e) => {
    e.preventDefault();
    if (!input.trim()) return;

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