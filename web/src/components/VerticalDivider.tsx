import { memo } from 'react';

function VerticalDivider() {
  return (
    <div className="left-1/2 my-2 inline-block w-px self-stretch bg-neutral-200/80 dark:bg-neutral-700/80" />
  );
}

export default memo(VerticalDivider);
