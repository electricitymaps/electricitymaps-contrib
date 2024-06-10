import { memo } from 'react';

function AnimatedCircle({ cx, cy, begin }: { cx: string; cy: string; begin: string }) {
  return (
    <circle cx={cx} cy={cy} r="19" fill="currentColor">
      <animate
        attributeName="opacity"
        from="1"
        to=".3"
        dur="0.8s"
        repeatCount="indefinite"
        begin={begin}
      />
    </circle>
  );
}

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
        viewBox="0 0 512 512"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <AnimatedCircle cx="420" cy="92" begin="0s" />
        <AnimatedCircle cx="420" cy="256" begin="0.1s" />
        <AnimatedCircle cx="420" cy="420" begin="0.2s" />
        <AnimatedCircle cx="256" cy="420" begin="0.3s" />
        <AnimatedCircle cx="92" cy="420" begin="0.4s" />
        <AnimatedCircle cx="92" cy="256" begin="0.5s" />
        <AnimatedCircle cx="92" cy="92" begin="0.6s" />
        <AnimatedCircle cx="256" cy="92" begin="0.7s" />
        <path
          d="M344.736 227.405H267.066V159.846C267.066 152.384 257.933 149.152 253.53 155.059L161.28 272C157.44 277.12 160.979 284.614 167.258 284.614H244.934V352.154C244.934 359.616 254.067 362.848 258.47 356.941L350.72 240C354.56 234.88 351.014 227.405 344.736 227.405Z"
          fill="currentColor"
        />
      </svg>
    </div>
  );
});
