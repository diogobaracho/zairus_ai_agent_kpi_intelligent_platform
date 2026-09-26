export const layers = ['clients', 'adapters', 'domain', 'data'] as const;
export const layerItems = ['i1', 'i2', 'i3'] as const;

export const tenancy = ['i1', 'i2', 'i3'] as const;

export const observability = [
  { id: 'trace', value: '1' },
  { id: 'fields', value: '6' },
  { id: 'health', value: '2' },
] as const;
