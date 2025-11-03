'use client';

import { PromptInputProps } from '@/lib/types';
import { EXAMPLE_PROMPTS } from '@/lib/constants';

export function PromptInput({ value, onChange, disabled }: PromptInputProps) {
  const examples = EXAMPLE_PROMPTS;

  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-6 space-y-4">
      <div>
        <label className="block text-sm font-semibold text-slate-700 dark:text-slate-200 mb-2">
          Describe Your Website
        </label>
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          placeholder="E.g., A professional portfolio website with a hero section, about me page, project gallery, and contact form. Include testimonials and a modern design."
          className="w-full h-40 px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 disabled:opacity-50 disabled:cursor-not-allowed"
        />
        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
          Be as specific as possible. Mention sections, features, and the style you want.
        </p>
      </div>

      <div>
        <p className="text-sm font-medium text-slate-700 dark:text-slate-200 mb-2">
          💡 Example Prompts:
        </p>
        <div className="space-y-2">
          {examples.map((example, index) => (
            <button
              key={index}
              onClick={() => onChange(example)}
              disabled={disabled}
              className="w-full text-left px-4 py-2 text-sm bg-slate-50 dark:bg-slate-700 hover:bg-slate-100 dark:hover:bg-slate-600 rounded-lg transition-colors text-slate-700 dark:text-slate-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
