import { useCallback } from 'react';
import { useIntl } from 'react-intl';
import { brand } from '../brand';

type Values = Record<string, string | number>;

const brandValues: Values = {
  brand: brand.brand,
  product: brand.product,
  provider: brand.dataProvider,
};

/** `t('home.hero.title')`, with the white-label names always available as {brand}, {product}, {provider}. */
export function useT() {
  const intl = useIntl();
  return useCallback(
    (id: string, values?: Values) => intl.formatMessage({ id }, { ...brandValues, ...values }),
    [intl],
  );
}
