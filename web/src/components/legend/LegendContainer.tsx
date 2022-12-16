import type { ReactElement } from 'react';
import Co2Legend from './Co2Legend';

export default function LegendContainer(): ReactElement {
  return (
    <div className="fixed bottom-4 right-4 z-50 flex h-[78px] w-[224px] rounded bg-white p-2 shadow dark:bg-gray-900">
      <Co2Legend />
    </div>
  );
}
