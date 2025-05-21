import { DatabaseZap } from 'lucide-react';
import React from 'react';

interface DataCenterIconProps {
  provider: string;
  withPin?: boolean;
}

export function DataCenterIcon({ provider, withPin = false }: DataCenterIconProps) {
  const providerLower = provider.toLowerCase();

  if (providerLower.includes('aws') || providerLower.includes('amazon')) {
    return <Aws size={20} withPin={withPin} />;
  }

  if (providerLower.includes('gcp') || providerLower.includes('google')) {
    return <Gcp size={20} withPin={withPin} />;
  }

  if (providerLower.includes('azure') || providerLower.includes('microsoft')) {
    return <Azure size={20} withPin={withPin} />;
  }

  // Default fallback icon
  return <DatabaseZap size={24} strokeWidth={2} />;
}

// --- Pin SVG Component with Blur Effect ---
function PinIconSVG(): React.ReactElement {
  return (
    <svg
      width="28"
      height="32"
      viewBox="0 0 28 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <foreignObject x="-50" y="-50" width="128" height="132">
        <div
          style={{
            backdropFilter: 'blur(25px)',
            clipPath: 'url(#bgblur_pin_clip_path)',
            height: '100%',
            width: '100%',
          }}
        ></div>
      </foreignObject>
      <path
        opacity="0.8"
        data-figma-bg-blur-radius="50"
        d="M14 0.5C17.5562 0.499821 20.969 1.91162 23.4971 4.42871C25.9463 6.86733 27.3731 10.1525 27.4922 13.6094L27.5 13.9443C27.4978 18.5595 24.5573 22.73 21.4443 25.8506C19.1158 28.1848 16.759 29.8689 15.5801 30.6738L14.8379 31.1768L14.8242 31.1875L14.8115 31.1982C14.585 31.3931 14.2971 31.5 14 31.5C13.7401 31.5 13.4872 31.4185 13.2764 31.2676L13.1885 31.1982C13.129 31.147 13.0232 31.0727 12.917 30.999C12.8139 30.9275 12.6186 30.7937 12.4443 30.6729C12.0597 30.4062 11.5393 30.0408 10.9307 29.585C9.71248 28.6726 8.14112 27.4013 6.58789 25.8496C3.46321 22.7281 0.502215 18.5583 0.5 13.9443C0.535588 10.3654 1.97473 6.94593 4.50293 4.42871C6.95202 1.99029 10.2313 0.588915 13.667 0.503906L14 0.5Z"
        fill="white"
        fillOpacity="0.8"
        stroke="#E5E5E5"
      />
      <defs>
        <clipPath id="bgblur_pin_clip_path" transform="translate(50 50)">
          <path d="M14 0.5C17.5562 0.499821 20.969 1.91162 23.4971 4.42871C25.9463 6.86733 27.3731 10.1525 27.4922 13.6094L27.5 13.9443C27.4978 18.5595 24.5573 22.73 21.4443 25.8506C19.1158 28.1848 16.759 29.8689 15.5801 30.6738L14.8379 31.1768L14.8242 31.1875L14.8115 31.1982C14.585 31.3931 14.2971 31.5 14 31.5C13.7401 31.5 13.4872 31.4185 13.2764 31.2676L13.1885 31.1982C13.129 31.147 13.0232 31.0727 12.917 30.999C12.8139 30.9275 12.6186 30.7937 12.4443 30.6729C12.0597 30.4062 11.5393 30.0408 10.9307 29.585C9.71248 28.6726 8.14112 27.4013 6.58789 25.8496C3.46321 22.7281 0.502215 18.5583 0.5 13.9443C0.535588 10.3654 1.97473 6.94593 4.50293 4.42871C6.95202 1.99029 10.2313 0.588915 13.667 0.503906L14 0.5Z" />
        </clipPath>
      </defs>
    </svg>
  );
}

// --- Icon Wrapper ---
interface IconWrapperProps {
  iconElement: React.ReactElement;
  iconNominalWidth: number;
  iconNominalHeight: number;
  withPin?: boolean;
  className?: string;
}

// Define PinnableIconProps interface
interface PinnableIconProps {
  withPin?: boolean;
  className?: string;
  size?: number;
}

