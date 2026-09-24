/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_CHAT_URL?: string;
  readonly VITE_API_DOCS_URL?: string;
}

declare module '@brand' {
  const config: unknown;
  export default config;
}
