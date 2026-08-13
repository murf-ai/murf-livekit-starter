import { NextResponse } from 'next/server';
import path from 'path';
import sqlite3 from 'sqlite3';

export const revalidate = 0;
export const dynamic = 'force-dynamic';

function getLatestStats(dbPath: string): Promise<any> {
  return new Promise((resolve) => {
    const db = new sqlite3.Database(dbPath, sqlite3.OPEN_READONLY, (err) => {
      if (err) {
        return resolve({ total_calls: 0, successful_calls: 0, failed_calls: 0, records: [] });
      }
    });

    db.serialize(() => {
      db.all(
        `SELECT 
           COUNT(*) as total_calls,
           SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) as successful_calls,
           SUM(CASE WHEN outcome = 'failed' THEN 1 ELSE 0 END) as failed_calls
         FROM call_outcomes`,
        [],
        (err, countRows: any[]) => {
          if (err) {
            db.close();
            return resolve({ total_calls: 0, successful_calls: 0, failed_calls: 0, records: [] });
          }

          const total = countRows[0]?.total_calls || 0;
          const success = countRows[0]?.successful_calls || 0;
          const failed = countRows[0]?.failed_calls || 0;

          db.all(
            `SELECT call_id, timestamp, outcome, outcome_reason 
             FROM call_outcomes 
             ORDER BY timestamp DESC 
             LIMIT 50`,
            [],
            (err, records: any[]) => {
              db.close();
              resolve({
                total_calls: total,
                successful_calls: success,
                failed_calls: failed,
                records: records || [],
              });
            }
          );
        }
      );
    });
  });
}

export async function GET(): Promise<Response> {
  const dbPath = path.resolve(process.cwd(), '../backend/src/caller_memory.db');
  let lastStatsJson = '';

  const stream = new ReadableStream({
    async start(controller) {
      const encoder = new TextEncoder();

      const sendStats = async () => {
        try {
          const stats = await getLatestStats(dbPath);
          const currentJson = JSON.stringify(stats);
          if (currentJson !== lastStatsJson) {
            lastStatsJson = currentJson;
            controller.enqueue(encoder.encode(`data: ${currentJson}\n\n`));
          }
        } catch (e) {
          // ignore error
        }
      };

      // Send initial stats immediately
      await sendStats();

      // Check DB every 1s for instant real-time pushes when new call outcomes land
      const interval = setInterval(async () => {
        await sendStats();
      }, 1000);

      // Clean up interval when client disconnects
      return () => {
        clearInterval(interval);
      };
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      'Connection': 'keep-alive',
    },
  });
}
