import { NextResponse } from 'next/server';

const CATALOGUE_API_URL = process.env.CATALOGUE_API_URL ?? 'http://127.0.0.1:8001/catalogue';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const response = await fetch(CATALOGUE_API_URL, {
      cache: 'no-store',
      signal: AbortSignal.timeout(2500),
    });
    if (!response.ok) {
      throw new Error(`Catalogue API returned ${response.status}`);
    }
    return NextResponse.json(await response.json(), {
      headers: { 'Cache-Control': 'no-store' },
    });
  } catch (error) {
    console.error('Catalogue API unavailable', error);
    return NextResponse.json(
      {
        error:
          "The local catalogue is temporarily unavailable. Current products, prices, and stock can't be confirmed.",
      },
      { status: 503, headers: { 'Cache-Control': 'no-store' } }
    );
  }
}
