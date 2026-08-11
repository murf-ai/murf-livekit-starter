import { AgentDispatchClient, RoomServiceClient, SipClient } from 'livekit-server-sdk';

export const CALL_STATES = [
  'REQUESTED',
  'RINGING',
  'ANSWERED',
  'CONNECTING_TO_AGENT',
  'CONNECTED',
  'IN_PROGRESS',
  'COMPLETED',
  'BUSY',
  'NO_ANSWER',
  'FAILED',
  'USER_HANGUP',
  'OPTED_OUT',
] as const;

export type CallState = (typeof CALL_STATES)[number];

export interface OutboundCallRequest {
  customerName: string;
  orderId: string;
  orderItems: string[];
  orderTotal: number;
  deliveryTime: string;
}

export interface OutboundCallResult {
  callSid: string;
  state: CallState;
}

type CallRecord = OutboundCallResult & {
  roomName: string;
  participantIdentity: string;
  orderId: string;
  attempt: number;
  orderConfirmed: boolean;
  retryAllowedAt: string | null;
  retryRule: string;
  connectedAt: string | null;
  updatedAt: string;
};

declare global {
  var mitraOutboundCalls: Map<string, CallRecord> | undefined;
}

const calls = globalThis.mitraOutboundCalls ?? new Map<string, CallRecord>();
globalThis.mitraOutboundCalls = calls;

function required(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) throw new Error(`Missing outbound configuration: ${name}`);
  return value;
}

function e164(value: string, name: string): string {
  if (!/^\+[1-9]\d{7,14}$/.test(value)) {
    throw new Error(`${name} must be an international E.164 phone number`);
  }
  return value;
}

function liveKitHost(): string {
  return required('LIVEKIT_URL').replace(/^wss:/, 'https:').replace(/^ws:/, 'http:');
}

function previousOrderCall(orderId: string): CallRecord | undefined {
  return [...calls.values()]
    .filter((call) => call.orderId === orderId)
    .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt))[0];
}

async function validateRetry(orderId: string): Promise<number> {
  let previous = previousOrderCall(orderId);
  if (!previous) return 1;
  previous = await recoverCallStatus(previous.callSid);
  if (previous.orderConfirmed) {
    throw new Error('Retry blocked: the order is already confirmed');
  }
  if (previous.state === 'OPTED_OUT') {
    throw new Error('Retry blocked: the customer opted out');
  }
  if (['COMPLETED', 'USER_HANGUP', 'FAILED'].includes(previous.state)) {
    return 1;
  }
  if (!['BUSY', 'NO_ANSWER'].includes(previous.state)) {
    throw new Error(`Retry blocked: ${previous.retryRule || 'the previous call is not retryable'}`);
  }
  if (previous.attempt >= 2) throw new Error('Retry blocked: the single controlled retry was used');
  const retryAt = previous.retryAllowedAt ? Date.parse(previous.retryAllowedAt) : Infinity;
  if (Date.now() < retryAt) throw new Error(`Retry available after ${previous.retryAllowedAt}`);
  return previous.attempt + 1;
}

function validateRequest(request: OutboundCallRequest): void {
  if (!request.customerName?.trim()) throw new Error('Customer name is required');
  if (!request.orderId?.trim()) throw new Error('Order ID is required');
  if (!request.deliveryTime?.trim()) throw new Error('Delivery time is required');
  if (!request.orderItems?.length) throw new Error('At least one order item is required');
  if (!Number.isFinite(request.orderTotal) || request.orderTotal <= 0) {
    throw new Error('Order total must be greater than zero');
  }
}

function failedState(error: unknown): CallState {
  const message =
    error instanceof Error ? error.message.toLowerCase() : String(error).toLowerCase();
  if (message.includes('busy')) return 'BUSY';
  if (
    message.includes('no answer') ||
    message.includes('no-answer') ||
    message.includes('timeout')
  ) {
    return 'NO_ANSWER';
  }
  return 'FAILED';
}

function applyFailure(record: CallRecord, state: CallState): CallRecord {
  const delayMinutes = state === 'BUSY' ? 5 : state === 'NO_ANSWER' ? 30 : 0;
  record.state = state;
  record.retryAllowedAt = delayMinutes
    ? new Date(Date.now() + delayMinutes * 60_000).toISOString()
    : null;
  record.retryRule =
    state === 'BUSY'
      ? 'Allow one manual retry after 5 minutes'
      : state === 'NO_ANSWER'
        ? 'Allow one manual retry after 30 minutes'
        : 'No automatic retry; inspect the SIP disconnect reason';
  record.updatedAt = new Date().toISOString();
  calls.set(record.callSid, record);
  return record;
}

