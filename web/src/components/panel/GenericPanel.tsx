import { X } from 'lucide-react';
import React from 'react';
import { twMerge } from 'tailwind-merge';

import GlassContainer from '../GlassContainer'; // Adjust path as needed
import LoadingSpinner from '../LoadingSpinner'; // Adjust path as needed

interface GenericPanelProps {
  children: React.ReactNode;
  isLoading?: boolean;
  error?: string | React.ReactNode;
  className?: string;
  contentClassName?: string;
  headerHeight?: string;

  // Props for built-in header (used if renderFullHeader is not provided)
  title?: string; // Title becomes optional if custom full header is used
  iconSrc?: string;
  onClose?: () => void;

  customHeaderStartContent?: React.ReactNode; // New: For content at the start of the header (e.g., back button)
  customHeaderEndContent?: React.ReactNode; // Renamed: For content at the end (e.g., action buttons)

  // Prop for rendering a completely custom header
  renderFullHeader?: () => React.ReactNode;
}

function GenericPanel({
  children,
  isLoading = false,
  error = null,
  className = '',
  contentClassName = '',
  headerHeight = '57px',
  title,
  iconSrc,
  onClose,
  customHeaderStartContent,
  customHeaderEndContent,
  renderFullHeader,
}: GenericPanelProps): JSX.Element {
  const actualHeaderHeight = renderFullHeader ? headerHeight : '57px';

  return (
    <GlassContainer
      className={twMerge(
        'pointer-events-auto z-[21] flex h-full flex-col border-0 transition-all duration-500 sm:inset-3 sm:bottom-[8.5rem] sm:h-auto sm:border sm:pt-0',
        'pt-[max(2.5rem,env(safe-area-inset-top))] sm:pt-0',
        className
      )}
    >
      {renderFullHeader
        ? renderFullHeader()
        : // Render built-in header only if title is provided (as a proxy for wanting the built-in header)
          // Or if custom start/end content is provided, as they need a header bar.
          (title || customHeaderStartContent || customHeaderEndContent) && (
            <header
              className={twMerge(
                'flex items-center justify-between border-b border-neutral-200/60 p-3 dark:border-neutral-700/60'
              )}
            >
              <div className="flex min-w-0 flex-grow items-center">
                {' '}
                {/* Container for left and middle elements */}
                {customHeaderStartContent && (
                  <div className="mr-2 flex-shrink-0">{customHeaderStartContent}</div>
                )}
                {iconSrc && title && (
                  <img src={iconSrc} alt={title} className="mr-2 h-5 w-5 flex-shrink-0" />
                )}
                {title && (
                  <h2 className="truncate text-lg font-semibold text-gray-800 dark:text-gray-100">
                    {title}
                  </h2>
                )}
              </div>
              <div className="ml-auto flex flex-shrink-0 items-center pl-2">
                {' '}
                {/* Container for right elements */}
                {customHeaderEndContent && (
                  <div className="flex-shrink-0">{customHeaderEndContent}</div>
                )}
                {onClose && (
                  <button
                    onClick={onClose}
                    className="ml-2 flex-shrink-0 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                    aria-label="Close panel"
                  >
                    <X className="h-6 w-6" />
                  </button>
                )}
              </div>
            </header>
          )}
      <div
        id="generic-panel-scroller"
        className={twMerge(
          'flex-1 overflow-y-auto',
          `sm:h-[calc(100%-${actualHeaderHeight})]`, // Use actualHeaderHeight
          isLoading || error ? 'flex items-center justify-center' : '', // Remove default padding, let contentClassName handle it
          contentClassName // This should now define the padding e.g. 'p-3 md:p-4'
        )}
      >
        {isLoading ? (
          <LoadingSpinner />
        ) : (error ? (
          <div className="p-3 text-center text-red-500 md:p-4">{error}</div>
        ) : (
          children
        ))}
      </div>
    </GlassContainer>
  );
}

export default GenericPanel;
