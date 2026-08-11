'use client';

import { useState } from 'react';
import { PhoneCallIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';

type UiState =
  | 'Ready'
  | 'Calling...'
  | 'Ringing...'
  | 'Connecting...'
  | 'Connected'
  | 'Conversation in progress'
  | 'Call completed'
  | 'Busy'
  | 'No answer'
  | 'Voicemail'
  | 'Call ended immediately'
  | 'Failed';

const statusLabels: Record<string, UiState> = {
  REQUESTED: 'Calling...',
  INITIATED: 'Calling...',
  RINGING: 'Ringing...',
  ANSWERED: 'Connected',
  CONNECTING_TO_AGENT: 'Connecting...',
  CONNECTED: 'Connected',
  IN_PROGRESS: 'Conversation in progress',
  COMPLETED: 'Call completed',
  BUSY: 'Busy',
  NO_ANSWER: 'No answer',
  VOICEMAIL: 'Voicemail',
  FAILED: 'Failed',
  USER_HANGUP: 'Call ended immediately',
  OPTED_OUT: 'Call completed',
};

const order = {
  customerName: 'Shivam',
  orderId: 'ORD-1001',
  items: [
    {
      name: 'Amul Taaza Milk',
      quantity: 1,
      unit: '1 litre pouch',
      seller: 'Sharma General Store',
      unitPrice: 68,
    },
    {
      name: 'Britannia Brown Bread',
      quantity: 1,
      unit: '400 gram loaf',
      seller: 'Sharma General Store',
      unitPrice: 45,
    },
    {
      name: 'Homemade Mango Pickle',
      quantity: 1,
      unit: '500 gram jar',
      seller: 'Asha Foods',
      unitPrice: 240,
    },
  ],
  deliveryTime: 'Today, 6 PM-8 PM',
};

const orderTotal = order.items.reduce((total, item) => total + item.quantity * item.unitPrice, 0);

export function OutboundCallCard() {
  const [state, setState] = useState<UiState>('Ready');
  const [error, setError] = useState('');
  const [orderConfirmed, setOrderConfirmed] = useState(false);
  const [retryRule, setRetryRule] = useState('');

  function trackCall(callSid: string) {
    const poll = window.setInterval(async () => {
      const response = await fetch(`/api/outbound-call?callSid=${encodeURIComponent(callSid)}`);
      if (!response.ok) return;
      const result = await response.json();
      const label = statusLabels[result.state];
      if (label) setState(label);
      setOrderConfirmed(Boolean(result.orderConfirmed));
      setRetryRule(result.retryRule ?? '');
      if (
        [
          'COMPLETED',
          'BUSY',
          'NO_ANSWER',
          'VOICEMAIL',
          'FAILED',
          'USER_HANGUP',
          'OPTED_OUT',
        ].includes(result.state)
      ) {
        window.clearInterval(poll);
      }
    }, 1500);
  }

  async function callCustomer() {
    setError('');
    setOrderConfirmed(false);
    setRetryRule('');
    setState('Calling...');
    const ringingTimer = window.setTimeout(() => setState('Ringing...'), 1000);
    try {
      const response = await fetch('/api/outbound-call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customerName: order.customerName,
          orderId: order.orderId,
          orderItems: order.items.map(
            (item) =>
              `${item.quantity} × ${item.name}, ${item.unit}, ₹${item.unitPrice} each, ` +
              `subtotal ₹${item.quantity * item.unitPrice}, seller ${item.seller}`
          ),
          orderTotal,
          deliveryTime: order.deliveryTime,
        }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error ?? 'Outbound call failed');
      setState(statusLabels[result.state] ?? 'Calling...');
      trackCall(result.callSid);
    } catch (caught) {
      setState('Failed');
      setError(caught instanceof Error ? caught.message : 'Outbound call failed');
    } finally {
      window.clearTimeout(ringingTimer);
    }
  }

  return (
    <section className="mx-auto mt-10 max-w-5xl px-5">
      <div className="rounded-[2rem] border border-emerald-200 bg-white/90 p-6 shadow-lg dark:border-emerald-900 dark:bg-stone-900/90">
        <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-center">
          <div>
            <p className="font-mono text-xs font-bold tracking-[0.18em] text-emerald-700 uppercase">
              Local Commerce
            </p>
            <h2 className="mt-2 text-xl font-bold">Outbound order confirmation</h2>
            <p className="mt-2 text-sm text-stone-600 dark:text-stone-300">
              Customer: {order.customerName} · Order: {order.orderId}
            </p>
            <div className="mt-4 overflow-hidden rounded-xl border border-stone-200 dark:border-stone-700">
              {order.items.map((item) => (
                <div
                  key={item.name}
                  className="border-b border-stone-200 px-4 py-3 last:border-b-0 dark:border-stone-700"
                >
                  <div className="flex justify-between gap-4 text-sm font-semibold">
                    <span>
                      {item.quantity} × {item.name}
                    </span>
                    <span>₹{item.quantity * item.unitPrice}</span>
                  </div>
                  <p className="mt-1 text-xs text-stone-500 dark:text-stone-400">
                    {item.unit} · ₹{item.unitPrice} each · {item.seller}
                  </p>
                </div>
              ))}
            </div>
            <div className="mt-3 flex justify-between text-base font-bold">
              <span>Order total</span>
              <span>₹{orderTotal}</span>
            </div>
            <p className="mt-2 text-sm text-stone-600 dark:text-stone-300">
              Delivery window: {order.deliveryTime}
            </p>
            <p className="mt-2 text-sm font-semibold text-emerald-700" aria-live="polite">
              Status: {state}
            </p>
            {orderConfirmed && (
              <p className="mt-1 text-sm font-bold text-emerald-700" aria-live="polite">
                ✓ Order confirmed
              </p>
            )}
            {retryRule && state !== 'Ready' && (
              <p className="mt-1 text-xs text-stone-500 dark:text-stone-400">{retryRule}</p>
            )}
            {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
          </div>
          <Button
            size="lg"
            onClick={callCustomer}
            disabled={state === 'Calling...' || state === 'Ringing...'}
            className="rounded-2xl bg-emerald-700 text-white hover:bg-emerald-800"
          >
            <PhoneCallIcon className="size-5" /> Call Customer
          </Button>
        </div>
      </div>
    </section>
  );
}
