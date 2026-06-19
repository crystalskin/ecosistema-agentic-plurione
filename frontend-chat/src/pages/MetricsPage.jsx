import { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, ResponsiveContainer,
} from 'recharts';

// ─── Paleta PluriOne ──────────────────────────────────────────────────────────
const C = {
  primary:   '#2e7d32',
  dark:      '#1b5e20',
  medium:    '#43a047',
  light:     '#e8f5e9',
  pageBg:    '#f0f4f1',
  negative:  '#ef5350',
  neutral:   '#78909c',
  positive:  '#66bb6a',
  warning:   '#f57c00',
  info:      '#1976d2',
  text:      '#212121',
  textSub:   '#616161',
  textMuted: '#9e9e9e',
  border:    '#e0e0e0',
  white:     '#ffffff',
};

const SENTIMENT_COLORS = {
  negative: C.negative,
  neutral:  C.neutral,
  positive: C.positive,
};

const INTENT_COLORS   = [C.dark, C.primary, C.medium, '#66bb6a', '#a5d6a7', '#c8e6c9'];
const PRIORIDAD_COLORS = { alta: C.negative, media: C.warning, baja: C.positive };
const CATEGORIA_COLOR = C.primary;

// ─── Helpers ──────────────────────────────────────────────────────────────────

function truncate(str, n) {
  return str && str.length > n ? str.slice(0, n) + '…' : (str ?? '—');
}

function badgeColor(sentiment) {
  return SENTIMENT_COLORS[sentiment] ?? '#bdbdbd';
}

