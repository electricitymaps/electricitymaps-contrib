import App from 'App';
import renderWithProviders from 'testing/testUtils';

describe('<App />', () => {
  it('renders', async () => {
    window.history.pushState({}, 'Home', '/');
    renderWithProviders(<App />, false);
  });
});
