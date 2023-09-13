import { ChartTitle } from './ChartTitle';

export function NotEnoughDataMessage({ title }: { title: string }) {
  return (
    <div className="w-full">
      <ChartTitle translationKey={title} hasLink={false} />
      <div className="my-2 rounded bg-gray-200 py-4 text-center text-sm dark:bg-gray-800">
        <p>Not enough data available to display chart</p>
      </div>
    </div>
  );
}
