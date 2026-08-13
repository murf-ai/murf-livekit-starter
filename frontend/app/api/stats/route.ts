import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import { promisify } from 'util';

const execAsync = promisify(exec);

export const revalidate = 0;

export async function GET() {
  try {
    // Navigate to the backend folder relative to next.js root
    const backendDir = path.join(process.cwd(), '../backend');

    // Execute get_call_stats_json CLI command via uv
    const { stdout } = await execAsync('uv run python src/db.py get_call_stats_json', {
      cwd: backendDir,
    });

    const stats = JSON.parse(stdout.trim());
    return NextResponse.json(stats);
  } catch (error) {
    console.error('Failed to fetch call stats:', error);
    return NextResponse.json(
      { total: 0, successful: 0, failed: 0, error: String(error) },
      { status: 500 }
    );
  }
}
