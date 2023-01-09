import { ReactElement } from 'react';
import { HiArrowLeft } from 'react-icons/hi2';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from '../../../translation/translation';
import FAQContent from './FAQContent';

export default function FAQPanel(): ReactElement {
  const { __ } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const createUrlWithState = (to: string) => `${to}${location.search}${location.hash}`;

  const isMobile = false; // TODO: Replace this

  const parentPage = {
    pathname: isMobile ? '/info' : '/map',
    search: location.search,
  };

  // FAQ section is embedded on the /info page on mobile screens
  if (isMobile) {
    navigate(createUrlWithState('/info'));
  }

  return (
    <div className="pt-4 pl-2 ">
      <div className="mb-2 flex flex-row pl-2">
        <Link to={parentPage} className="text-3xl mr-4 self-center">
          <HiArrowLeft />
        </Link>
        <h2 className="font-poppins text-lg font-medium">{__('misc.faq')}</h2>
      </div>
      <div className="h-[calc(100vh-330px)] overflow-y-scroll shadow-[inset_0px_-11px_8px_-12px_rgba(0,0,0,0.2)]">
        <FAQContent />
      </div>
      <div className=" mt-2 hidden space-x-4 text-center text-sm md:block">
        <a
          className="text-brand-green underline hover:text-gray-500 dark:text-brand-yellow"
          href="https://www.electricitymaps.com/privacy-policy/"
        >
          {__('misc.privacyPolicy')}
        </a>
        <a
          className="text-brand-green underline hover:text-gray-500 dark:text-brand-yellow"
          href="https://www.electricitymaps.com/legal-notice/"
        >
          {__('misc.legalNotice')}
        </a>
      </div>
    </div>
  );
}
