import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import { promisify } from 'util';

const execAsync = promisify(exec);

export const revalidate = 0;

export async function GET() {
  try {
    const backendDir = path.join(process.cwd(), '../backend');
    const { stdout } = await execAsync('uv run python src/db.py get_calls_history_json', {
      cwd: backendDir,
    });
    const history = JSON.parse(stdout.trim());
    return NextResponse.json(history);
  } catch (error) {
    console.error('Failed to fetch call history:', error);
    return NextResponse.json([], { status: 500 });
  }
}
