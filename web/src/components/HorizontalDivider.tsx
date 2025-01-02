import { memo } from 'react';

function HorizontalDivider() {
  return <hr className="my-2 h-px border-none bg-neutral-200/80 dark:bg-gray-700/80" />;
}

export default memo(HorizontalDivider);
