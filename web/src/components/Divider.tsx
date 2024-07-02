export function HorizontalDivider() {
  return <hr className="my-2 h-px border-none bg-gray-200/50 dark:bg-gray-700/50" />;
}

export function VerticalDivider() {
  return (
    <div className="left-1/2 my-2 inline-block w-px self-stretch bg-gray-200/50 dark:bg-gray-700/50" />
  );
}
