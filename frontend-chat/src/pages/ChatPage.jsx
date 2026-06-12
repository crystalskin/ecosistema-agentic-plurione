import { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';


// Mantenemos la IP directa para evitar problemas de DNS en Windows
const socket = io("http://127.0.0.1:3000");

function ChatPage() {
  const [messages, setMessages] = useState([
    { text: "Conectando con el agente...", sender: 'system' }
  ]);
  const [input, setInput] = useState('');
  const chatBoxRef = useRef(null);

  // 1. Manejar la conexión
  useEffect(() => {
    socket.on("connect", () => {
      setMessages(prev => [...prev, { text: "🟢 Agente conectado. ¿En qué te puedo ayudar?", sender: 'system' }]);
    });
    
    socket.on("connect_error", (err) => {
      console.error("ERROR DE CONEXIÓN WebSocket:", err.message);
    });

    // 2. Escuchar la respuesta de nuestra IA
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

    // NOTA: Ya NO ponemos el return () => socket.disconnect() 
    // porque el "Strict Mode" de React en desarrollo lo mata al instante.
  }, []);

  // Bajar el scroll automáticamente
  useEffect(() => {
    chatBoxRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 3. Enviar mensaje
  const sendMessage = (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    setMessages(prev => [...prev, { text: input, sender: 'user' }]);
    
    socket.emit("user_message", { 
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