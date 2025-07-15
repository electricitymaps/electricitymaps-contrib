import { RoundedCard } from 'features/charts/RoundedCard';
import { FlaskConicalIcon } from 'lucide-react';
import { memo } from 'react';

export interface ExperimentalCardProps {
  title: string;
  description?: string;
}

function ExperimentalCard({ title, description }: ExperimentalCardProps) {
  return (
    <RoundedCard className="gap-2 border border-info-subtle bg-info-muted px-4 py-2 dark:border-info-subtle-dark dark:bg-info-muted-dark">
      <div className="flex items-center gap-2">
        <FlaskConicalIcon size={16} className="text-info-base dark:text-info-base-dark" />
        <h2 className="text-info-base dark:text-info-base-dark">{title}</h2>
      </div>
      {description && (
        <p className="text-info-base dark:text-info-base-dark">{description}</p>
      )}
    </RoundedCard>
  );
}

export default memo(ExperimentalCard);
