export const getSentryUuid = () => {
  // Retrieve the UUID from localStorage or generate a new one if it doesn't exist
  let sentryUuid = localStorage.getItem('sentry_uuid');
  // Check if the UUID is valid
  if (!sentryUuid) {
    // Generate a new UUID using the crypto.randomUUID() to ensure it's unique
    sentryUuid = crypto.randomUUID();
    // Store the UUID in localStorage so it's available on subsequent visits
    localStorage.setItem('sentry_uuid', sentryUuid);
  }
  return sentryUuid;
};
