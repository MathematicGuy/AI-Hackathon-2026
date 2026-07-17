"use client";
import * as React from "react";
import { sendMessage } from "@/lib/advisor-api";
import { MessageList, type Turn } from "@/components/chat/MessageList";
import { MessageInput } from "@/components/chat/MessageInput";

export function ChatPanel() {
  const [turns, setTurns] = React.useState<Turn[]>([]);
  const [loading, setLoading] = React.useState(false);
  const sessionId = React.useRef<string | undefined>(undefined);

  async function send(text: string) {
    setLoading(true);
    try {
      const response = await sendMessage({ message: text, session_id: sessionId.current });
      sessionId.current = response.session_id;
      setTurns((prev) => [...prev, { user: text, response }]);
    } finally {
      setLoading(false);
    }
  }

  function onMore() {
    void send("xem thêm");
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4 p-6">
      <h1 className="text-lg font-semibold">Tư vấn máy lạnh — bản thử nghiệm</h1>
      <MessageList turns={turns} loading={loading} onMore={onMore} />
      <MessageInput onSend={send} disabled={loading} />
    </div>
  );
}
