export function LegalRoute({ terms }: { terms: boolean }) {
  return <main className="page"><section className="panel">
    <p className="eyebrow">Sinopia by KamdyB</p>
    <h1 className="display-title">{terms ? "Terms of use" : "Privacy notice"}</h1>
    {terms ? <>
      <p>Sinopia is a workload-monitoring aid. It does not provide medical advice, diagnosis, or injury prediction. Coaches remain responsible for decisions and should refer health concerns to qualified professionals.</p>
      <p>Use accurate information, protect athlete check-in links, and never use the tool to punish, rank, or scout young athletes.</p>
    </> : <>
      <p>Sinopia processes athlete labels, training records, and wellbeing check-ins so the responsible coach can review workload and follow up when needed.</p>
      <p>Check-ins are shared with the coach responsible for that team. The public check-in link does not require an athlete account and should be treated as private.</p>
      <p>For access, correction, or deletion requests, contact the coach who issued the link or use the account-data controls in the coach app.</p>
    </>}
    <p><a href="/sign-in">Back to Sinopia</a></p>
  </section></main>;
}
