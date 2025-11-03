'use client';

import { useState } from 'react';
import { PromptInput } from './PromptInput';
import { ConfigPanel } from './ConfigPanel';
import { ProgressTracker } from './ProgressTracker';
import { ResultDisplay } from './ResultDisplay';

export interface WebsiteConfig {
  prompt: string;
  primaryColor: string;
  secondaryColor: string;
  accentColor: string;
  additionalPages: string[];
}

export interface GenerationStatus {
  stage: 'idle' | 'planning' | 'building' | 'testing' | 'complete' | 'error';
  message: string;
  progress: number;
}

export interface GenerationResult {
  output_path?: string;
  site_path?: string;
  components_generated?: number;
  pages?: string[];
  total_pages?: number;
  tests_passed?: boolean | string;
  message?: string;
}

export default function WebsiteBuilder() {
  const [config, setConfig] = useState<WebsiteConfig>({
    prompt: '',
    primaryColor: '#3b82f6',
    secondaryColor: '#8b5cf6',
    accentColor: '#10b981',
    additionalPages: [],
  });

  const [status, setStatus] = useState<GenerationStatus>({
    stage: 'idle',
    message: 'Ready to build your website',
    progress: 0,
  });

  const [result, setResult] = useState<GenerationResult | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = async () => {
    if (!config.prompt.trim()) {
      alert('Please enter a description of your website');
      return;
    }

    setIsGenerating(true);
    setStatus({
      stage: 'planning',
      message: 'Converting your prompt into a website plan...',
      progress: 10,
    });

    try {
      // Convert natural language prompt to structured checklist
      const checklist = await convertPromptToChecklist(config);

      setStatus({
        stage: 'building',
        message: 'Building your website components...',
        progress: 30,
      });

      // Call the backend API to generate the website
      const response = await fetch('http://localhost:8000/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ checklist }),
      });

      if (!response.ok) {
        throw new Error(`Generation failed: ${response.statusText}`);
      }

      setStatus({
        stage: 'testing',
        message: 'Testing and validating your website...',
        progress: 80,
      });

      const data = await response.json();

      setStatus({
        stage: 'complete',
        message: 'Website generated successfully!',
        progress: 100,
      });

      setResult(data);
    } catch (error) {
      console.error('Generation error:', error);
      setStatus({
        stage: 'error',
        message: error instanceof Error ? error.message : 'An error occurred',
        progress: 0,
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleReset = () => {
    setConfig({
      prompt: '',
      primaryColor: '#3b82f6',
      secondaryColor: '#8b5cf6',
      accentColor: '#10b981',
      additionalPages: [],
    });
    setStatus({
      stage: 'idle',
      message: 'Ready to build your website',
      progress: 0,
    });
    setResult(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-12">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
            AI Website Factory
          </h1>
          <p className="text-lg text-slate-600 dark:text-slate-300">
            Describe your dream website, and watch it come to life
          </p>
        </header>

        {status.stage === 'idle' || status.stage === 'error' ? (
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
                  Just describe your website in plain English, customize the colors, and
                  let AI handle the rest.
                </p>
                <button
                  onClick={handleGenerate}
                  disabled={isGenerating || !config.prompt.trim()}
                  className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-full font-semibold text-lg hover:shadow-lg transform hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                >
                  {isGenerating ? 'Generating...' : 'Generate Website'}
                </button>
                {status.stage === 'error' && (
                  <div className="mt-4 p-4 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-lg">
                    <p className="text-red-700 dark:text-red-300">{status.message}</p>
                    <button
                      onClick={handleReset}
                      className="mt-2 text-red-600 dark:text-red-400 underline"
                    >
                      Try Again
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : status.stage === 'complete' && result ? (
          <ResultDisplay result={result} onReset={handleReset} />
        ) : (
          <ProgressTracker status={status} />
        )}
      </div>
    </div>
  );
}

interface ChecklistPage {
  name: string;
  path: string;
  sections: Array<{
    component: string;
    props: Record<string, unknown>;
  }>;
}

interface Checklist {
  branding: {
    colors: {
      primary: string;
      secondary: string;
      accent: string;
    };
  };
  pages: ChecklistPage[];
}

// Helper function to convert natural language prompt to structured checklist
async function convertPromptToChecklist(config: WebsiteConfig): Promise<Checklist> {
  // Parse the prompt to extract pages and components
  const prompt = config.prompt.toLowerCase();
  const pages: ChecklistPage[] = [];

  // Default home page
  const homeSections = [];

  // Detect common sections from the prompt
  if (prompt.includes('hero') || prompt.includes('landing') || prompt.includes('banner')) {
    homeSections.push({
      component: 'Hero',
      props: {
        title: 'Welcome',
        description: 'Your amazing website',
      },
    });
  }

  if (prompt.includes('feature') || prompt.includes('benefit')) {
    homeSections.push({
      component: 'Features',
      props: {
        items: [],
      },
    });
  }

  if (prompt.includes('testimonial') || prompt.includes('review')) {
    homeSections.push({
      component: 'Testimonials',
      props: {
        testimonials: [],
      },
    });
  }

  if (prompt.includes('contact') || prompt.includes('form')) {
    homeSections.push({
      component: 'ContactForm',
      props: {},
    });
  }

  if (prompt.includes('gallery') || prompt.includes('portfolio')) {
    homeSections.push({
      component: 'Gallery',
      props: {
        images: [],
      },
    });
  }

  if (prompt.includes('pricing') || prompt.includes('plan')) {
    homeSections.push({
      component: 'Pricing',
      props: {
        plans: [],
      },
    });
  }

  // If no sections detected, add default sections
  if (homeSections.length === 0) {
    homeSections.push(
      {
        component: 'Hero',
        props: {
          title: 'Welcome',
          description: 'Built with AI',
        },
      },
      {
        component: 'Features',
        props: {
          items: [],
        },
      },
      {
        component: 'ContactForm',
        props: {},
      }
    );
  }

  pages.push({
    name: 'Home',
    path: '/',
    sections: homeSections,
  });

  // Add additional pages from config
  for (const pageName of config.additionalPages) {
    if (pageName.trim()) {
      pages.push({
        name: pageName.trim(),
        path: `/${pageName.toLowerCase().replace(/\s+/g, '-')}`,
        sections: [
          {
            component: 'PageHeader',
            props: {
              title: pageName,
            },
          },
          {
            component: 'Content',
            props: {
              content: `${pageName} content goes here`,
            },
          },
        ],
      });
    }
  }

  // Detect specific page mentions
  if (prompt.includes('about')) {
    const aboutExists = pages.some((p) => p.name.toLowerCase() === 'about');
    if (!aboutExists) {
      pages.push({
        name: 'About',
        path: '/about',
        sections: [
          {
            component: 'PageHeader',
            props: {
              title: 'About Us',
            },
          },
          {
            component: 'Content',
            props: {},
          },
        ],
      });
    }
  }

  if (prompt.includes('services') || prompt.includes('what we do')) {
    const servicesExists = pages.some((p) => p.name.toLowerCase() === 'services');
    if (!servicesExists) {
      pages.push({
        name: 'Services',
        path: '/services',
        sections: [
          {
            component: 'PageHeader',
            props: {
              title: 'Our Services',
            },
          },
          {
            component: 'ServiceGrid',
            props: {},
          },
        ],
      });
    }
  }

  return {
    branding: {
      colors: {
        primary: config.primaryColor,
        secondary: config.secondaryColor,
        accent: config.accentColor,
      },
    },
    pages,
  };
}
