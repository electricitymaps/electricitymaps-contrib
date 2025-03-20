interface EstimationLegendProps {
  text: string;
}

/**
 * A legend component that shows a square followed by text to indicate estimated data.
 */
function EstimationLegend({ text }: EstimationLegendProps) {
  return (
    <div className="flex items-center gap-1">
      <div
        style={{
          borderRadius: '2px',
          background: 'rgba(82, 82, 82, 0.10)',
          height: '14px',
          width: '14px',
        }}
        aria-hidden="true"
      />
      <span className="text-secondary text-xs">{text}</span>
    </div>
  );
}

export default EstimationLegend;
