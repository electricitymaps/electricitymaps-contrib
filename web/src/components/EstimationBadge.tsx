import Badge from 'components/Badge';

export default function EstimationBadge({ text }: { text: string }) {
  return (
    <Badge
      type={'warning'}
      icon={
        "h-[16px] w-[16px] bg-[url('/images/estimated_light.svg')] bg-center dark:bg-[url('/images/estimated_dark.svg')]"
      }
      pillText={text}
    />
  );
}
