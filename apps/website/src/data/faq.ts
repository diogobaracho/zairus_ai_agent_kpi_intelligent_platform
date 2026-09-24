import { brand } from '../brand';
import type { FaqItem } from '../types/content';

export const faq: FaqItem[] = [
  {
    question: 'What data does the platform serve?',
    answer: `${brand.dataProvider}'s quarterly KPI estimates for public companies: completed-quarter (historical) estimates and quarter-to-date snapshots that update at most daily.`,
  },
  {
    question: 'How is a chat answer produced?',
    answer:
      'A language model calls four read-only MCP tools (search companies, list KPIs, get history, get QTD). Every call, with its arguments and result, is shown next to the answer and stored in an audit table.',
  },
  {
    question: 'What happens when I misspell a company or KPI?',
    answer:
      'The tool returns a structured error with the closest matches and a hint. The assistant retries once with the suggestion and tells you what it did.',
  },
  {
    question: 'Can I use it from Claude Desktop or Cursor?',
    answer:
      'Yes. The MCP server runs over stdio for desktop clients and over HTTP for services. The developer page has the exact configuration.',
  },
  {
    question: 'Does it work without an LLM API key?',
    answer:
      'Yes. A deterministic stub provider runs the same tool-calling flow, so the demo, tests and CI never need a key. Set a key to use a real model.',
  },
  {
    question: 'How do you keep the model away from the database?',
    answer:
      'The model only sees tool schemas and results. Tools go through one domain layer with parameterised queries; identity comes from the server, never from the model.',
  },
  {
    question: 'Is it multi-tenant?',
    answer:
      'It is multi-tenant-ready: every call carries a tenant id and the audit trail records it. Row-level security is the documented next step.',
  },
  {
    question: 'Can I run it myself?',
    answer:
      'One command starts Postgres, the API, the MCP server, the chat app and this site with Docker Compose. Each part also ships as its own container image.',
  },
];
