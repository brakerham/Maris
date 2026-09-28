export interface ChartAdapter<Data> {
  readonly id: string;
  render(element: HTMLElement, data: Data): void;
  destroy(): void;
}
