import { useCallback } from 'react';
import { twMerge } from 'tailwind-merge';

interface ToggleSwitchProps {
  isEnabled: boolean;
  onChange: (isEnabled: boolean) => void;
  ariaLabel?: string;
  className?: string;
  activeColor?: string;
  inactiveColor?: string;
}

function ToggleSwitch({
  isEnabled,
  onChange,
  ariaLabel,
  className,
  activeColor = 'bg-neutral-500 dark:bg-neutral-300',
  inactiveColor = 'bg-neutral-300 dark:bg-neutral-500',
}: ToggleSwitchProps): JSX.Element {
  const handleToggle = useCallback(() => {
    onChange(!isEnabled);
  }, [isEnabled, onChange]);
  return (
    <button
      onClick={handleToggle}
      className={twMerge(
        `relative inline-flex h-5 w-9 items-center rounded-full transition-colors`,
        isEnabled ? activeColor : inactiveColor,
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-green focus-visible:ring-offset-1',
        className
      )}
      role="switch"
      aria-checked={isEnabled}
      aria-label={ariaLabel}
    >
      <span
        className={`${
          isEnabled ? 'translate-x-[18px]' : 'translate-x-[2px]'
        } inline-block h-4 w-4 transform rounded-full bg-white transition-transform dark:bg-neutral-900`}
      />
    </button>
  );
}

export default ToggleSwitch;
