"use client";
import * as React from "react";
import { Button } from "@/components/ui/button";

export function MessageInput({
  onSend,
  disabled,
}: {
  onSend: (text: string) => void;
  disabled: boolean;
}) {
  const [text, setText] = React.useState("");
  function submit() {
    const trimmed = text.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setText("");
  }
  return (
    <div className="flex gap-2">
      <input
        data-testid="message-input"
        className="flex-1 rounded-md border px-3 py-2 text-sm"
        placeholder="Nhập nhu cầu của bạn… (vd: phòng 18m2, ngân sách 10 triệu)"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && submit()}
        disabled={disabled}
      />
      <Button data-testid="message-send" onClick={submit} disabled={disabled}>
        Gửi
      </Button>
    </div>
  );
}
