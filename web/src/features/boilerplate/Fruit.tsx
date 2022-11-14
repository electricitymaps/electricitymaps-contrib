import ImageAttribution from 'components/ImageAttribution';
import type { KeyboardEvent, ReactElement } from 'react';
import { useNavigate } from 'react-router-dom';
import type { IFruit } from 'types';
import { useMediaQuery } from 'utils';

const PREFERRED_IMAGE_WIDTH = 384;
const MOBILE_PADDING = 16;
const ASPECT_RATIO_WIDTH = 16;
const ASPECT_RATIO_HEIGHT = 9;
const IMAGE_INDEX_BELOW_THE_FOLD = 3;

interface Properties {
  fruit: IFruit;
  index: number;
}

export default function Fruit({ fruit, index }: Properties): ReactElement {
  const isTabletAndUp = useMediaQuery('(min-width: 600px)');

  const navigate = useNavigate();
  function onClick(): void {
    window.scrollTo(0, 0);
    navigate(fruit.name.toLowerCase());
  }

  function onKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter') {
      onClick();
    }
  }

  const imageWidth = Math.min(PREFERRED_IMAGE_WIDTH, window.innerWidth - MOBILE_PADDING);
  const imageHeight = imageWidth / (ASPECT_RATIO_WIDTH / ASPECT_RATIO_HEIGHT);

  return (
    <div
      data-testid="FruitCard"
      className="cursor-pointer select-none overflow-hidden rounded-lg shadow-lg focus:border-gray-300 focus:outline-none focus:ring focus:ring-gray-500 focus:ring-opacity-50 dark:shadow-2xl"
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={onKeyDown}
    >
      <div className="relative">
        <img
          data-testid="FruitCardImage"
          loading={
            !isTabletAndUp && index >= IMAGE_INDEX_BELOW_THE_FOLD ? 'lazy' : 'eager'
          }
          decoding={
            !isTabletAndUp && index >= IMAGE_INDEX_BELOW_THE_FOLD ? 'async' : 'sync'
          }
          width={imageWidth}
          height={imageHeight}
          style={{
            backgroundColor: fruit.image.color,
          }}
          src={`${fruit.image.url}&w=${imageWidth * window.devicePixelRatio}&h=${
            imageHeight * window.devicePixelRatio
          }`}
          alt={fruit.name}
        />
        <ImageAttribution author={fruit.image.author} />
      </div>
      <h3 data-testid="FruitCardName" className="p-6 text-xl font-bold">
        {fruit.name}
      </h3>
    </div>
  );
}
