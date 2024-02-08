export default function Pill({
  classes,
  text,
  isButton = false,
  isDisabled = false,
  onClick,
  identifier = '',
}: {
  classes: string;
  text: string;
  isButton?: boolean;
  isDisabled?: boolean;
  onClick?: (identifier: string) => void;
  identifier?: string;
}): JSX.Element {
  const Element = isButton ? 'button' : 'div';

  const handleClick = () => {
    if (onClick) {
      onClick(identifier);
    }
  };

  return (
    <Element
      className={`flex flex-row items-center justify-center rounded-full ${classes}`}
      role={isButton ? 'button' : undefined}
      onClick={handleClick}
      disabled={isDisabled}
      data-test-id="pill"
    >
      <div className={`text-xs font-semibold`}>{text}</div>
    </Element>
  );
}
