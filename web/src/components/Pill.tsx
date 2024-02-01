import { useState } from 'react';

export default function Pill({
  classes,
  clickedClasses = '',
  text,
  isButton = false,
  isDisabled = false,
  onClick,
  identifier = '',
}: {
  classes: string;
  clickedClasses?: string;
  text: string;
  isButton?: boolean;
  isDisabled?: boolean;
  onClick?: (identifier: string) => void;
  identifier?: string;
}): JSX.Element {
  const Element = isButton ? 'button' : 'div';

  const [clicked, setClickedClasses] = useState('');

  const handleClick = () => {
    if (onClick) {
      onClick(identifier);
      setClickedClasses(clickedClasses);
    }
  };

  return (
    <Element
      className={`flex flex-row items-center justify-center rounded-full ${classes} ${clicked}`}
      role={isButton ? 'button' : undefined}
      onClick={handleClick}
      disabled={isDisabled}
    >
      <div className={`text-xs font-semibold`}>{text}</div>
    </Element>
  );
}
