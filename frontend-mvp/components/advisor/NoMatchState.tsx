export function NoMatchState({ warnings, nextQuestion }: { warnings: string[]; nextQuestion?: string }) {
  return (
    <div data-testid="answer-no_match" className="rounded-md border p-4">
      <p className="font-medium">Chưa tìm được máy phù hợp</p>
      <ul className="list-disc pl-5 text-sm">
        {warnings.length > 0 ? warnings.map((w, i) => <li key={i}>{w}</li>) : <li>không có</li>}
      </ul>
      {nextQuestion && <p className="mt-2 text-sm">{nextQuestion}</p>}
    </div>
  );
}
