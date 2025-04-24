import { memo } from 'react';

export const LoadingSpinnerIcon = memo(function LoadingSpinnerIcon({
  size = 100,
}: {
  size?: number;
}) {
  return (
    <div className="text-black dark:text-white">
      <svg
        width={size}
        height={size}
        viewBox="0 0 71 75" // Adjusted viewBox to match the new logo
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        // Add a class for the animation
        className="animate-loading-icon-spinner-animation"
      >
        {/* Inserted LogoIcon path */}
        <path
          fillRule="evenodd"
          clipRule="evenodd"
          d="M3.08184 50.9458C4.986 52.8132 7.61657 53.9683 10.5222 53.9683H29.735V69.3859C29.735 70.9362 30.3757 72.3397 31.4117 73.3557C32.4476 74.3716 33.8788 75 35.4596 75C39.1049 75 42.5289 73.2848 44.6656 70.3885L69.0027 37.3997C70.301 35.6398 70.9999 33.5231 70.9999 31.3509C70.9999 28.5014 69.8222 25.9216 67.918 24.0542C66.0139 22.1868 63.3833 21.0317 60.4777 21.0317H41.2649V5.6141C41.2649 4.06381 40.6241 2.66029 39.5882 1.64434C38.5523 0.628387 37.1211 7.62939e-06 35.5403 7.62939e-06C31.895 7.62939e-06 28.471 1.71517 26.3342 4.61155L1.99719 37.6003C0.698875 39.3601 -6.10352e-05 41.4769 -6.10352e-05 43.6491C-6.10352e-05 46.4986 1.17768 49.0784 3.08184 50.9458Z"
          fill="currentColor"
        />
      </svg>
    </div>
  );
});
