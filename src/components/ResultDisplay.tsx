'use client';

interface GenerationResult {
  output_path?: string;
  site_path?: string;
  components_generated?: number;
  pages?: string[];
  total_pages?: number;
  tests_passed?: boolean | string;
  message?: string;
}

interface ResultDisplayProps {
  result: GenerationResult;
  onReset: () => void;
}

export function ResultDisplay({ result, onReset }: ResultDisplayProps) {
  const hasOutput = result?.output_path || result?.site_path;
  const outputPath = result?.output_path || result?.site_path || 'output/';

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-8">
        {/* Success Header */}
        <div className="text-center mb-8">
          <div className="text-7xl mb-4">🎉</div>
          <h2 className="text-4xl font-bold text-slate-800 dark:text-slate-100 mb-2">
            Your Website is Ready!
          </h2>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            Your website has been successfully generated and is ready to deploy.
          </p>
        </div>

        {/* Result Details */}
        <div className="space-y-6">
          {/* Output Path */}
          {hasOutput && (
            <div className="p-4 bg-slate-50 dark:bg-slate-700/50 rounded-xl">
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                📁 Output Location
              </p>
              <code className="block p-3 bg-slate-900 dark:bg-slate-950 text-green-400 rounded-lg text-sm font-mono">
                {outputPath}
              </code>
            </div>
          )}

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl text-center">
              <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-1">
                {result?.components_generated || result?.pages?.length || 0}
              </div>
              <div className="text-sm text-slate-600 dark:text-slate-400">
                Components
              </div>
            </div>
            <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-xl text-center">
              <div className="text-3xl font-bold text-purple-600 dark:text-purple-400 mb-1">
                {result?.pages?.length || result?.total_pages || 0}
              </div>
              <div className="text-sm text-slate-600 dark:text-slate-400">Pages</div>
            </div>
            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-xl text-center">
              <div className="text-3xl font-bold text-green-600 dark:text-green-400 mb-1">
                {result?.tests_passed || '✓'}
              </div>
              <div className="text-sm text-slate-600 dark:text-slate-400">
                Tests Passed
              </div>
            </div>
          </div>

          {/* Next Steps */}
          <div className="p-6 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-xl">
            <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-4">
              🚀 Next Steps
            </h3>
            <ol className="space-y-3 text-sm text-slate-700 dark:text-slate-300">
              <li className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">
                  1
                </span>
                <span>
                  Navigate to the output directory:{' '}
                  <code className="px-2 py-1 bg-slate-900 dark:bg-slate-950 text-green-400 rounded text-xs font-mono">
                    cd {outputPath}
                  </code>
                </span>
              </li>
              <li className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">
                  2
                </span>
                <span>
                  Install dependencies:{' '}
                  <code className="px-2 py-1 bg-slate-900 dark:bg-slate-950 text-green-400 rounded text-xs font-mono">
                    npm install
                  </code>
                </span>
              </li>
              <li className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">
                  3
                </span>
                <span>
                  Start development server:{' '}
                  <code className="px-2 py-1 bg-slate-900 dark:bg-slate-950 text-green-400 rounded text-xs font-mono">
                    npm run dev
                  </code>
                </span>
              </li>
              <li className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">
                  4
                </span>
                <span>
                  Open your browser to:{' '}
                  <code className="px-2 py-1 bg-slate-900 dark:bg-slate-950 text-blue-400 rounded text-xs font-mono">
                    http://localhost:3000
                  </code>
                </span>
              </li>
            </ol>
          </div>

          {/* Additional Info */}
          {result?.message && (
            <div className="p-4 bg-slate-50 dark:bg-slate-700/50 rounded-xl">
              <p className="text-sm text-slate-600 dark:text-slate-400">
                {result.message}
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-4 justify-center pt-4">
            <button
              onClick={onReset}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-full font-semibold hover:shadow-lg transform hover:scale-105 transition-all"
            >
              Create Another Website
            </button>
            <a
              href={`file://${outputPath}`}
              target="_blank"
              rel="noopener noreferrer"
              className="px-6 py-3 bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-200 rounded-full font-semibold hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors"
            >
              Open Folder
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
