import TimeAverageToggle from 'components/TimeAverageToggle';
import TimeSlider from 'components/TimeSlider';

export default function TimeController() {
  return (
    <div
      className={
        'absolute bottom-3 left-3 right-3 rounded-xl bg-yellow-50 p-5 shadow-md sm:max-w-md'
      }
    >
      <div className="flex flex-row items-center justify-between">
        <p className="mb-2 text-sm font-bold">Display data from the past</p>
        <div className="mb-2 rounded-full bg-gray-100 py-2 px-3 text-xs">
          November 4, 2022 at 10:00 PM
        </div>
      </div>
      <TimeAverageToggle className="mb-2" />
      <TimeSlider />
    </div>
  );
}