function formatDate(ts) {
  return new Date(ts).toLocaleString('es-MX', { dateStyle: 'short', timeStyle: 'short' });
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function EmptyChart({ height = 220 }) {
  return (
    <div style={{
      height,
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      color: C.textMuted, gap: '0.5rem',
    }}>
      <span style={{ fontSize: '2rem' }}>📊</span>
      <span style={{ fontSize: '0.875rem' }}>Sin datos disponibles</span>
    </div>
  );
}

function KpiCard({ label, value, accent, sub }) {
  return (
    <div style={{
      background: C.white,
      border: `1px solid ${C.border}`,
      borderLeft: `4px solid ${accent}`,
      borderRadius: '10px',
      padding: '1.1rem 1.25rem',
      boxShadow: '0 1px 4px rgba(0,0,0,0.07)',
    }}>
      <div style={{
        fontSize: '0.7rem', color: C.textSub,
        textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '0.4rem',
      }}>
        {label}
      </div>
      <div style={{ fontSize: '1.9rem', fontWeight: 700, color: accent, lineHeight: 1.1 }}>
        {value}
      </div>
      {sub && (
        <div style={{ fontSize: '0.73rem', color: C.textMuted, marginTop: '0.3rem' }}>{sub}</div>
      )}
    </div>
  );
}

function Card({ children, style }) {
  return (
    <div style={{
      background: C.white,
      border: `1px solid ${C.border}`,
      borderRadius: '10px',
      padding: '1.4rem',
      boxShadow: '0 1px 4px rgba(0,0,0,0.07)',
      ...style,
    }}>
      {children}
    </div>
  );
}

function CardTitle({ children, sub }) {
  return (
    <h3 style={{ margin: '0 0 1rem', fontSize: '0.95rem', fontWeight: 600, color: C.text }}>
      {children}
      {sub && (
        <span style={{ marginLeft: '0.5rem', fontSize: '0.75rem', fontWeight: 400, color: C.textMuted }}>
          {sub}
        </span>
      )}
    </h3>
  );
}

function SectionLabel({ children }) {
  return (
    <div style={{
      fontSize: '0.7rem', fontWeight: 700, color: C.textMuted,
      textTransform: 'uppercase', letterSpacing: '0.1em',
      margin: '0.25rem 0 0.75rem',
      paddingLeft: '2px',
    }}>
      {children}
    </div>
  );
}

function SkeletonDashboard() {
  const pulse = {
    background: 'linear-gradient(90deg,#e8e8e8 25%,#f5f5f5 50%,#e8e8e8 75%)',
    backgroundSize: '200% 100%',
    animation: 'skPulse 1.4s ease-in-out infinite',
    borderRadius: '10px',
  };
  return (
    <>
      <style>{`@keyframes skPulse{0%{background-position:200% 0}100%{background-position:-200% 0}}`}</style>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(160px,1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        {[1,2,3,4,5,6].map(i => <div key={i} style={{ ...pulse, height: '88px' }} />)}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '5fr 7fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        <div style={{ ...pulse, height: '308px' }} />
        <div style={{ ...pulse, height: '308px' }} />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '7fr 5fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        <div style={{ ...pulse, height: '260px' }} />
        <div style={{ ...pulse, height: '260px' }} />
      </div>
      <div style={{ ...pulse, height: '72px', marginBottom: '1.5rem' }} />
      <div style={{ ...pulse, height: '260px' }} />
    </>
  );
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function MetricsPage() {
  const [metrics,      setMetrics]     = useState(null);
  const [tickets,      setTickets]     = useState(null);
  const [escalas,      setEscalas]     = useState(null);
  const [error,        setError]       = useState(null);
  const [loadedAt,     setLoadedAt]    = useState(null);

  useEffect(() => {
    window.scrollTo(0, 0);

    // Chat metrics — original, no se toca
    const fetchChat = fetch('http://localhost:3000/api/cognitive/metrics')
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); });

    // Tickets — nuevo, fallo aislado
    const fetchTickets = fetch('http://localhost:3000/api/tickets/metricas')
      .then(r => r.ok ? r.json() : null)
      .catch(() => null);

    // Escalamientos — nuevo, fallo aislado
    const fetchEscalas = fetch('http://localhost:3000/api/escalamientos/metricas')
      .then(r => r.ok ? r.json() : null)
      .catch(() => null);

    fetchChat
      .then(data => { setMetrics(data); setLoadedAt(new Date()); })
      .catch(err  => setError(err.message));

    fetchTickets.then(setTickets);
    fetchEscalas.then(setEscalas);
  }, []);

  const page = {
    fontFamily: "'Inter','Segoe UI',system-ui,sans-serif",
    background: C.pageBg,
    minHeight: '100vh',
    padding: '1.5rem 2rem',
    boxSizing: 'border-box',
  };

  // ── Error ──────────────────────────────────────────────────────────────────
  if (error) return (
    <div style={page}>
      <div style={{
        background: '#ffebee', border: '1px solid #ef9a9a', color: '#c62828',
        padding: '1.25rem 1.5rem', borderRadius: '10px', maxWidth: '520px',
        fontSize: '0.9rem', lineHeight: 1.6,
      }}>
        <strong>Error al cargar métricas:</strong> {error}
        <br />
        <small style={{ color: '#e57373' }}>Verifica que NestJS esté corriendo en localhost:3000</small>
      </div>
    </div>
  );

  // ── Loading ────────────────────────────────────────────────────────────────
  if (!metrics) return (
    <div style={page}>
      <div style={{
        background: C.primary, borderRadius: '10px',
        padding: '1.4rem 2rem', marginBottom: '1.5rem',
      }}>
        <h2 style={{ margin: 0, color: '#fff', fontSize: '1.4rem', fontWeight: 700 }}>
          Dashboard de Métricas
        </h2>
        <p style={{ margin: '0.2rem 0 0', color: 'rgba(255,255,255,0.75)', fontSize: '0.85rem' }}>
          Cargando datos…
        </p>
      </div>
      <SkeletonDashboard />
    </div>
  );

  // ── Computed ───────────────────────────────────────────────────────────────
  const negativePct = metrics.total > 0
    ? Math.round(
        (metrics.sentimentCounts.find(x => x.sentiment === 'negative')?.count ?? 0)
        / metrics.total * 100
      )
    : 0;

  const ultimos8 = metrics.ultimos.slice(0, 8);

  const ticketsPendientes  = tickets ? tickets.total - tickets.abiertos : null;
  const escalaPendientes   = escalas?.pendientes ?? null;

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div style={page}>

      {/* HEADER */}
      <div style={{
        background: `linear-gradient(135deg, ${C.dark} 0%, ${C.primary} 100%)`,
        color: '#fff',
        padding: '1.4rem 2rem',
        borderRadius: '10px',
        marginBottom: '1.5rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
      }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.4rem', fontWeight: 700, letterSpacing: '-0.01em' }}>
            Dashboard de Métricas
          </h2>
          <p style={{ margin: '0.2rem 0 0', opacity: 0.8, fontSize: '0.85rem' }}>
            Sistema Agentic PluriOne — Interacciones, Tickets y Escalamientos
          </p>
        </div>
        {loadedAt && (
          <div style={{ fontSize: '0.75rem', opacity: 0.75, textAlign: 'right', paddingTop: '0.15rem' }}>
            Actualizado<br />{formatDate(loadedAt)}
          </div>
        )}
      </div>

      {/* KPI ROW — 6 cards */}
      <SectionLabel>Resumen general</SectionLabel>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(155px, 1fr))',
        gap: '1rem',
        marginBottom: '1.5rem',
      }}>
        <KpiCard label="Total interacciones" value={metrics.total} accent={C.primary} />
        <KpiCard label="Sentimiento negativo" value={`${negativePct}%`} accent={C.negative} sub="del total de mensajes" />
        <KpiCard label="Confianza promedio" value={`${(metrics.avgConfidence * 100).toFixed(1)}%`} accent={C.medium} sub="clasificador de intención" />
        <KpiCard
          label="Tickets clasificados"
          value={tickets ? tickets.total : '—'}
          accent={C.info}
          sub={tickets ? `${tickets.abiertos} abiertos` : 'cargando…'}
        />
        <KpiCard
          label="Tickets cerrados"
          value={tickets ? (tickets.total - tickets.abiertos) : '—'}
          accent={C.positive}
          sub="estado completado"
        />
        <KpiCard
          label="Escalamientos pendientes"
          value={escalaPendientes !== null ? escalaPendientes : '—'}
          accent={escalaPendientes > 0 ? C.warning : C.positive}
          sub={escalas ? `${escalas.total} total` : 'cargando…'}
        />
      </div>

      {/* FILA 1 — Chat charts */}
      <SectionLabel>Chat — Análisis de conversaciones</SectionLabel>
      <div style={{
        display: 'grid',
        gridTemplateColumns: '5fr 7fr',
        gap: '1.5rem',
        marginBottom: '1.5rem',
        alignItems: 'start',
      }}>
        {/* Pie — sentimientos */}
        <Card>
          <CardTitle>Distribución de Sentimientos</CardTitle>
          {metrics.sentimentCounts.length === 0 ? <EmptyChart /> : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={metrics.sentimentCounts}
                  dataKey="count"
                  nameKey="sentiment"
                  cx="50%" cy="45%"
                  outerRadius={88} innerRadius={44}
                >
                  {metrics.sentimentCounts.map((entry, i) => (
                    <Cell key={i} fill={badgeColor(entry.sentiment)} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(v, n) => [v, n]}
                  contentStyle={{ borderRadius: '8px', fontSize: '0.85rem' }}
                />
                <Legend
                  verticalAlign="bottom" height={36}
                  formatter={v => v.charAt(0).toUpperCase() + v.slice(1)}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Card>

        {/* Bar — intenciones */}
        <Card>
          <CardTitle>Intenciones Más Frecuentes</CardTitle>
          {metrics.intentCounts.length === 0 ? <EmptyChart /> : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={metrics.intentCounts} margin={{ bottom: 48, left: -10, right: 8 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                <XAxis
                  dataKey="intent"
                  tickFormatter={v => truncate(v, 14)}
                  angle={-30} textAnchor="end"
                  interval={0}
                  tick={{ fontSize: 11, fill: C.textSub }}
                />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: C.textSub }} />
                <Tooltip
                  labelFormatter={l => l}
                  formatter={v => [v, 'Mensajes']}
                  contentStyle={{ borderRadius: '8px', fontSize: '0.85rem' }}
                />
                <Bar dataKey="count" name="Mensajes" radius={[4, 4, 0, 0]}>
                  {metrics.intentCounts.map((_, i) => (
                    <Cell key={i} fill={INTENT_COLORS[i % INTENT_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>

      {/* FILA 2 — Tickets charts */}
      <SectionLabel>Tickets — Clasificación inteligente (M10)</SectionLabel>
      <div style={{
        display: 'grid',
        gridTemplateColumns: '7fr 5fr',
        gap: '1.5rem',
        marginBottom: '1.5rem',
        alignItems: 'start',
      }}>
        {/* HorizontalBar — categorías */}
        <Card>
          <CardTitle>Tickets por Categoría</CardTitle>
          {!tickets || tickets.porCategoria.length === 0 ? <EmptyChart height={200} /> : (
            <ResponsiveContainer width="100%" height={Math.max(180, tickets.porCategoria.length * 38)}>
              <BarChart
                data={tickets.porCategoria}
                layout="vertical"
                margin={{ left: 8, right: 24, top: 4, bottom: 4 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f0f0f0" />
                <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11, fill: C.textSub }} />
                <YAxis
                  type="category" dataKey="categoria"
                  tick={{ fontSize: 11, fill: C.textSub }}
                  width={110}
                />
                <Tooltip
                  formatter={v => [v, 'Tickets']}
                  contentStyle={{ borderRadius: '8px', fontSize: '0.85rem' }}
                />
                <Bar dataKey="count" name="Tickets" fill={CATEGORIA_COLOR} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        {/* Pie — prioridad */}
        <Card>
          <CardTitle>Tickets por Prioridad</CardTitle>
          {!tickets || tickets.porPrioridad.length === 0 ? <EmptyChart height={200} /> : (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={tickets.porPrioridad}
                  dataKey="count"
                  nameKey="prioridad"
                  cx="50%" cy="42%"
                  outerRadius={72} innerRadius={32}
                >
                  {tickets.porPrioridad.map((entry, i) => (
                    <Cell key={i} fill={PRIORIDAD_COLORS[entry.prioridad] ?? C.neutral} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(v, n) => [v, n]}
                  contentStyle={{ borderRadius: '8px', fontSize: '0.85rem' }}
                />
                <Legend
                  verticalAlign="bottom" height={30}
                  formatter={v => v.charAt(0).toUpperCase() + v.slice(1)}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>

      {/* ESCALAMIENTOS RESUMEN */}
      <SectionLabel>Escalamientos — Solicitudes a agente humano (M5)</SectionLabel>
      <Card style={{ marginBottom: '1.5rem' }}>
        <CardTitle>Estado de Escalamientos</CardTitle>
        {!escalas ? (
          <div style={{ color: C.textMuted, fontSize: '0.875rem' }}>Sin datos disponibles</div>
        ) : (
          <div style={{ display: 'flex', gap: '2.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
            {[
              { label: 'Total solicitudes', value: escalas.total,     color: C.primary  },
              { label: 'Pendientes',         value: escalas.pendientes, color: C.warning  },
              { label: 'Atendidos',          value: escalas.atendidos,  color: C.positive },
            ].map(item => (
              <div key={item.label} style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '2rem', fontWeight: 700, color: item.color, lineHeight: 1 }}>
                  {item.value}
                </div>
                <div style={{ fontSize: '0.73rem', color: C.textSub, textTransform: 'uppercase', letterSpacing: '0.06em', marginTop: '0.3rem' }}>
                  {item.label}
                </div>
              </div>
            ))}
            {escalas.total > 0 && (
              <div style={{
                marginLeft: 'auto',
                background: escalas.pendientes > 0 ? '#fff3e0' : C.light,
                border: `1px solid ${escalas.pendientes > 0 ? '#ffcc80' : '#c8e6c9'}`,
                color: escalas.pendientes > 0 ? C.warning : C.primary,
                borderRadius: '8px',
                padding: '0.5rem 1rem',
                fontSize: '0.82rem',
                fontWeight: 600,
              }}>
                {escalas.pendientes > 0
                  ? `${Math.round(escalas.pendientes / escalas.total * 100)}% pendiente de atención`
                  : 'Todos los escalamientos atendidos'}
              </div>
            )}
          </div>
        )}
      </Card>

      {/* TABLE */}
      <SectionLabel>Chat — Historial reciente</SectionLabel>
      <Card>
        <CardTitle sub="(8 más recientes)">Últimas Interacciones</CardTitle>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr>
                {['Mensaje', 'Intención', 'Sentimiento', 'Emoción', 'Fecha'].map(h => (
                  <th key={h} style={{
                    background: C.light, color: C.primary,
                    textAlign: 'left', padding: '0.65rem 0.85rem',
                    borderBottom: '2px solid #c8e6c9',
                    fontWeight: 600, fontSize: '0.78rem',
                    textTransform: 'uppercase', letterSpacing: '0.05em',
                    whiteSpace: 'nowrap',
                  }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ultimos8.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ padding: '2.5rem', textAlign: 'center', color: C.textMuted }}>
                    <div style={{ fontSize: '1.5rem', marginBottom: '0.4rem' }}>📭</div>
                    Sin interacciones registradas
                  </td>
                </tr>
              )}
              {ultimos8.map((row, idx) => (
                <tr key={row.event_id} style={{ background: idx % 2 === 0 ? C.white : '#fafafa' }}>
                  <td style={{ padding: '0.65rem 0.85rem', color: C.text, borderBottom: '1px solid #f0f0f0', maxWidth: '280px' }}>
                    {truncate(row.raw_text, 48)}
                  </td>
                  <td style={{ padding: '0.65rem 0.85rem', borderBottom: '1px solid #f0f0f0' }}>
                    <code style={{
                      background: C.light, color: C.dark,
                      padding: '2px 7px', borderRadius: '4px',
                      fontSize: '0.78rem', fontFamily: 'monospace',
                    }}>
                      {row.intent}
                    </code>
                  </td>
                  <td style={{ padding: '0.65rem 0.85rem', borderBottom: '1px solid #f0f0f0' }}>
                    <span style={{
                      display: 'inline-block', padding: '2px 9px', borderRadius: '12px',
                      fontSize: '0.75rem', fontWeight: 600, color: '#fff',
                      background: badgeColor(row.sentiment),
                      textTransform: 'capitalize',
                    }}>
                      {row.sentiment}
                    </span>
                  </td>
                  <td style={{ padding: '0.65rem 0.85rem', color: C.textSub, borderBottom: '1px solid #f0f0f0', fontSize: '0.82rem' }}>
                    {row.emotion ?? '—'}
                  </td>
                  <td style={{ padding: '0.65rem 0.85rem', color: C.textMuted, borderBottom: '1px solid #f0f0f0', fontSize: '0.78rem', whiteSpace: 'nowrap' }}>
                    {formatDate(row.timestamp)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

    </div>
  );
}
