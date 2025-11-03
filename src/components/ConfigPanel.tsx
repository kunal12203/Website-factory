'use client';

import { useState } from 'react';
import { WebsiteConfig } from './WebsiteBuilder';

interface ConfigPanelProps {
  config: WebsiteConfig;
  onChange: (config: WebsiteConfig) => void;
  disabled?: boolean;
}

export function ConfigPanel({ config, onChange, disabled }: ConfigPanelProps) {
  const [newPage, setNewPage] = useState('');

  const handleAddPage = () => {
    if (newPage.trim() && !config.additionalPages.includes(newPage.trim())) {
      onChange({
        ...config,
        additionalPages: [...config.additionalPages, newPage.trim()],
      });
      setNewPage('');
    }
  };

  const handleRemovePage = (index: number) => {
    onChange({
      ...config,
      additionalPages: config.additionalPages.filter((_, i) => i !== index),
    });
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-6 space-y-6">
      <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100">
        Customize Your Website
      </h3>

      {/* Color Scheme */}
      <div>
        <p className="text-sm font-medium text-slate-700 dark:text-slate-200 mb-3">
          🎨 Color Scheme
        </p>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-xs text-slate-600 dark:text-slate-400 mb-1">
              Primary
            </label>
            <div className="flex items-center gap-2">
              <input
                type="color"
                value={config.primaryColor}
                onChange={(e) =>
                  onChange({ ...config, primaryColor: e.target.value })
                }
                disabled={disabled}
                className="w-12 h-12 rounded-lg cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
              />
              <input
                type="text"
                value={config.primaryColor}
                onChange={(e) =>
                  onChange({ ...config, primaryColor: e.target.value })
                }
                disabled={disabled}
                className="flex-1 px-2 py-1 text-xs border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 disabled:opacity-50"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs text-slate-600 dark:text-slate-400 mb-1">
              Secondary
            </label>
            <div className="flex items-center gap-2">
              <input
                type="color"
                value={config.secondaryColor}
                onChange={(e) =>
                  onChange({ ...config, secondaryColor: e.target.value })
                }
                disabled={disabled}
                className="w-12 h-12 rounded-lg cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
              />
              <input
                type="text"
                value={config.secondaryColor}
                onChange={(e) =>
                  onChange({ ...config, secondaryColor: e.target.value })
                }
                disabled={disabled}
                className="flex-1 px-2 py-1 text-xs border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 disabled:opacity-50"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs text-slate-600 dark:text-slate-400 mb-1">
              Accent
            </label>
            <div className="flex items-center gap-2">
              <input
                type="color"
                value={config.accentColor}
                onChange={(e) =>
                  onChange({ ...config, accentColor: e.target.value })
                }
                disabled={disabled}
                className="w-12 h-12 rounded-lg cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
              />
              <input
                type="text"
                value={config.accentColor}
                onChange={(e) =>
                  onChange({ ...config, accentColor: e.target.value })
                }
                disabled={disabled}
                className="flex-1 px-2 py-1 text-xs border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 disabled:opacity-50"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Additional Pages */}
      <div>
        <p className="text-sm font-medium text-slate-700 dark:text-slate-200 mb-3">
          📄 Additional Pages
        </p>
        <div className="flex gap-2 mb-3">
          <input
            type="text"
            value={newPage}
            onChange={(e) => setNewPage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAddPage()}
            placeholder="E.g., Blog, Services, Team"
            disabled={disabled}
            className="flex-1 px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 disabled:opacity-50"
          />
          <button
            onClick={handleAddPage}
            disabled={disabled || !newPage.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Add
          </button>
        </div>
        {config.additionalPages.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {config.additionalPages.map((page, index) => (
              <div
                key={index}
                className="flex items-center gap-2 px-3 py-1 bg-slate-100 dark:bg-slate-700 rounded-full text-sm text-slate-700 dark:text-slate-300"
              >
                <span>{page}</span>
                <button
                  onClick={() => handleRemovePage(index)}
                  disabled={disabled}
                  className="text-slate-500 hover:text-red-600 disabled:opacity-50"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
          Home page is included by default. Add any other pages you need.
        </p>
      </div>

      {/* Quick Options */}
      <div>
        <p className="text-sm font-medium text-slate-700 dark:text-slate-200 mb-3">
          ⚡ Quick Add
        </p>
        <div className="flex flex-wrap gap-2">
          {['About', 'Services', 'Blog', 'Contact', 'Team', 'Portfolio'].map((page) => (
            <button
              key={page}
              onClick={() => {
                if (!config.additionalPages.includes(page)) {
                  onChange({
                    ...config,
                    additionalPages: [...config.additionalPages, page],
                  });
                }
              }}
              disabled={disabled || config.additionalPages.includes(page)}
              className="px-3 py-1 text-sm bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 rounded-lg transition-colors text-slate-700 dark:text-slate-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {page}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
