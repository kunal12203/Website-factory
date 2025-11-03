'use client';

import { useState, useEffect } from 'react';
import { PromptInput } from './PromptInput';
import { ConfigPanel } from './ConfigPanel';
import { ProgressTracker } from './ProgressTracker';
import { ResultDisplay } from './ResultDisplay';
import { ErrorBoundary } from './ErrorBoundary';
import { WebsiteConfig, GenerationStatus, GenerationResult } from '@/lib/types';
import {
  DEFAULT_COLORS,
  GENERATION_STAGES,
  PROGRESS_PERCENTAGES,
  ERROR_MESSAGES,
} from '@/lib/constants';
import { validateWebsiteConfig } from '@/lib/validation';
import { generateWebsite, checkBackendHealth, APIException } from '@/lib/api';
import { convertPromptToChecklist } from '@/lib/promptConverter';

export default function WebsiteBuilder() {
  const [config, setConfig] = useState<WebsiteConfig>({
    prompt: '',
    primaryColor: DEFAULT_COLORS.primary,
    secondaryColor: DEFAULT_COLORS.secondary,
    accentColor: DEFAULT_COLORS.accent,
    additionalPages: [],
  });

  const [status, setStatus] = useState<GenerationStatus>({
    stage: GENERATION_STAGES.IDLE,
    message: 'Ready to build your website',
    progress: 0,
  });

  const [result, setResult] = useState<GenerationResult | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  // Check backend health on mount
  useEffect(() => {
    checkBackendHealth().then(setBackendHealthy);
  }, []);

  const handleGenerate = async () => {
    // Clear previous errors
    setValidationErrors([]);

    // Validate configuration
    const validation = validateWebsiteConfig(config);
    if (!validation.isValid) {
      setValidationErrors(validation.errors);
      return;
    }

    // Check backend health first
    if (backendHealthy === false) {
      setValidationErrors([ERROR_MESSAGES.API_CONNECTION_ERROR]);
      return;
    }

    setIsGenerating(true);
    setStatus({
      stage: GENERATION_STAGES.PLANNING,
      message: 'Converting your prompt into a website plan...',
      progress: PROGRESS_PERCENTAGES[GENERATION_STAGES.PLANNING],
    });

    try {
      // Convert natural language prompt to structured checklist
      const checklist = await convertPromptToChecklist(config);

      setStatus({
        stage: GENERATION_STAGES.PHASE1_COMPONENTS,
        message: 'Generating all frontend components...',
        progress: PROGRESS_PERCENTAGES[GENERATION_STAGES.PHASE1_COMPONENTS],
      });

      // Call the backend API to generate the website
      // The backend will progress through all phases
      const data = await generateWebsite({ checklist });

      setStatus({
        stage: GENERATION_STAGES.FINAL_TESTING,
        message: 'Running final tests...',
        progress: PROGRESS_PERCENTAGES[GENERATION_STAGES.FINAL_TESTING],
      });

      // Simulate a small delay for better UX
      await new Promise((resolve) => setTimeout(resolve, 1000));

      setStatus({
        stage: GENERATION_STAGES.COMPLETE,
        message: 'Website generated successfully!',
        progress: PROGRESS_PERCENTAGES[GENERATION_STAGES.COMPLETE],
      });

      setResult(data);
    } catch (error) {
      console.error('Generation error:', error);

      let errorMessage: string = ERROR_MESSAGES.UNKNOWN_ERROR;

      if (error instanceof APIException) {
        errorMessage = error.message;
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }

      setStatus({
        stage: GENERATION_STAGES.ERROR,
        message: errorMessage,
        progress: 0,
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleReset = () => {
    setConfig({
      prompt: '',
      primaryColor: DEFAULT_COLORS.primary,
      secondaryColor: DEFAULT_COLORS.secondary,
      accentColor: DEFAULT_COLORS.accent,
      additionalPages: [],
    });
    setStatus({
      stage: GENERATION_STAGES.IDLE,
      message: 'Ready to build your website',
      progress: 0,
    });
    setResult(null);
    setValidationErrors([]);
  };

  const handleRetryHealthCheck = async () => {
    setBackendHealthy(null);
    const healthy = await checkBackendHealth();
    setBackendHealthy(healthy);
  };

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        <div className="container mx-auto px-4 py-8">
          <header className="text-center mb-12">
            <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
              AI Website Factory
            </h1>
            <p className="text-lg text-slate-600 dark:text-slate-300">
              Describe your dream website, and watch it come to life
            </p>

            {/* Backend Health Status */}
            {backendHealthy === false && (
              <div className="mt-4 max-w-2xl mx-auto p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <p className="text-red-700 dark:text-red-300 mb-2">
                  ⚠️ Cannot connect to the backend API. Make sure it is running on port
                  8000.
                </p>
                <button
                  onClick={handleRetryHealthCheck}
                  className="text-sm text-red-600 dark:text-red-400 underline hover:no-underline"
                >
                  Retry Connection
                </button>
              </div>
            )}

            {backendHealthy === true && (
              <div className="mt-4 max-w-2xl mx-auto p-2 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                <p className="text-sm text-green-700 dark:text-green-300">
                  ✓ Backend API is connected and ready
                </p>
              </div>
            )}
          </header>

          {/* Validation Errors */}
          {validationErrors.length > 0 && (
            <div className="max-w-4xl mx-auto mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <h3 className="font-semibold text-red-800 dark:text-red-200 mb-2">
                Please fix the following errors:
              </h3>
              <ul className="list-disc list-inside text-red-700 dark:text-red-300">
                {validationErrors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          )}

          {status.stage === GENERATION_STAGES.IDLE ||
          status.stage === GENERATION_STAGES.ERROR ? (
            <div className="grid lg:grid-cols-2 gap-8">
              <div className="space-y-6">
                <PromptInput
                  value={config.prompt}
                  onChange={(prompt) => setConfig({ ...config, prompt })}
                  disabled={isGenerating}
                />
                <ConfigPanel
                  config={config}
                  onChange={setConfig}
                  disabled={isGenerating}
                />
              </div>
              <div className="flex items-center justify-center">
                <div className="text-center space-y-6 p-8 bg-white dark:bg-slate-800 rounded-2xl shadow-xl">
                  <div className="text-6xl mb-4">🚀</div>
                  <h3 className="text-2xl font-semibold text-slate-800 dark:text-slate-100">
                    Ready to Build?
                  </h3>
                  <p className="text-slate-600 dark:text-slate-300">
                    Just describe your website in plain English, customize the colors,
                    and let AI handle the rest.
                  </p>
                  <button
                    onClick={handleGenerate}
                    disabled={
                      isGenerating ||
                      !config.prompt.trim() ||
                      backendHealthy === false
                    }
                    className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-full font-semibold text-lg hover:shadow-lg transform hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                  >
                    {isGenerating ? 'Generating...' : 'Generate Website'}
                  </button>
                  {status.stage === GENERATION_STAGES.ERROR && (
                    <div className="mt-4 p-4 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-lg">
                      <p className="text-red-700 dark:text-red-300 font-medium mb-2">
                        Generation Failed
                      </p>
                      <p className="text-red-600 dark:text-red-400 text-sm mb-3">
                        {status.message}
                      </p>
                      <button
                        onClick={handleReset}
                        className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                      >
                        Try Again
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : status.stage === GENERATION_STAGES.COMPLETE && result ? (
            <ResultDisplay result={result} onReset={handleReset} />
          ) : (
            <ProgressTracker status={status} />
          )}
        </div>
      </div>
    </ErrorBoundary>
  );
}
