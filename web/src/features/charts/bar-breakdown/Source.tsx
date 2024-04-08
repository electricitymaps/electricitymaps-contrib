export function Source({
  title,
  icon,
  sources,
}: {
  title: string;
  icon: React.ReactNode;
  sources: string[];
}) {
  return (
    <div className="flex flex-col py-2">
      <div className="flex flex-row pb-2">
        <div className="mr-1">{icon}</div>
        <div className="text-md font-semibold">{title}</div>
      </div>
      <div className="flex flex-col gap-2 pl-5">
        {sources.map((source, index) => (
          <div key={index} className="text-xm">
            {source}
          </div>
        ))}
      </div>
    </div>
  );
}
