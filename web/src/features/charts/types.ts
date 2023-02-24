import { ElectricityModeType, ZoneDetail, ZoneKey } from 'types';

export interface AreaGraphElement {
  datetime: Date;
  meta: ZoneDetail;
  layerData: { [layerKey: LayerKey]: number };
}

export interface InnerAreaGraphTooltipProps {
  zoneDetail?: ZoneDetail;
  selectedLayerKey?: LayerKey;
}

export type LayerKey = ZoneKey | ElectricityModeType;
