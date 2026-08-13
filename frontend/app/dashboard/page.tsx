'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';

interface CallRecord {
  call_id: string;
  timestamp: string;
  outcome: 'success' | 'failed' | string;
  outcome_reason: string;
}

interface StatsData {
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  records: CallRecord[];
}

export default function DashboardPage() {
  const [stats, setStats] = useState<StatsData>({
    total_calls: 0,
    successful_calls: 0,
    failed_calls: 0,
    records: [],
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [lastRefreshed, setLastRefreshed] = useState<string>('');

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch('/api/stats', { cache: 'no-store' });
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to fetch call analytics stats:', err);
    } finally {
      setLoading(false);
      setLastRefreshed(new Date().toLocaleTimeString());
    }
  }, []);

  const [wsConnected, setWsConnected] = useState<boolean>(false);

  useEffect(() => {
    fetchStats();

    let ws: WebSocket | null = null;
    let eventSource: EventSource | null = null;

    // 1. Try WebSocket Connection (ws://localhost:8765)
    try {
      ws = new WebSocket('ws://localhost:8765');
      ws.onopen = () => {
        setWsConnected(true);
        console.log('[WS FRONTEND] Connected to ws://localhost:8765');
      };

      ws.onmessage = (event) => {
        const t_recv = new Date().toISOString();
        console.log(`[TIMESTAMP DEBUG 1e] Frontend received WebSocket message at ${t_recv}:`, event.data);
        fetchStats().then(() => {
          const t_dom = new Date().toISOString();
          console.log(`[TIMESTAMP DEBUG 1f] Frontend finished updating DOM state at ${t_dom}`);
        });
      };

      ws.onerror = () => {
        setWsConnected(false);
      };

      ws.onclose = () => {
        setWsConnected(false);
      };
    } catch (e) {
      setWsConnected(false);
    }

    // 2. Real-time SSE Push Stream Connection
    try {
      eventSource = new EventSource('/api/stats/stream');

      eventSource.onmessage = (event) => {
        try {
          const t_recv = new Date().toISOString();
          console.log(`[TIMESTAMP DEBUG 1e] Frontend received SSE stream message at ${t_recv}:`, event.data);
          const data = JSON.parse(event.data);
          setStats(data);
          setLoading(false);
          setLastRefreshed(new Date().toLocaleTimeString());
          const t_dom = new Date().toISOString();
          console.log(`[TIMESTAMP DEBUG 1f] Frontend finished updating DOM state at ${t_dom}`);
        } catch (e) {
          // ignore error
        }
      };

      eventSource.onerror = () => {
        eventSource?.close();
      };
    } catch (e) {
      // ignore
    }

    // 3. Fallback poll (30s interval)
    const interval = setInterval(fetchStats, 30000);

    return () => {
      ws?.close();
      eventSource?.close();
      clearInterval(interval);
    };
  }, [fetchStats]);

  return (
    <div style={{ padding: '32px', fontFamily: 'system-ui, -apple-system, sans-serif', backgroundColor: '#0f172a', minHeight: '100vh', color: '#f8fafc' }}>
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>
        
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
          <div>
            <h1 style={{ fontSize: '28px', fontWeight: '700', margin: '0 0 8px 0', color: '#ffffff' }}>
              FinSafe Call Analytics
            </h1>
            <p style={{ margin: 0, color: '#94a3b8', fontSize: '14px' }}>
              Real-time call outcome tracking & metrics
            </p>
          </div>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <Link
              href="/"
              style={{
                padding: '10px 18px',
                backgroundColor: '#1e293b',
                color: '#cbd5e1',
                border: '1px solid #334155',
                borderRadius: '6px',
                fontWeight: '600',
                textDecoration: 'none',
                fontSize: '14px',
              }}
            >
              ← Back to Assistant
            </Link>
            <button
              onClick={fetchStats}
              style={{
                padding: '10px 18px',
                backgroundColor: '#2563eb',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                fontWeight: '600',
                cursor: 'pointer',
                fontSize: '14px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
              }}
            >
              Refresh Now
            </button>
          </div>
        </div>

        {/* 3 Live Stat Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px', marginBottom: '32px' }}>
          {/* Card 1: Total Calls */}
          <div style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
            <span style={{ fontSize: '14px', color: '#94a3b8', fontWeight: '500' }}>Total Calls</span>
            <div style={{ fontSize: '36px', fontWeight: '700', marginTop: '8px', color: '#ffffff' }}>
              {loading ? '...' : stats.total_calls}
            </div>
          </div>

          {/* Card 2: Successful Calls */}
          <div style={{ backgroundColor: '#1e293b', border: '1px solid #166534', borderRadius: '12px', padding: '24px' }}>
            <span style={{ fontSize: '14px', color: '#4ade80', fontWeight: '500' }}>Successful Calls</span>
            <div style={{ fontSize: '36px', fontWeight: '700', marginTop: '8px', color: '#4ade80' }}>
              {loading ? '...' : stats.successful_calls}
            </div>
          </div>

          {/* Card 3: Failed Calls */}
          <div style={{ backgroundColor: '#1e293b', border: '1px solid #991b1b', borderRadius: '12px', padding: '24px' }}>
            <span style={{ fontSize: '14px', color: '#f87171', fontWeight: '500' }}>Failed Calls</span>
            <div style={{ fontSize: '36px', fontWeight: '700', marginTop: '8px', color: '#f87171' }}>
              {loading ? '...' : stats.failed_calls}
            </div>
          </div>
        </div>

        {/* Call Logs Table */}
        <div style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '18px', fontWeight: '600', margin: 0, color: '#ffffff' }}>
              Recent Call Logs
            </h2>
            <span style={{ fontSize: '12px', color: '#64748b' }}>
              Real-time SSE stream active • 30s fallback • Last updated: {lastRefreshed}
            </span>
          </div>

          {stats.records.length === 0 ? (
            <p style={{ color: '#64748b', fontSize: '14px', margin: '20px 0', textAlign: 'center' }}>
              No recorded calls yet. Make a call to see live outcome data here.
            </p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
                    <th style={{ padding: '12px 8px' }}>Call ID</th>
                    <th style={{ padding: '12px 8px' }}>Timestamp</th>
                    <th style={{ padding: '12px 8px' }}>Outcome</th>
                    <th style={{ padding: '12px 8px' }}>Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.records.map((rec, index) => (
                    <tr key={rec.call_id || index} style={{ borderBottom: '1px solid #334155' }}>
                      <td style={{ padding: '12px 8px', fontFamily: 'monospace', color: '#cbd5e1' }}>
                        {rec.call_id}
                      </td>
                      <td style={{ padding: '12px 8px', color: '#94a3b8' }}>
                        {new Date(rec.timestamp).toLocaleString()}
                      </td>
                      <td style={{ padding: '12px 8px' }}>
                        <span
                          style={{
                            padding: '4px 10px',
                            borderRadius: '12px',
                            fontSize: '12px',
                            fontWeight: '600',
                            backgroundColor: rec.outcome === 'success' ? '#14532d' : '#7f1d1d',
                            color: rec.outcome === 'success' ? '#86efac' : '#fca5a5',
                          }}
                        >
                          {rec.outcome}
                        </span>
                      </td>
                      <td style={{ padding: '12px 8px', color: '#cbd5e1' }}>
                        {rec.outcome_reason}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
