import { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, ResponsiveContainer,
} from 'recharts';

const SENTIMENT_COLORS = { negative: '#ef5350', neutral: '#78909c', positive: '#66bb6a' };
const INTENT_COLORS = ['#1b5e20', '#2e7d32', '#388e3c', '#43a047', '#66bb6a', '#a5d6a7'];

const s = {
  page:       { fontFamily: 'sans-serif', background: '#f5f5f5', minHeight: '100vh', padding: '2rem' },
  header:     { background: '#2e7d32', color: '#fff', padding: '1.25rem 2rem', borderRadius: '8px', marginBottom: '1.5rem' },
  hTitle:     { margin: 0, fontSize: '1.5rem', fontWeight: 700 },
  hSub:       { margin: '0.25rem 0 0', opacity: 0.8, fontSize: '0.875rem' },
  kpiRow:     { display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' },
  kpiCard:    { flex: '1 1 180px', background: '#fff', border: '1px solid #e0e0e0', borderRadius: '8px', padding: '1.25rem', boxShadow: '0 1px 3px rgba(0,0,0,0.08)' },
  kpiLabel:   { fontSize: '0.75rem', color: '#757575', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.5rem' },
  kpiValue:   { fontSize: '2rem', fontWeight: 700, color: '#2e7d32' },
  kpiNeg:     { fontSize: '2rem', fontWeight: 700, color: '#ef5350' },
  chartsRow:  { display: 'flex', gap: '1.5rem', flexWrap: 'wrap', marginBottom: '1.5rem', alignItems: 'flex-start' },
  card:       { background: '#fff', border: '1px solid #e0e0e0', borderRadius: '8px', padding: '1.25rem', boxShadow: '0 1px 3px rgba(0,0,0,0.08)' },
  cardTitle:  { fontSize: '1rem', fontWeight: 600, color: '#2e7d32', marginTop: 0, marginBottom: '1rem' },
  table:      { width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' },
  th:         { background: '#e8f5e9', color: '#2e7d32', textAlign: 'left', padding: '0.6rem 0.75rem', borderBottom: '2px solid #c8e6c9', fontWeight: 600 },
  td:         { padding: '0.6rem 0.75rem', borderBottom: '1px solid #f0f0f0', color: '#424242' },
  badge:      { display: 'inline-block', padding: '2px 8px', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 600, color: '#fff' },
  errorBox:   { background: '#ffebee', border: '1px solid #ef9a9a', color: '#c62828', padding: '1rem', borderRadius: '8px' },
  loading:    { display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '50vh', color: '#757575' },
};

function badgeColor(sentiment) {
  return SENTIMENT_COLORS[sentiment] ?? '#bdbdbd';
}

function truncate(str, n) {
  return str && str.length > n ? str.slice(0, n) + '…' : (str ?? '—');
}

function EmptyChart() {
  return (
    <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#bdbdbd', fontSize: '0.9rem' }}>
      Sin datos disponibles
    </div>
  );
}

export default function MetricsPage() {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('http://localhost:3000/api/cognitive/metrics')
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(setMetrics)
      .catch(err => setError(err.message));
  }, []);

  if (error) return (
    <div style={s.page}>
      <div style={s.errorBox}>
        <strong>Error al cargar métricas:</strong> {error}
        <br /><small>Verifica que NestJS esté corriendo en localhost:3000</small>
      </div>
    </div>
  );

  if (!metrics) return <div style={{ ...s.page, ...s.loading }}>Cargando métricas…</div>;

  const negativePct = metrics.total > 0
    ? Math.round((metrics.sentimentCounts.find(x => x.sentiment === 'negative')?.count ?? 0) / metrics.total * 100)
    : 0;

  return (
    <div style={s.page}>
      {/* Encabezado */}
      <div style={s.header}>
        <h2 style={s.hTitle}>Dashboard de Métricas</h2>
        <p style={s.hSub}>Sistema Agentic PluriOne — Interacciones registradas</p>
      </div>

      {/* KPI Cards */}
      <div style={s.kpiRow}>
        <div style={s.kpiCard}>
          <div style={s.kpiLabel}>Total interacciones</div>
          <div style={s.kpiValue}>{metrics.total}</div>
        </div>
        <div style={s.kpiCard}>
          <div style={s.kpiLabel}>Sentimiento negativo</div>
          <div style={s.kpiNeg}>{negativePct}%</div>
        </div>
        <div style={s.kpiCard}>
          <div style={s.kpiLabel}>Confianza promedio</div>
          <div style={s.kpiValue}>{(metrics.avgConfidence * 100).toFixed(1)}%</div>
        </div>
      </div>

      {/* Gráficas */}
      <div style={s.chartsRow}>
        {/* Pie — sentimientos */}
        <div style={{ ...s.card, flex: '1 1 340px' }}>
          <h3 style={s.cardTitle}>Distribución de Sentimientos</h3>
          {metrics.sentimentCounts.length === 0 ? <EmptyChart /> : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart margin={{ top: 0, bottom: 0 }}>
                <Pie
                  data={metrics.sentimentCounts}
                  dataKey="count"
                  nameKey="sentiment"
                  cx="50%"
                  cy="45%"
                  outerRadius={85}
                >
                  {metrics.sentimentCounts.map((entry, i) => (
                    <Cell key={i} fill={badgeColor(entry.sentiment)} />
                  ))}
                </Pie>
                <Tooltip formatter={(v) => [v, 'Mensajes']} />
                <Legend verticalAlign="bottom" height={36} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Bar — intenciones */}
        <div style={{ ...s.card, flex: '1 1 420px' }}>
          <h3 style={s.cardTitle}>Intenciones Más Frecuentes</h3>
          {metrics.intentCounts.length === 0 ? <EmptyChart /> : (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={metrics.intentCounts} margin={{ bottom: 40, left: -10 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="intent"
                tickFormatter={v => truncate(v, 14)}
                angle={-30}
                textAnchor="end"
                interval={0}
                tick={{ fontSize: 11 }}
              />
              <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
              <Tooltip labelFormatter={l => l} formatter={(v) => [v, 'Mensajes']} />
              <Bar dataKey="count" name="Mensajes" radius={[4, 4, 0, 0]}>
                {metrics.intentCounts.map((_, i) => (
                  <Cell key={i} fill={INTENT_COLORS[i % INTENT_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Tabla de últimas interacciones */}
      <div style={s.card}>
        <h3 style={s.cardTitle}>Últimas Interacciones</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={s.table}>
            <thead>
              <tr>
                <th style={s.th}>Mensaje</th>
                <th style={s.th}>Intención</th>
                <th style={s.th}>Sentimiento</th>
                <th style={s.th}>Emoción</th>
                <th style={s.th}>Fecha</th>
              </tr>
            </thead>
            <tbody>
              {metrics.ultimos.length === 0 && (
                <tr><td colSpan={5} style={{ ...s.td, textAlign: 'center', color: '#bdbdbd', padding: '2rem' }}>Sin interacciones registradas</td></tr>
              )}
              {metrics.ultimos.map(row => (
                <tr key={row.event_id}>
                  <td style={s.td}>{truncate(row.raw_text, 42)}</td>
                  <td style={{ ...s.td, fontFamily: 'monospace', fontSize: '0.8rem' }}>{row.intent}</td>
                  <td style={s.td}>
                    <span style={{ ...s.badge, background: badgeColor(row.sentiment) }}>{row.sentiment}</span>
                  </td>
                  <td style={{ ...s.td, color: '#616161' }}>{row.emotion}</td>
                  <td style={{ ...s.td, color: '#9e9e9e', fontSize: '0.8rem' }}>
                    {new Date(row.timestamp).toLocaleString('es-MX', { dateStyle: 'short', timeStyle: 'short' })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
