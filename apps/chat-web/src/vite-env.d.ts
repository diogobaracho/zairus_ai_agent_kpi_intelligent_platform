/// <reference types="vite/client" />

declare module '@brand' {
  const config: {
    brand: string;
    product: string;
    dataProvider: string;
    contact: { email: string };
  };
  export default config;
}
