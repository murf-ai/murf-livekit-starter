import { NextResponse } from 'next/server';
import path from 'path';
import sqlite3 from 'sqlite3';

export const revalidate = 0;

export async function GET(): Promise<NextResponse> {
  try {
    const dbPath = path.resolve(process.cwd(), '../backend/src/caller_memory.db');

    return new Promise<NextResponse>((resolve) => {
      const db = new sqlite3.Database(dbPath, sqlite3.OPEN_READONLY, (err) => {
        if (err) {
          // If DB file doesn't exist yet, return zeroed stats
          return resolve(
            NextResponse.json({
              total_calls: 0,
              successful_calls: 0,
              failed_calls: 0,
              records: [],
            })
          );
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
              return resolve(
                NextResponse.json({
                  total_calls: 0,
                  successful_calls: 0,
                  failed_calls: 0,
                  records: [],
                })
              );
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
                return resolve(
                  NextResponse.json({
                    total_calls: total,
                    successful_calls: success,
                    failed_calls: failed,
                    records: records || [],
                  })
                );
              }
            );
          }
        );
      });
    });
  } catch (error: any) {
    return NextResponse.json(
      { total_calls: 0, successful_calls: 0, failed_calls: 0, records: [] },
      { status: 500 }
    );
  }
}
