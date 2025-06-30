import config from './config/environment';

// Intercept all fetch requests and prepend the API base URL when the request
// starts with "/" (and not "//" which would indicate a protocol-relative URL).
// This removes the need for React-Scripts dev proxy and prevents noisy
// "Proxy error: ECONNREFUSED" messages when the backend is not running.

const { API_URL } = config;

// Detects if a URL looks like an API endpoint that should be proxied to the
// backend. Adjust the prefixes below to match your API surface area.
const API_PREFIXES = [
  '/coach/',
  '/consumption/',
  '/admin/',
  '/api/',
  '/login',
  '/register',
  '/generate',
];

const shouldPrependBase = (url: string): boolean => {
  if (!url.startsWith('/') || url.startsWith('//')) return false; // absolute/protocol-relative
  return API_PREFIXES.some(prefix => url.startsWith(prefix));
};

// Preserve the original window.fetch implementation
const originalFetch: typeof window.fetch = window.fetch.bind(window);

window.fetch = (input: RequestInfo | URL, init?: RequestInit) => {
  try {
    if (typeof input === 'string' && shouldPrependBase(input)) {
      input = `${API_URL}${input}`;
    } else if (input instanceof Request && shouldPrependBase(input.url)) {
      input = new Request(`${API_URL}${input.url}`, input);
    }
  } catch (err) {
    // In extremely unlikely cases (malformed URL, etc.) we fall back to original input
    // and just let the request fail normally.
    console.error('Failed to process fetch interceptor:', err);
  }

  return originalFetch(input as any, init);
};

// Optionally, you can log the patched behaviour in development for debugging.
if (process.env.NODE_ENV === 'development') {
  // eslint-disable-next-line no-console
  console.info('[setupFetchInterceptor] Global fetch interceptor active.');
} 