export async function placeOutboundCall(request: OutboundCallRequest): Promise<OutboundCallResult> {
  validateRequest(request);
  const attempt = await validateRetry(request.orderId);
  const host = liveKitHost();
  const apiKey = required('LIVEKIT_API_KEY');
  const apiSecret = required('LIVEKIT_API_SECRET');
  const trunkId = required('LIVEKIT_SIP_OUTBOUND_TRUNK_ID');
  const destination = e164(required('TWILIO_TO_NUMBER'), 'TWILIO_TO_NUMBER');
  const callerId = e164(required('TWILIO_PHONE_NUMBER'), 'TWILIO_PHONE_NUMBER');
  const callSid = crypto.randomUUID();
  const roomName = `outbound-order-${callSid}`;
  const participantIdentity = `customer-${callSid}`;
  const record: CallRecord = {
    callSid,
    roomName,
    participantIdentity,
    orderId: request.orderId,
    attempt,
    state: 'REQUESTED',
    orderConfirmed: false,
    retryAllowedAt: null,
    retryRule: 'No retry while the call is active',
    connectedAt: null,
    updatedAt: new Date().toISOString(),
  };
  calls.set(callSid, record);

  const agentName = process.env.AGENT_NAME?.trim() || 'mitra';
  const dispatch = new AgentDispatchClient(host, apiKey, apiSecret);
  await dispatch.createDispatch(roomName, agentName);
  record.state = 'RINGING';
  record.updatedAt = new Date().toISOString();
  calls.set(callSid, record);
  console.info(JSON.stringify({ event: 'call_requested', callSid, roomName, agentName }));

  const sip = new SipClient(host, apiKey, apiSecret);
  try {
    const participant = await sip.createSipParticipant(trunkId, destination, roomName, {
      fromNumber: callerId,
      participantIdentity,
      participantName: request.customerName,
      participantMetadata: JSON.stringify({
        type: 'outbound_order_confirmation',
        customerName: request.customerName,
        orderId: request.orderId,
        orderItems: request.orderItems,
        orderTotal: request.orderTotal,
        deliveryTime: request.deliveryTime,
      }),
      playDialtone: true,
      ringingTimeout: 45,
      maxCallDuration: 300,
    });
    record.state = 'CONNECTED';
    record.connectedAt = new Date().toISOString();
    record.updatedAt = record.connectedAt;
    calls.set(callSid, record);
    console.info(
      JSON.stringify({
        event: 'sip_participant_connected',
        callSid,
        roomName,
        participantId: participant.participantId,
      })
    );
    return { callSid, state: record.state };
  } catch (error) {
    const state = failedState(error);
    applyFailure(record, state);
    console.error(
      JSON.stringify({
        event: 'sip_call_failed',
        callSid,
        roomName,
        state,
        reason: error instanceof Error ? error.message : String(error),
      })
    );
    return { callSid, state };
  }
}

export async function recoverCallStatus(callSid: string): Promise<CallRecord> {
  const record =
    calls.get(callSid) ??
    ({
      callSid,
      roomName: `outbound-order-${callSid}`,
      participantIdentity: `customer-${callSid}`,
      orderId: '',
      attempt: 1,
      state: 'REQUESTED',
      orderConfirmed: false,
      retryAllowedAt: null,
      retryRule: 'No automatic retry',
      connectedAt: null,
      updatedAt: new Date().toISOString(),
    } satisfies CallRecord);
  if (
    ['COMPLETED', 'BUSY', 'NO_ANSWER', 'FAILED', 'USER_HANGUP', 'OPTED_OUT'].includes(record.state)
  ) {
    if (record.retryRule === 'No retry while the call is active') {
      record.retryRule = record.orderConfirmed
        ? 'Order confirmed; no retry'
        : 'Call disconnected; no automatic retry';
    }
    return record;
  }
  const rooms = new RoomServiceClient(
    liveKitHost(),
    required('LIVEKIT_API_KEY'),
    required('LIVEKIT_API_SECRET')
  );
  let participants;
  try {
    participants = await rooms.listParticipants(record.roomName);
  } catch {
    record.state = 'COMPLETED';
    calls.set(callSid, record);
    return record;
  }
  const participant = participants.find((item) => item.identity === record.participantIdentity);
  if (participant) {
    record.state = record.state === 'CONNECTED' ? 'IN_PROGRESS' : record.state;
  } else {
    const duration = record.connectedAt ? Date.now() - Date.parse(record.connectedAt) : 6000;
    record.state = record.orderConfirmed
      ? 'COMPLETED'
      : duration <= 5000
        ? 'USER_HANGUP'
        : 'COMPLETED';
    record.retryRule = record.orderConfirmed
      ? 'Order confirmed; no retry'
      : 'Call disconnected; no automatic retry';
  }
  record.updatedAt = new Date().toISOString();
  calls.set(callSid, record);
  return record;
}

export async function confirmOrder(orderId: string): Promise<CallRecord | undefined> {
  let record = previousOrderCall(orderId);
  if (!record) {
    const rooms = new RoomServiceClient(
      liveKitHost(),
      required('LIVEKIT_API_KEY'),
      required('LIVEKIT_API_SECRET')
    );
    const activeRooms = await rooms.listRooms();
    for (const room of activeRooms) {
      if (!room.name.startsWith('outbound-order-')) continue;
      const participants = await rooms.listParticipants(room.name);
      const customer = participants.find((participant) => {
        try {
          return JSON.parse(participant.metadata || '{}').orderId === orderId;
        } catch {
          return false;
        }
      });
      if (!customer) continue;
      const callSid = room.name.replace(/^outbound-order-/, '');
      record = {
        callSid,
        roomName: room.name,
        participantIdentity: customer.identity,
        orderId,
        attempt: 1,
        state: 'IN_PROGRESS',
        orderConfirmed: false,
        retryAllowedAt: null,
        retryRule: 'No retry while the call is active',
        connectedAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      break;
    }
  }
  if (!record) return undefined;
  record.orderConfirmed = true;
  record.state = 'COMPLETED';
  record.retryRule = 'Order confirmed; no retry';
  record.updatedAt = new Date().toISOString();
  calls.set(record.callSid, record);
  console.info(JSON.stringify({ event: 'order_confirmed', callSid: record.callSid, orderId }));
  return record;
}
