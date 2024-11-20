import { memo } from 'react';

function AnimatedCircle({ cx, cy, delay }: { cx: string; cy: string; delay: number }) {
  return (
    <circle
      cx={cx}
      cy={cy}
      r="19"
      fill="currentColor"
      style={{
        animation: `loading-icon-spinner-animation 0.8s ${delay}s infinite linear`,
      }}
    />
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
        <AnimatedCircle cx="420" cy="92" delay={0} />
        <AnimatedCircle cx="420" cy="256" delay={0.1} />
        <AnimatedCircle cx="420" cy="420" delay={0.2} />
        <AnimatedCircle cx="256" cy="420" delay={0.3} />
        <AnimatedCircle cx="92" cy="420" delay={0.4} />
        <AnimatedCircle cx="92" cy="256" delay={0.5} />
        <AnimatedCircle cx="92" cy="92" delay={0.6} />
        <AnimatedCircle cx="256" cy="92" delay={0.7} />
        <path
          d="M344.736 227.405H267.066V159.846C267.066 152.384 257.933 149.152 253.53 155.059L161.28 272C157.44 277.12 160.979 284.614 167.258 284.614H244.934V352.154C244.934 359.616 254.067 362.848 258.47 356.941L350.72 240C354.56 234.88 351.014 227.405 344.736 227.405Z"
          fill="currentColor"
        />
      </svg>
    </div>
  );
});
