'use client';

import { GenerationStatus } from './WebsiteBuilder';

interface ProgressTrackerProps {
  status: GenerationStatus;
}

export function ProgressTracker({ status }: ProgressTrackerProps) {
  const stages = [
    { key: 'planning', label: 'Planning', icon: '🧠' },
    { key: 'building', label: 'Building', icon: '🔨' },
    { key: 'testing', label: 'Testing', icon: '🧪' },
    { key: 'complete', label: 'Complete', icon: '✅' },
  ];

  const getCurrentStageIndex = () => {
    const index = stages.findIndex((s) => s.key === status.stage);
    return index >= 0 ? index : 0;
  };

  const currentIndex = getCurrentStageIndex();

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-8">
        <div className="text-center mb-8">
          <div className="text-6xl mb-4 animate-bounce">
            {stages[currentIndex]?.icon || '⚙️'}
          </div>
          <h2 className="text-3xl font-bold text-slate-800 dark:text-slate-100 mb-2">
            {status.message}
          </h2>
          <p className="text-slate-600 dark:text-slate-400">
            This may take a few minutes...
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-4 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-600 to-purple-600 transition-all duration-500 ease-out"
              style={{ width: `${status.progress}%` }}
            />
          </div>
          <p className="text-center mt-2 text-sm text-slate-600 dark:text-slate-400">
            {status.progress}% Complete
          </p>
        </div>

        {/* Stage Indicators */}
        <div className="grid grid-cols-4 gap-4">
          {stages.map((stage, index) => {
            const isActive = index === currentIndex;
            const isComplete = index < currentIndex;

            return (
              <div
                key={stage.key}
                className={`text-center p-4 rounded-xl transition-all ${
                  isActive
                    ? 'bg-blue-100 dark:bg-blue-900/30 border-2 border-blue-500'
                    : isComplete
                    ? 'bg-green-100 dark:bg-green-900/30 border-2 border-green-500'
                    : 'bg-slate-100 dark:bg-slate-700 border-2 border-slate-300 dark:border-slate-600 opacity-50'
                }`}
              >
                <div className="text-3xl mb-2">{stage.icon}</div>
                <p
                  className={`text-sm font-medium ${
                    isActive
                      ? 'text-blue-700 dark:text-blue-300'
                      : isComplete
                      ? 'text-green-700 dark:text-green-300'
                      : 'text-slate-600 dark:text-slate-400'
                  }`}
                >
                  {stage.label}
                </p>
                {isActive && (
                  <div className="mt-2 flex justify-center gap-1">
                    <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
                    <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse delay-100" />
                    <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse delay-200" />
                  </div>
                )}
                {isComplete && (
                  <div className="mt-2 text-green-600 dark:text-green-400">✓</div>
                )}
              </div>
            );
          })}
        </div>

        {/* Fun Facts */}
        <div className="mt-8 p-4 bg-slate-50 dark:bg-slate-700/50 rounded-xl">
          <p className="text-sm text-slate-600 dark:text-slate-400 text-center">
            <span className="font-semibold">💡 Did you know?</span> Our AI agents are
            working together to design, code, test, and deploy your website automatically.
          </p>
        </div>
      </div>
    </div>
  );
}
