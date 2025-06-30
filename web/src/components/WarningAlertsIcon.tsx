import * as React from 'react';

interface WarningIconProps extends React.SVGProps<SVGSVGElement> {
  className?: string;
  fill?: string;
}

function WarningIcon({
  className = '',
  fill = 'currentColor',
  ...props
}: WarningIconProps) {
  return (
    <svg
      width="33"
      height="32"
      viewBox="0 0 33 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      {...props}
    >
      {/* Inner white circle */}
      <circle cx="16.5" cy="16" r="15" fill="white" fillOpacity="0.1" />

      {/* Your warning icon path */}
      <path
        d="M16.5 13V15.6667M16.5 18.3333H16.5067M22.9867 19L17.6533 9.66667C17.537 9.46147 17.3684 9.29079 17.1646 9.17205C16.9608 9.0533 16.7292 8.99074 16.4933 8.99074C16.2575 8.99074 16.0258 9.0533 15.8221 9.17205C15.6183 9.29079 15.4496 9.46147 15.3333 9.66667L10 19C9.88246 19.2036 9.82082 19.4346 9.82134 19.6697C9.82186 19.9047 9.88452 20.1355 10.003 20.3386C10.1214 20.5416 10.2914 20.7097 10.4958 20.8259C10.7002 20.942 10.9316 21.0021 11.1667 21H21.8333C22.0673 20.9998 22.297 20.938 22.4995 20.8209C22.702 20.7037 22.8701 20.5354 22.987 20.3327C23.1039 20.1301 23.1654 19.9003 23.1653 19.6663C23.1652 19.4324 23.1036 19.2026 22.9867 19Z"
        stroke={fill}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default WarningIcon;
