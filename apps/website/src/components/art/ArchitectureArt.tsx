import { useT } from '../../i18n/useT';

export default function ArchitectureArt() {
  const t = useT();
  const box = 'fill-white stroke-[#DCE3EE]';
  const label = 'fill-[#0B1220] text-[13px] font-semibold';
  const sub = 'fill-[#475569] text-[11px]';
  return (
    <svg viewBox="0 0 760 360" className="w-full" role="img" aria-label={t('architecture.label')}>
      <defs>
        <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 z" fill="#2F6BFF" />
        </marker>
      </defs>
      <rect x="20" y="20" width="200" height="70" rx="14" className={box} />
      <text x="120" y="50" textAnchor="middle" className={label}>
        {t('architecture.chat')}
      </text>
      <text x="120" y="70" textAnchor="middle" className={sub}>
        React · SSE
      </text>
      <rect x="280" y="20" width="200" height="70" rx="14" className={box} />
      <text x="380" y="50" textAnchor="middle" className={label}>
        {t('architecture.desktop')}
      </text>
      <text x="380" y="70" textAnchor="middle" className={sub}>
        MCP client · stdio / http
      </text>
      <rect x="540" y="20" width="200" height="70" rx="14" className={box} />
      <text x="640" y="50" textAnchor="middle" className={label}>
        {t('architecture.scripts')}
      </text>
      <text x="640" y="70" textAnchor="middle" className={sub}>
        REST · JSON
      </text>
      <rect x="20" y="140" width="330" height="80" rx="14" className={box} />
      <text x="185" y="170" textAnchor="middle" className={label}>
        {t('architecture.api')}
      </text>
      <text x="185" y="192" textAnchor="middle" className={sub}>
        {t('architecture.apiSub')}
      </text>
      <rect x="410" y="140" width="330" height="80" rx="14" className={box} />
      <text x="575" y="170" textAnchor="middle" className={label}>
        {t('architecture.mcp')}
      </text>
      <text x="575" y="192" textAnchor="middle" className={sub}>
        {t('architecture.mcpSub')}
      </text>
      <rect x="120" y="260" width="520" height="40" rx="12" fill="#E3ECFF" stroke="#2F6BFF" />
      <text x="380" y="285" textAnchor="middle" className={label}>
        {t('architecture.core')}
      </text>
      <rect x="280" y="320" width="200" height="34" rx="10" fill="#0B1220" />
      <text x="380" y="342" textAnchor="middle" className="fill-white text-[12px] font-semibold">
        Postgres 16
      </text>
      <g stroke="#2F6BFF" strokeWidth="2" fill="none" markerEnd="url(#arrow)">
        <path d="M120 90 V140" />
        <path d="M380 90 V140" />
        <path d="M640 90 V140" />
        <path d="M350 180 H410" />
        <path d="M185 220 V260" />
        <path d="M575 220 V260" />
        <path d="M380 300 V320" />
      </g>
      <text x="380" y="130" textAnchor="middle" className="fill-[#2F6BFF] text-[10px]">
        {t('architecture.llm')}
      </text>
    </svg>
  );
}
