import { NextRequest, NextResponse } from 'next/server';
import { confirmOrder } from '@/lib/outbound-call';

export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  const expected = process.env.LIVEKIT_API_SECRET;
  const supplied = request.headers.get('authorization')?.replace(/^Bearer\s+/i, '');
  if (!expected || supplied !== expected) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  const body = await request.json();
  const orderId = typeof body.orderId === 'string' ? body.orderId.trim() : '';
  if (!orderId) return NextResponse.json({ error: 'orderId is required' }, { status: 400 });
  const record = await confirmOrder(orderId);
  if (!record) return NextResponse.json({ error: 'Active order call not found' }, { status: 404 });
  return NextResponse.json(record);
}
