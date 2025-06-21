import Badge from 'components/Badge';
import { useTranslation } from 'react-i18next';

export default function NoDataBadge() {
  const { t } = useTranslation();

  return <Badge pillText={t(($) => $.tooltips.noParserInfo)} />;
}