const PIN_WIDTH = 28;
const PIN_HEIGHT = 32;
const PIN_HEAD_DIAMETER = 27;
const PIN_HEAD_CENTER_X = PIN_WIDTH / 2;
const PIN_HEAD_CENTER_Y = PIN_HEAD_DIAMETER / 2;

function IconWrapper({
  iconElement,
  iconNominalWidth,
  iconNominalHeight,
  withPin,
  className,
}: IconWrapperProps): React.ReactElement {
  if (!withPin) {
    return <div className={className}>{iconElement}</div>;
  }

  const iconOffsetX = PIN_HEAD_CENTER_X - iconNominalWidth / 2;
  const iconOffsetY = PIN_HEAD_CENTER_Y - iconNominalHeight / 2;

  return (
    <div
      className={className}
      style={{
        position: 'relative',
        width: `${PIN_WIDTH}px`,
        height: `${PIN_HEIGHT}px`,
        display: 'inline-flex',
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      <PinIconSVG />
      <div
        style={{
          position: 'absolute',
          left: `${iconOffsetX}px`,
          top: `${iconOffsetY}px`,
        }}
      >
        {iconElement}
      </div>
    </div>
  );
}

// --- GCP Icon ---
const GCP_ICON_NOMINAL_WIDTH = 20;
const GCP_ICON_NOMINAL_HEIGHT = 16;
const GCP_ASPECT_RATIO = GCP_ICON_NOMINAL_HEIGHT / GCP_ICON_NOMINAL_WIDTH;

interface CloudIconSvgComponentProps {
  size?: number;
  width?: number;
  height?: number;
}

function GcpIconSvgComponent(props: CloudIconSvgComponentProps): React.ReactElement {
  let w = props.width ?? GCP_ICON_NOMINAL_WIDTH;
  let h = props.height ?? GCP_ICON_NOMINAL_HEIGHT;

  if (props.size != null) {
    w = props.size;
    h = props.size * GCP_ASPECT_RATIO;
  }

  return (
    <svg
      width={w}
      height={h}
      viewBox={`0 0 ${GCP_ICON_NOMINAL_WIDTH} ${GCP_ICON_NOMINAL_HEIGHT}`}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <g clipPath="url(#clip0_gcp)">
        <path
          d="M13.285 4.41747L15.0151 2.68738L15.1304 1.95889C11.9777 -0.90785 6.96607 -0.582792 4.12398 2.63715C3.33462 3.53147 2.74895 4.64643 2.43665 5.79778L3.05628 5.71047L6.51639 5.13981L6.78352 4.86669C8.32267 3.17632 10.9251 2.94891 12.7022 4.38715L13.285 4.41747Z"
          fill="#EA4335"
        />
        <path
          d="M17.4797 5.74687C17.082 4.28244 16.2655 2.96595 15.1304 1.95891L12.7022 4.38708C13.2083 4.8006 13.6138 5.32361 13.8883 5.91669C14.1627 6.50976 14.2989 7.15741 14.2866 7.8108V8.24183C15.48 8.24183 16.4477 9.20938 16.4477 10.4029C16.4477 11.5964 15.4801 12.5397 14.2866 12.5397H9.95841L9.53345 13.0011V15.5931L9.95841 15.9998H14.2866C17.391 16.024 19.9273 13.5513 19.9515 10.4469C19.9587 9.52043 19.7368 8.60656 19.3056 7.78657C18.8743 6.96659 18.2471 6.26591 17.4797 5.74687Z"
          fill="#4285F4"
        />
        <path
          d="M5.63607 15.9999H9.95823V12.5397H5.63607C5.33012 12.5396 5.0278 12.4734 4.74984 12.3455L4.13666 12.5337L2.39444 14.2637L2.24268 14.8526C3.21971 15.5903 4.4118 16.0052 5.63607 15.9999Z"
          fill="#34A853"
        />
        <path
          d="M5.63612 4.77565C2.53171 4.79408 0.0300603 7.32581 0.0485639 10.4303C0.0536619 11.2858 0.253961 12.1288 0.6342 12.8952C1.01444 13.6615 1.56458 14.331 2.24272 14.8525L4.74989 12.3455C3.66222 11.854 3.17879 10.574 3.67022 9.4863C4.16166 8.39863 5.44175 7.9152 6.52935 8.40656C7.00862 8.62313 7.39248 9.00702 7.60901 9.4863L10.1162 6.97914C9.58995 6.29121 8.91172 5.73435 8.13452 5.3521C7.35732 4.96985 6.50223 4.77251 5.63612 4.77565Z"
          fill="#FBBC05"
        />
      </g>
      <defs>
        <clipPath id="clip0_gcp">
          <rect width="20" height="16" fill="white" />
        </clipPath>
      </defs>
    </svg>
  );
}

export function Gcp({ withPin, className, size }: PinnableIconProps): React.ReactElement {
  const iconElement = withPin ? (
    <GcpIconSvgComponent
      width={GCP_ICON_NOMINAL_WIDTH}
      height={GCP_ICON_NOMINAL_HEIGHT}
    />
  ) : (
    <GcpIconSvgComponent size={size} />
  );

  return (
    <IconWrapper
      iconElement={iconElement}
      iconNominalWidth={GCP_ICON_NOMINAL_WIDTH}
      iconNominalHeight={GCP_ICON_NOMINAL_HEIGHT}
      withPin={withPin}
      className={className}
    />
  );
}

// --- Azure Icon ---
const AZURE_ICON_NOMINAL_WIDTH = 20;
const AZURE_ICON_NOMINAL_HEIGHT = 16;
const AZURE_ASPECT_RATIO = AZURE_ICON_NOMINAL_HEIGHT / AZURE_ICON_NOMINAL_WIDTH;

function AzureIconSvgComponent(props: CloudIconSvgComponentProps): React.ReactElement {
  let w = props.width ?? AZURE_ICON_NOMINAL_WIDTH;
  let h = props.height ?? AZURE_ICON_NOMINAL_HEIGHT;

  if (props.size != null) {
    w = props.size;
    h = props.size * AZURE_ASPECT_RATIO;
  }

  return (
    <svg
      width={w}
      height={h}
      viewBox={`0 0 ${AZURE_ICON_NOMINAL_WIDTH} ${AZURE_ICON_NOMINAL_HEIGHT}`}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <g clipPath="url(#clip0_azure)">
        <path
          d="M7.18465 0.000198989H12.1845L6.99416 15.4548C6.94082 15.6136 6.83926 15.7516 6.70379 15.8493C6.56831 15.9471 6.40575 15.9997 6.23897 15.9997H2.3478C2.22145 15.9997 2.09692 15.9695 1.9845 15.9115C1.87208 15.8536 1.77501 15.7695 1.70131 15.6664C1.62761 15.5633 1.57941 15.444 1.56067 15.3184C1.54194 15.1928 1.55323 15.0646 1.5936 14.9442L6.42925 0.545162C6.48257 0.386291 6.58415 0.248234 6.71966 0.150434C6.85518 0.0526335 7.01781 1.88292e-05 7.18465 0V0.000198989Z"
          fill="url(#paint0_linear_azure)"
        />
        <path
          d="M14.4502 10.3661H6.52159C6.44788 10.3661 6.37587 10.3883 6.31492 10.4299C6.25397 10.4716 6.20691 10.5307 6.17988 10.5996C6.15284 10.6685 6.14708 10.744 6.16334 10.8163C6.1796 10.8885 6.21713 10.9542 6.27104 11.0047L11.3658 15.7835C11.5141 15.9225 11.7094 15.9998 11.9123 15.9998H16.4017L14.4502 10.3661Z"
          fill="#0078D4"
        />
        <path
          d="M7.18453 0.000204208C7.01587 -0.000445629 6.85143 0.053119 6.71521 0.153073C6.579 0.253028 6.47816 0.394134 6.42742 0.55578L1.59942 14.9311C1.55632 15.0519 1.54278 15.1813 1.55997 15.3084C1.57716 15.4356 1.62457 15.5567 1.69818 15.6615C1.7718 15.7664 1.86945 15.8518 1.98289 15.9107C2.09632 15.9696 2.2222 16.0002 2.34987 15.9998H6.34136C6.49001 15.9731 6.62895 15.9072 6.74399 15.8089C6.85903 15.7106 6.94605 15.5834 6.99616 15.4402L7.959 12.5886L11.3981 15.8122C11.5422 15.932 11.723 15.9983 11.91 15.9998H16.3827L14.4211 10.3661L8.70245 10.3674L12.2025 0.000204208H7.18453Z"
          fill="url(#paint1_linear_azure)"
        />
        <path
          d="M13.5707 0.544366C13.5174 0.385754 13.416 0.24793 13.2806 0.150308C13.1453 0.0526851 12.983 0.000183597 12.8164 0.000198367H7.24414C7.5857 0.000198367 7.88918 0.219152 7.99841 0.544366L12.8342 14.944C12.8746 15.0644 12.886 15.1927 12.8673 15.3183C12.8486 15.444 12.8004 15.5633 12.7266 15.6665C12.6529 15.7697 12.5558 15.8538 12.4434 15.9118C12.3309 15.9698 12.2063 16 12.0799 16H17.6524C17.7788 16 17.9034 15.9697 18.0158 15.9117C18.1282 15.8537 18.2253 15.7696 18.299 15.6664C18.3727 15.5632 18.4209 15.4439 18.4396 15.3183C18.4583 15.1927 18.4469 15.0644 18.4065 14.944L13.5707 0.544366Z"
          fill="url(#paint2_linear_azure)"
        />
      </g>
      <defs>
        <linearGradient
          id="paint0_linear_azure"
          x1="628.579"
          y1="118.574"
          x2="134.548"
          y2="1570.89"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#114A8B" />
          <stop offset="1" stopColor="#0669BC" />
        </linearGradient>
        <linearGradient
          id="paint1_linear_azure"
          x1="887.186"
          y1="836.988"
          x2="781.223"
          y2="872.639"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopOpacity="0.3" />
          <stop offset="0.071" stopOpacity="0.2" />
          <stop offset="0.321" stopOpacity="0.1" />
          <stop offset="0.623" stopOpacity="0.05" />
          <stop offset="1" stopOpacity="0" />
        </linearGradient>
        <linearGradient
          id="paint2_linear_azure"
          x1="424.925"
          y1="73.5993"
          x2="964.018"
          y2="1502.77"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#3CCBF4" />
          <stop offset="1" stopColor="#2892DF" />
        </linearGradient>
        <clipPath id="clip0_azure">
          <rect width="20" height="16" fill="white" />
        </clipPath>
      </defs>
    </svg>
  );
}

export function Azure({
  withPin,
  className,
  size,
}: PinnableIconProps): React.ReactElement {
  const iconElement = withPin ? (
    <AzureIconSvgComponent
      width={AZURE_ICON_NOMINAL_WIDTH}
      height={AZURE_ICON_NOMINAL_HEIGHT}
    />
  ) : (
    <AzureIconSvgComponent size={size} />
  );

  return (
    <IconWrapper
      iconElement={iconElement}
      iconNominalWidth={AZURE_ICON_NOMINAL_WIDTH}
      iconNominalHeight={AZURE_ICON_NOMINAL_HEIGHT}
      withPin={withPin}
      className={className}
    />
  );
}

// --- AWS Icon ---
const AWS_ICON_NOMINAL_WIDTH = 20;
const AWS_ICON_NOMINAL_HEIGHT = 16;
const AWS_ASPECT_RATIO = AWS_ICON_NOMINAL_HEIGHT / AWS_ICON_NOMINAL_WIDTH;

function AwsIconSvgComponent(props: CloudIconSvgComponentProps): React.ReactElement {
  let w = props.width ?? AWS_ICON_NOMINAL_WIDTH;
  let h = props.height ?? AWS_ICON_NOMINAL_HEIGHT;

  if (props.size != null) {
    w = props.size;
    h = props.size * AWS_ASPECT_RATIO;
  }

  return (
    <svg
      width={w}
      height={h}
      viewBox={`0 0 ${AWS_ICON_NOMINAL_WIDTH} ${AWS_ICON_NOMINAL_HEIGHT}`}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M5.78805 6.34141C5.78805 6.58745 5.81461 6.7869 5.86094 6.93318C5.91976 7.09774 5.99058 7.25773 6.07281 7.41184C6.10594 7.46502 6.11914 7.5182 6.11914 7.56478C6.11914 7.63122 6.07945 7.69773 5.99336 7.76424L5.57617 8.04345C5.51656 8.08337 5.45695 8.10329 5.40391 8.10329C5.33773 8.10329 5.27148 8.07004 5.20523 8.0102C5.11593 7.914 5.03611 7.80935 4.96688 7.69773C4.90063 7.58478 4.83437 7.45835 4.76156 7.30549C4.24495 7.9171 3.59594 8.22293 2.81453 8.22298C2.25828 8.22298 1.81453 8.06337 1.49 7.74431C1.16555 7.4251 1 6.99961 1 6.46776C1 5.90267 1.19867 5.44392 1.60266 5.0982C2.00656 4.75247 2.54305 4.57961 3.22516 4.57961C3.45031 4.57961 3.68211 4.59953 3.92711 4.63278C4.17219 4.66604 4.42383 4.71922 4.68875 4.77906V4.29373C4.68875 3.78839 4.58273 3.43608 4.37742 3.22996C4.16555 3.02384 3.80789 2.92408 3.29797 2.92408C3.06617 2.92408 2.82781 2.95075 2.58273 3.01059C2.33766 3.07043 2.0993 3.14353 1.8675 3.23663C1.76156 3.28314 1.68211 3.30973 1.6357 3.32306C1.5893 3.33639 1.55625 3.34298 1.52977 3.34298C1.43703 3.34298 1.3907 3.27647 1.3907 3.13686V2.81106C1.3907 2.70471 1.40398 2.62494 1.43703 2.57843C1.47016 2.53184 1.52977 2.48533 1.6225 2.43882C1.85427 2.31908 2.1324 2.21935 2.45688 2.13961C2.78148 2.05318 3.12586 2.01333 3.49008 2.01333C4.2782 2.01333 4.85438 2.19278 5.22523 2.55184C5.58945 2.91082 5.77492 3.456 5.77492 4.18737V6.34141H5.78805ZM3.0993 7.352C3.31789 7.352 3.54305 7.31216 3.78141 7.23231C4.01984 7.15255 4.2318 7.00627 4.41055 6.80682C4.51656 6.68055 4.59602 6.54094 4.6357 6.38133C4.67547 6.2218 4.70195 6.02894 4.70195 5.8029V5.52369C4.50111 5.47465 4.29769 5.43691 4.09266 5.41067C3.88619 5.38437 3.67828 5.37103 3.47016 5.37074C3.02641 5.37074 2.70195 5.45718 2.48344 5.63671C2.26492 5.81624 2.15891 6.06886 2.15891 6.40125C2.15891 6.71373 2.23836 6.94643 2.40391 7.10604C2.56289 7.27223 2.79469 7.352 3.0993 7.352ZM8.41719 8.07004C8.29797 8.07004 8.21852 8.05012 8.16555 8.00353C8.11258 7.96369 8.06617 7.87059 8.02648 7.74431L6.47023 2.60502C6.43039 2.472 6.41055 2.38557 6.41055 2.33906C6.41055 2.23271 6.46352 2.17278 6.56953 2.17278H7.21852C7.3443 2.17278 7.43047 2.19278 7.4768 2.23929C7.52977 2.27922 7.56953 2.37231 7.60922 2.49859L8.7218 6.89992L9.75492 2.49859C9.78805 2.36565 9.82781 2.27922 9.8807 2.23929C9.93375 2.19945 10.0265 2.17286 10.1457 2.17286H10.6755C10.8013 2.17286 10.8874 2.19278 10.9403 2.23929C10.9934 2.27922 11.0397 2.37231 11.0662 2.49859L12.1126 6.9531L13.2582 2.49859C13.2979 2.36565 13.3443 2.27922 13.3906 2.23929C13.4436 2.19945 13.5297 2.17286 13.6489 2.17286H14.2648C14.3708 2.17286 14.4304 2.22604 14.4304 2.33906C14.4304 2.37231 14.4237 2.40557 14.4171 2.44541C14.4105 2.48525 14.3973 2.53851 14.3708 2.61169L12.7747 7.7509C12.735 7.88392 12.6886 7.97035 12.6356 8.0102C12.5827 8.05012 12.4966 8.07671 12.3841 8.07671H11.8145C11.6887 8.07671 11.6026 8.05678 11.5495 8.0102C11.4966 7.96369 11.4502 7.87725 11.4238 7.74431L10.3972 3.456L9.37734 7.73757C9.3443 7.87059 9.30453 7.95702 9.25156 8.00353C9.19859 8.05012 9.10586 8.07004 8.98672 8.07004H8.41719ZM16.9271 8.24957C16.5827 8.24957 16.2384 8.20965 15.9073 8.12988C15.5761 8.05012 15.3179 7.96361 15.1457 7.864C15.0397 7.80408 14.9668 7.73765 14.9404 7.6778C14.9146 7.61911 14.9011 7.55574 14.9006 7.49161V7.15255C14.9006 7.01294 14.9536 6.94643 15.053 6.94643C15.0935 6.94658 15.1338 6.95334 15.1722 6.96643C15.2119 6.97976 15.2715 7.00627 15.3377 7.03286C15.5716 7.13621 15.8158 7.21422 16.0662 7.26557C16.3256 7.31837 16.5896 7.34509 16.8543 7.34533C17.2715 7.34533 17.596 7.27224 17.8212 7.12596C18.0463 6.97969 18.1655 6.76698 18.1655 6.49435C18.1655 6.30824 18.1059 6.15529 17.9867 6.02894C17.8675 5.90259 17.6423 5.78965 17.3179 5.68322L16.3576 5.38408C15.8741 5.23114 15.5166 5.0051 15.298 4.70588C15.0795 4.41333 14.9669 4.08761 14.9669 3.74188C14.9669 3.46267 15.0265 3.21665 15.1457 3.00384C15.2648 2.79114 15.4238 2.60502 15.6225 2.45875C15.8212 2.3058 16.0463 2.19278 16.3113 2.11302C16.5761 2.03325 16.8542 2 17.1456 2C17.2913 2 17.4437 2.00667 17.5894 2.02659C17.7417 2.04651 17.8808 2.0731 18.0198 2.09969C18.1523 2.13294 18.2781 2.1662 18.3973 2.20612C18.5165 2.24596 18.6092 2.28583 18.6755 2.32573C18.7682 2.37898 18.8344 2.43216 18.8741 2.492C18.9139 2.54518 18.9338 2.6183 18.9338 2.71137V3.02384C18.9338 3.16345 18.8808 3.23663 18.7814 3.23663C18.7284 3.23663 18.6423 3.20996 18.5298 3.15678C18.1522 2.98392 17.7284 2.89749 17.2583 2.89749C16.8808 2.89749 16.5827 2.95733 16.3774 3.08369C16.1722 3.20996 16.0662 3.40282 16.0662 3.67537C16.0662 3.86157 16.1324 4.0211 16.2648 4.14745C16.3973 4.2738 16.6423 4.40008 16.9934 4.5131L17.9337 4.81231C18.4105 4.96525 18.7549 5.17796 18.9602 5.45051C19.1655 5.72306 19.2649 6.03561 19.2649 6.38133C19.2649 6.66722 19.2052 6.92651 19.0927 7.15255C18.9735 7.37859 18.8145 7.57804 18.6092 7.73765C18.4039 7.90384 18.1589 8.02353 17.8741 8.10996C17.5761 8.20306 17.2648 8.24957 16.9271 8.24957Z"
        fill="#252F3E"
      />
      <path
        d="M18.0464 11.4874C15.8676 13.103 12.702 13.9606 9.9802 13.9606C6.16559 13.9606 2.72856 12.5445 0.132544 10.1909C-0.0727688 10.0048 0.112622 9.75215 0.357622 9.89835C3.16559 11.534 6.62918 12.5245 10.212 12.5245C12.6292 12.5245 15.2848 12.0193 17.7286 10.9821C18.0928 10.8158 18.404 11.2215 18.0464 11.4874ZM18.9537 10.4502C18.6756 10.0912 17.1126 10.2773 16.404 10.3638C16.1921 10.3904 16.159 10.2042 16.3511 10.0646C17.5961 9.18697 19.6425 9.43968 19.8808 9.73215C20.1193 10.0314 19.8146 12.0857 18.649 13.0697C18.4703 13.2227 18.2981 13.1429 18.3775 12.9434C18.6424 12.2852 19.2318 10.8026 18.9537 10.4502Z"
        fill="#FF9900"
      />
    </svg>
  );
}

export function Aws({ withPin, className, size }: PinnableIconProps): React.ReactElement {
  const iconElement = withPin ? (
    <AwsIconSvgComponent
      width={AWS_ICON_NOMINAL_WIDTH}
      height={AWS_ICON_NOMINAL_HEIGHT}
    />
  ) : (
    <AwsIconSvgComponent size={size} />
  );

  return (
    <IconWrapper
      iconElement={iconElement}
      iconNominalWidth={AWS_ICON_NOMINAL_WIDTH}
      iconNominalHeight={AWS_ICON_NOMINAL_HEIGHT}
      withPin={withPin}
      className={className}
    />
  );
}
