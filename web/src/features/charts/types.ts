export interface AreaGraphElement {
  datetime: Date;
  meta: any; // TODO: investigate whether this can be removed after tooltips are implemented
  layerData: { [layerKey: string]: number };
}
