import { NextRequest, NextResponse } from 'next/server';
import {
  type OutboundCallRequest,
  placeOutboundCall,
  recoverCallStatus,
} from '@/lib/outbound-call';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const callSid = request.nextUrl.searchParams.get('callSid');
  if (!callSid) return NextResponse.json({ error: 'callSid is required' }, { status: 400 });
  try {
    return NextResponse.json(await recoverCallStatus(callSid));
  } catch {
    return NextResponse.json({ error: 'Call not found' }, { status: 404 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as Partial<OutboundCallRequest>;
    const result = await placeOutboundCall({
      customerName: process.env.ORDER_CUSTOMER_NAME ?? body.customerName ?? '',
      orderId: process.env.ORDER_ID ?? body.orderId ?? '',
      orderItems:
        process.env.ORDER_ITEMS?.split('|').map((item) => item.trim()) ?? body.orderItems ?? [],
      orderTotal: Number(process.env.ORDER_TOTAL_INR ?? body.orderTotal ?? 0),
      deliveryTime: process.env.ORDER_DELIVERY_TIME ?? body.deliveryTime ?? '',
    });
    return NextResponse.json(result, { status: 201 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Outbound call failed';
    console.error(JSON.stringify({ event: 'call_failed', reason: message }));
    return NextResponse.json({ error: message, state: 'FAILED' }, { status: 400 });
  }
}
