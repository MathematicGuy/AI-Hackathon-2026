export function GuardrailState({ warnings }: { warnings: string[] }) {
  return (
    <div data-testid="answer-guardrail_block" className="rounded-md border border-destructive p-4">
      <p className="font-medium text-destructive">Yêu cầu không được hỗ trợ</p>
      <ul className="list-disc pl-5 text-sm">
        {warnings.length > 0
          ? warnings.map((w, i) => <li key={i}>{w}</li>)
          : <li>Mình chỉ hỗ trợ tư vấn máy lạnh.</li>}
      </ul>
    </div>
  );
}
