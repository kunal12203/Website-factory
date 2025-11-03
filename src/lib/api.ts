/**
 * API utilities with retry logic and error handling
 */

import {
  GenerateWebsiteRequest,
  GenerateWebsiteResponse,
  APIError,
} from './types';
import {
  API_BASE_URL,
  API_TIMEOUT,
  API_RETRY_ATTEMPTS,
  API_RETRY_DELAY,
  ERROR_MESSAGES,
} from './constants';

/**
 * Custom API Error class
 */
export class APIException extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public detail?: string
  ) {
    super(message);
    this.name = 'APIException';
  }
}

/**
 * Sleep utility for retry delays
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Parse API error response
 */
function parseAPIError(error: APIError): string {
  if (error.message) return error.message;
  if (error.detail) return error.detail;
  if (error.error) return error.error;
  return ERROR_MESSAGES.UNKNOWN_ERROR;
}

/**
 * Check if the backend is reachable
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(`${API_BASE_URL}/health`, {
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    return response.ok;
  } catch (error) {
    console.error('Backend health check failed:', error);
    return false;
  }
}

/**
 * Fetch with timeout
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeout: number = API_TIMEOUT
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      throw new APIException(ERROR_MESSAGES.API_TIMEOUT);
    }
    throw error;
  }
}

/**
 * Fetch with retry logic
 */
async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  retries: number = API_RETRY_ATTEMPTS
): Promise<Response> {
  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const response = await fetchWithTimeout(url, options);

      // Only retry on 5xx errors or network errors
      if (response.ok || (response.status >= 400 && response.status < 500)) {
        return response;
      }

      // If it's a 5xx error and we have retries left, continue
      if (attempt < retries) {
        console.warn(
          `Request failed with status ${response.status}. Retrying (${attempt}/${retries})...`
        );
        await sleep(API_RETRY_DELAY * attempt); // Exponential backoff
        continue;
      }

      return response;
    } catch (error) {
      lastError = error as Error;

      if (attempt < retries) {
        console.warn(
          `Request failed: ${lastError.message}. Retrying (${attempt}/${retries})...`
        );
        await sleep(API_RETRY_DELAY * attempt); // Exponential backoff
      }
    }
  }

  // If we've exhausted all retries
  throw new APIException(
    ERROR_MESSAGES.API_CONNECTION_ERROR,
    undefined,
    lastError?.message
  );
}

/**
 * Generate website via API
 */
export async function generateWebsite(
  request: GenerateWebsiteRequest
): Promise<GenerateWebsiteResponse> {
  try {
    // First check if backend is healthy
    const isHealthy = await checkBackendHealth();
    if (!isHealthy) {
      throw new APIException(ERROR_MESSAGES.API_CONNECTION_ERROR);
    }

    // Make the generation request
    const response = await fetchWithRetry(`${API_BASE_URL}/api/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    // Handle response
    if (!response.ok) {
      const errorData: APIError = await response.json().catch(() => ({}));
      const errorMessage = parseAPIError(errorData);

      throw new APIException(
        errorMessage,
        response.status,
        errorData.detail
      );
    }

    const data: GenerateWebsiteResponse = await response.json();

    // Normalize the response
    return {
      ...data,
      output_path: data.output_path || data.outputPath,
    };
  } catch (error) {
    if (error instanceof APIException) {
      throw error;
    }

    if (error instanceof Error) {
      if (error.message.includes('Failed to fetch')) {
        throw new APIException(ERROR_MESSAGES.API_CONNECTION_ERROR);
      }
      throw new APIException(error.message);
    }

    throw new APIException(ERROR_MESSAGES.UNKNOWN_ERROR);
  }
}

/**
 * Get API health status
 */
export async function getHealthStatus(): Promise<{
  status: string;
  ai_provider?: string;
  ai_model?: string;
}> {
  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/health`, {}, 5000);

    if (!response.ok) {
      throw new Error('Health check failed');
    }

    return await response.json();
  } catch {
    throw new APIException('Failed to check API health');
  }
}
