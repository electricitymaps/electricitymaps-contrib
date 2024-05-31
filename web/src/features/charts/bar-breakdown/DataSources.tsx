import { ElectricityModeType } from 'types';

import ProductionSourceLegend from './ProductionSourceLegend';

export function DataSources({
  title,
  icon,
  sources,
  emissionFactorSourcesToProductionSources,
}: {
  title: string;
  icon: React.ReactNode;
  sources: string[];
  emissionFactorSourcesToProductionSources?: { [key: string]: string[] };
}) {
  const showDataSources = Boolean(
    (sources && sources?.length > 0) || emissionFactorSourcesToProductionSources
  );
  if (showDataSources == false) {
    return null;
  }

  return (
    <div className="flex flex-col py-2">
      <div className="flex flex-row pb-2">
        <div className="mr-1">{icon}</div>
        <div className="text-md font-semibold">{title}</div>
      </div>
      <div className="flex flex-col gap-2 pl-5">
        {sources.sort().map((source, index) => (
          <div key={index} className=" pl-5 text-sm">
            {source}
            {emissionFactorSourcesToProductionSources && (
              <span className="inline-flex translate-y-1 gap-1 pl-1.5">
                {emissionFactorSourcesToProductionSources[source]?.map(
                  (productionSource, index) => (
                    <span key={index} className="self-center object-center text-xs">
                      <ProductionSourceLegend
                        electricityType={productionSource as ElectricityModeType}
                      />
                    </span>
                  )
                )}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
