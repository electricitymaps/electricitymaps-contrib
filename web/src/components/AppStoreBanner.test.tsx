import { Capacitor } from '@capacitor/core';
import { render, renderHook, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { useAtom } from 'jotai';
import { TestProvider } from 'testing/testUtils';
import { describe, expect, test, vi } from 'vitest';

import { AppStoreBanner, appStoreDismissedAtom, AppStoreURLs } from './AppStoreBanner';

vi.mock('@capacitor/core', () => ({
  Capacitor: {
    isNativePlatform: vi.fn(),
  },
}));

Object.defineProperty(navigator, 'userAgent', {
  value: 'android',
  configurable: true,
});

describe('AppStoreBanner', () => {
  beforeEach(() => {
    vi.mocked(Capacitor.isNativePlatform).mockReturnValue(false);
  });
  afterEach(() => {
    vi.restoreAllMocks();
    const { result } = renderHook(() => useAtom(appStoreDismissedAtom));
    result.current[1](false);
  });

  test('renders when isAppBannerDismissed is undefined', () => {
    render(<AppStoreBanner />);

    expect(screen.getByRole('banner')).toBeDefined();
  });

  test('does not render when isAppBannerDismissed is true', () => {
    render(
      <TestProvider initialValues={[[appStoreDismissedAtom, true]]}>
        <AppStoreBanner />
      </TestProvider>
    );

    expect(screen.queryAllByRole('banner')).toHaveLength(0);
  });

  test('clicking dismiss sets local storage', async () => {
    render(<AppStoreBanner />);

    await userEvent.click(screen.getByTestId('dismiss-btn'));

    expect(screen.queryAllByRole('banner')).toHaveLength(0);
  });

  test('clicking cta button sets local storage', async () => {
    render(<AppStoreBanner />);

    await userEvent.click(screen.getByText('app-banner.cta'));

    expect(screen.queryAllByRole('banner')).toHaveLength(0);
  });

  test('cta href should match on android', () => {
    render(<AppStoreBanner />);

    const node = screen.getByText('app-banner.cta');
    expect(node.getAttribute('href')).toBe(AppStoreURLs.GOOGLE);
  });

  test('cta href should match on iphone', () => {
    Object.defineProperty(navigator, 'userAgent', {
      value: 'iPhone',
      configurable: true,
    });
    render(<AppStoreBanner />);

    const node = screen.getByText('app-banner.cta');
    expect(node.getAttribute('href')).toBe(AppStoreURLs.APPLE);
  });

  test('does not render if on native app', () => {
    vi.mocked(Capacitor.isNativePlatform).mockReturnValue(true);

    render(<AppStoreBanner />);

    expect(screen.queryAllByRole('banner')).toHaveLength(0);
  });
});
