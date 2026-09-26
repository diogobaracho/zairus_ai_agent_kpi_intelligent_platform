import { useT } from '../../i18n/useT';

const rows = [
  { at: '18:02:11.412', where: 'browser', what: 'POST /v1/chat', trace: '9f1c2ab4d0e3f5a7' },
  {
    at: '18:02:11.418',
    where: 'api',
    what: 'llm_turn iteration=1 stop_reason=tool_use',
    trace: '9f1c2ab4d0e3f5a7',
  },
  {
    at: '18:02:11.431',
    where: 'mcp',
    what: 'tool_call get_kpi_qtd ok 12ms {"ticker":"ORBY","kpi":"total_revenue"}',
    trace: '9f1c2ab4d0e3f5a7',
  },
  {
    at: '18:02:11.433',
    where: 'postgres',
    what: 'tool_call_audit row #1042 status=ok',
    trace: '9f1c2ab4d0e3f5a7',
  },
  {
    at: '18:02:12.007',
    where: 'api',
    what: 'agent_run tool_calls=1 stopped_reason=end_turn',
    trace: '9f1c2ab4d0e3f5a7',
  },
];

export default function TraceTimelineMockup() {
  const t = useT();
  return (
    <div
      className="overflow-x-auto rounded-2xl border border-line bg-white shadow-card"
      aria-label={t('mockup.timelineLabel')}
    >
      <table className="w-full text-xs">
        <thead className="bg-paper text-left text-ink-soft">
          <tr>
            <th className="p-2">{t('mockup.time')}</th>
            <th className="p-2">{t('mockup.where')}</th>
            <th className="p-2">{t('mockup.event')}</th>
            <th className="p-2">trace_id</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.at} className="border-t border-line">
              <td className="p-2 font-mono">{r.at}</td>
              <td className="p-2">{r.where}</td>
              <td className="p-2 font-mono">{r.what}</td>
              <td className="p-2 font-mono text-brand">{r.trace}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
