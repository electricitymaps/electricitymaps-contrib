export const isEmpty = (obj: any) =>
  // @ts-expect-error TS(2550): Property 'entries' does not exist on type 'ObjectC... Remove this comment to see the full error message
  [Object, Array].includes((obj || {}).constructor) && !Object.entries(obj || {}).length;
