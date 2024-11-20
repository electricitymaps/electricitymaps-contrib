export function HorizontalDivider() {
  return <hr className="my-2 h-px border-none bg-neutral-200/80 dark:bg-gray-700/80" />;
}

export function VerticalDivider() {
  return (
    <div className="left-1/2 my-2 inline-block w-px self-stretch bg-neutral-200/80 dark:bg-gray-700/80" />
  );
}
