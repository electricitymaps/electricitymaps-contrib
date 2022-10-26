import getFruits from 'api/getFruits';
import Head from 'components/Head';
import ImageAttribution from 'components/ImageAttribution';
import LoadingOrError from 'components/LoadingOrError';
import type { ReactElement } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, Navigate, useParams } from 'react-router-dom';
import { useMediaQuery } from 'utils';

const DESKTOP_IMAGE_WIDTH_PERCENTAGE = 0.4;
const MOBILE_IMAGE_HEIGHT_PERCENTAGE = 0.3;

export default function DetailsPage(): ReactElement {
  const isTabletAndUp = useMediaQuery('(min-width: 600px)');
  const { fruitName } = useParams();

  const { isLoading, isError, error, data } = useQuery(['fruits'], getFruits);
  if (isLoading || isError) {
    return <LoadingOrError error={error as Error} />;
  }

  const fruit = data.find((f) => f.name.toLowerCase() === fruitName?.toLowerCase());
  if (!fruit) {
    return <Navigate to="/" replace />;
  }

  const imageWidth =
    (isTabletAndUp ? window.innerWidth * DESKTOP_IMAGE_WIDTH_PERCENTAGE : window.innerWidth) * window.devicePixelRatio;
  const imageHeight =
    (isTabletAndUp ? window.innerHeight : window.innerHeight * MOBILE_IMAGE_HEIGHT_PERCENTAGE) *
    window.devicePixelRatio;

  return (
    <>
      <Head title={fruit.name} />
      <div className="flex min-h-screen flex-col items-center sm:flex-row">
        <div className="relative">
          <img
            data-testid="FruitImage"
            width={imageWidth}
            height={imageHeight}
            style={{
              backgroundColor: fruit.image.color,
            }}
            src={`${fruit.image.url}&w=${imageWidth}&h=${imageHeight}`}
            alt={fruit.name}
          />
          <ImageAttribution author={fruit.image.author} />
        </div>
        <div className="my-8 sm:my-0 sm:ml-16">
          <Link data-testid="BackLink" to="/" className="flex items-center">
            <img src="/icons/arrow-left.svg" alt="" className="h-5 w-5" />
            <span className="ml-4 text-xl">Back</span>
          </Link>

          <h1 data-testid="FruitName" className="mt-2 text-6xl font-bold sm:mt-8">
            {fruit.name}
          </h1>
          <h2 className="mt-3 text-xl text-gray-500 dark:text-gray-400">Vitamins per 100 g (3.5 oz)</h2>
          <table className="mt-8 text-lg">
            <thead>
              <tr>
                <th className="px-4 py-2">Vitamin</th>
                <th className="px-4 py-2">Quantity</th>
              </tr>
            </thead>
            <tbody>
              {fruit.metadata.map(({ name, value }) => (
                <tr key={`FruitVitamin-${name}`} className="font-medium">
                  <td className="border border-gray-300 px-4 py-2">{name}</td>
                  <td className="border border-gray-300 px-4 py-2">{value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
