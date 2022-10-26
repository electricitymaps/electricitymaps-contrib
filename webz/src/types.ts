export interface IFruit {
  name: string;
  image: {
    author: {
      name: string;
      url: string;
    };
    color: string;
    url: string;
  };
  metadata: {
    name: string;
    value: string;
  }[];
}
