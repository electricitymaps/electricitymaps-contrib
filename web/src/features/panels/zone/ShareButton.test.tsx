import { ToastProvider } from '@radix-ui/react-toast';
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { describe, expect, test } from 'vitest';

import { ShareButton } from './ShareButton';

const navMocks = vi.hoisted(() => ({
  share: vi.fn(),
  canShare: vi.fn(),
  clipboard: {
    writeText: vi.fn(),
  },
}));

Object.defineProperty(window.navigator, 'share', { value: navMocks.share });
Object.defineProperty(window.navigator, 'canShare', { value: navMocks.canShare });
Object.defineProperty(window.navigator, 'clipboard', {
  value: {
    writeText: navMocks.clipboard.writeText,
  },
});

const utilMocks = vi.hoisted(() => ({
  isMobile: vi.fn(),
  isiOS: vi.fn(),
}));

vi.mock('features/weather-layers/wind-layer/util', () => utilMocks);

const ffMocks = vi.hoisted(() => ({
  useFeatureFlag: vi.fn(),
}));

vi.mock('features/feature-flags/api', () => ffMocks);

describe('ShareButton', () => {
  beforeEach(() => {
    ffMocks.useFeatureFlag.mockReturnValue(true);
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  test('does not render', () => {
    ffMocks.useFeatureFlag.mockReturnValue(false);
    render(
      <ToastProvider>
        <ShareButton />
      </ToastProvider>
    );
    expect(screen.queryByRole('button')).toBeNull();
  });

  test('renders', () => {
    render(
      <ToastProvider>
        <ShareButton />
      </ToastProvider>
    );
    expect(screen.getByRole('button')).toBeDefined();
  });

  describe('share icon', () => {
    test('uses iOS share icon on iOS', () => {
      utilMocks.isiOS.mockReturnValue(true);
      render(
        <ToastProvider>
          <ShareButton />
        </ToastProvider>
      );
      expect(screen.getByTestId('iosShareIcon')).toBeDefined();
    });

    test('uses iOS share icon on iOS', () => {
      utilMocks.isiOS.mockReturnValue(false);
      render(
        <ToastProvider>
          <ShareButton />
        </ToastProvider>
      );
      expect(screen.getByTestId('defaultShareIcon')).toBeDefined();
    });
  });

  test('uses navigator if on mobile and can share', async () => {
    navMocks.canShare.mockReturnValue(true);
    utilMocks.isMobile.mockReturnValue(true);
    render(
      <ToastProvider>
        <ShareButton />
      </ToastProvider>
    );
    expect(window.navigator.share).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole('button'));
    expect(window.navigator.share).toHaveBeenCalled();
  });

  describe('copies to clipboard', () => {
    test('if not on mobile', async () => {
      navMocks.canShare.mockReturnValue(true);
      utilMocks.isMobile.mockReturnValue(false);
      render(
        <ToastProvider>
          <ShareButton />
        </ToastProvider>
      );
      expect(window.navigator.clipboard.writeText).not.toHaveBeenCalled();
      await userEvent.click(screen.getByRole('button'));
      expect(window.navigator.clipboard.writeText).toHaveBeenCalled();
      expect(window.navigator.share).not.toHaveBeenCalled();
    });

    test('if navigator.share is not available', async () => {
      navMocks.canShare.mockReturnValue(false);
      utilMocks.isMobile.mockReturnValue(true);
      render(
        <ToastProvider>
          <ShareButton />
        </ToastProvider>
      );
      expect(window.navigator.clipboard.writeText).not.toHaveBeenCalled();
      await userEvent.click(screen.getByRole('button'));
      expect(window.navigator.clipboard.writeText).toHaveBeenCalled();
      expect(window.navigator.share).not.toHaveBeenCalled();
    });
  });
});
