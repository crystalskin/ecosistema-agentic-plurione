import { useEffect, useState } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, ResponsiveContainer
} from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#AF19FF'];

export default function MetricsPage() {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    axios.get('http://localhost:3000/api/cognitive/metrics')
      .then(res => setMetrics(res.data))
      .catch(err => console.error('Error al cargar métricas', err));
  }, []);

  if (!metrics) return <p style={{ padding: '2rem' }}>Cargando métricas...</p>;

  return (
    <div style={{ padding: '2rem' }}>
      <h2>Dashboard de Métricas del Sistema</h2>
      <p><strong>Total de interacciones registradas:</strong> {metrics.total}</p>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2rem' }}>
        {/* Sentimientos */}
        <div>
          <h3>Distribución de Sentimientos</h3>
          <ResponsiveContainer width={400} height={300}>
            <PieChart>
              <Pie
                data={metrics.sentimentCounts}
                dataKey="count"
                nameKey="sentiment"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label
              >
                {metrics.sentimentCounts.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Intenciones */}
        <div>
          <h3>Intenciones Más Frecuentes</h3>
          <ResponsiveContainer width={500} height={300}>
            <BarChart data={metrics.intentCounts}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="intent" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#8884d8" name="Cantidad" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={{ marginTop: '2rem' }}>
        <p><strong>Confianza promedio de intención:</strong> {(metrics.avgConfidence * 100).toFixed(1)}%</p>
      </div>
    </div>
  );
}