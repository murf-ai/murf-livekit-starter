'use client';

import { type ComponentProps } from 'react';
import { AnimatePresence } from 'motion/react';
import { type AgentState, type ReceivedMessage } from '@livekit/components-react';
import { AgentChatIndicator } from '@/components/agents-ui/agent-chat-indicator';
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from '@/components/ai-elements/conversation';
import { Message, MessageContent, MessageResponse } from '@/components/ai-elements/message';

/**
 * Props for the AgentChatTranscript component.
 */
export interface AgentChatTranscriptProps extends ComponentProps<'div'> {
  /**
   * The current state of the agent. When 'thinking', displays a loading indicator.
   */
  agentState?: AgentState;
  /**
   * Array of messages to display in the transcript.
   * @defaultValue []
   */
  messages?: ReceivedMessage[];
  /**
   * Additional CSS class names to apply to the conversation container.
   */
  className?: string;
}

/**
 * A chat transcript component that displays a conversation between the user and agent.
 * Shows messages with timestamps and origin indicators, plus a thinking indicator
 * when the agent is processing.
 *
 * @extends ComponentProps<'div'>
 *
 * @example
 * ```tsx
 * <AgentChatTranscript
 *   agentState={agentState}
 *   messages={chatMessages}
 * />
 * ```
 */
/** Hide internal locks / chain-of-thought that should never appear in the UI. */
function isInternalOrMetaMessage(text: string | undefined): boolean {
  if (!text) return true;
  const t = text.trim();
  if (
    t.startsWith('[[LANG_LOCK]]') ||
    t.startsWith('[[HIDDEN_LANG_LOCK]]') ||
    t.startsWith('[[CALLER_MEMORY]]')
  ) {
    return true;
  }
  // Nemotron sometimes narrates instructions instead of answering.
  const meta =
    /we need to respond|as per policy|the user asks|never narrate|language now:|reply in hindi only|speak only the final/i;
  return meta.test(t);
}

export function AgentChatTranscript({
  agentState,
  messages = [],
  className,
  ...props
}: AgentChatTranscriptProps) {
  const visibleMessages = messages.filter((m) => !isInternalOrMetaMessage(m.message));

  return (
    <Conversation className={className} {...props}>
      <ConversationContent>
        {visibleMessages.map((receivedMessage) => {
          const { id, timestamp, from, message } = receivedMessage;
          const locale = navigator?.language ?? 'en-US';
          const messageOrigin = from?.isLocal ? 'user' : 'assistant';
          const time = new Date(timestamp);
          const title = time.toLocaleTimeString(locale, { timeStyle: 'full' });

          return (
            <Message key={id} title={title} from={messageOrigin}>
              <MessageContent>
                {messageOrigin === 'assistant' && (
                  <div className="mb-1 flex items-center gap-2 border-b border-emerald-500/15 pb-1.5 text-[11px] font-medium tracking-wider text-emerald-400 uppercase">
                    <span className="inline-block size-1.5 animate-pulse rounded-full bg-emerald-400" />
                    Jan Sahay AI
                  </div>
                )}
                <MessageResponse>{message}</MessageResponse>
              </MessageContent>
            </Message>
          );
        })}
        <AnimatePresence>
          {agentState === 'thinking' && <AgentChatIndicator size="sm" />}
        </AnimatePresence>
      </ConversationContent>
      <ConversationScrollButton />
    </Conversation>
  );
}
