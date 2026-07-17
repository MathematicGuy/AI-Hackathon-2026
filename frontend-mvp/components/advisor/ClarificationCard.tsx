import { display } from "@/lib/format";

export function ClarificationCard({ question }: { question?: string }) {
  return (
    <div data-testid="answer-clarification" className="rounded-md border p-4">
      <p className="font-medium">Cần thêm thông tin</p>
      <p className="text-sm">{display(question)}</p>
    </div>
  );
}
