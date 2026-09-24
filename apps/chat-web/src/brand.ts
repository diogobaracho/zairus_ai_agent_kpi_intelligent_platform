import config from '@brand';

/** White-label names, read at build time from brand.config.json. */
export const brand = {
  name: config.brand,
  product: config.product,
  provider: config.dataProvider,
  initial: config.brand.charAt(0).toUpperCase(),
};
