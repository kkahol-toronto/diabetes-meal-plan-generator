interface Environment {
  API_URL: string;
  APP_NAME: string;
  VERSION: string;
  NODE_ENV: string;
  ENABLE_ANALYTICS: boolean;
  ENABLE_ERROR_REPORTING: boolean;
  MAX_FILE_SIZE: number;
  SUPPORTED_IMAGE_FORMATS: string[];
  API_TIMEOUT: number;
  RETRY_ATTEMPTS: number;
}

const development: Environment = {
  API_URL: 'http://localhost:8000',
  APP_NAME: 'Dietra (Dev)',
  VERSION: '1.0.0-dev',
  NODE_ENV: 'development',
  ENABLE_ANALYTICS: false,
  ENABLE_ERROR_REPORTING: false,
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  SUPPORTED_IMAGE_FORMATS: ['image/jpeg', 'image/png', 'image/webp'],
  API_TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
};

const production: Environment = {
  API_URL: 'https://Dietra-backend.azurewebsites.net', // HARDCODED for deployment
  APP_NAME: 'Dietra',
  VERSION: '1.0.0',
  NODE_ENV: 'production',
  ENABLE_ANALYTICS: true,
  ENABLE_ERROR_REPORTING: true,
  MAX_FILE_SIZE: 5 * 1024 * 1024, // 5MB
  SUPPORTED_IMAGE_FORMATS: ['image/jpeg', 'image/png', 'image/webp'],
  API_TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
};

const test: Environment = {
  API_URL: 'http://localhost:8000',
  APP_NAME: 'Dietra (Test)',
  VERSION: '1.0.0-test',
  NODE_ENV: 'test',
  ENABLE_ANALYTICS: false,
  ENABLE_ERROR_REPORTING: false,
  MAX_FILE_SIZE: 1 * 1024 * 1024, // 1MB
  SUPPORTED_IMAGE_FORMATS: ['image/jpeg', 'image/png'],
  API_TIMEOUT: 10000,
  RETRY_ATTEMPTS: 1,
};

const getEnvironment = (): Environment => {
  // Check if we're in production (deployed) or development
  if (process.env.NODE_ENV === 'production') {
    return production;
  }
  // Use development config for local development
  return development;
};

export const config = getEnvironment();

export default config; 