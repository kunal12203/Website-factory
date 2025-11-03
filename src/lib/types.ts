/**
 * Type definitions for the application
 */

// Website Configuration
export interface WebsiteConfig {
  prompt: string;
  primaryColor: string;
  secondaryColor: string;
  accentColor: string;
  additionalPages: string[];
}

// Generation Status
export type GenerationStage = 'idle' | 'planning' | 'building' | 'testing' | 'complete' | 'error';

export interface GenerationStatus {
  stage: GenerationStage;
  message: string;
  progress: number;
}

// Generation Result
export interface GenerationResult {
  status?: string;
  output_path?: string;
  outputPath?: string;
  site_path?: string;
  components_generated?: number;
  pages?: string[];
  total_pages?: number;
  tests_passed?: boolean | string;
  message?: string;
}

// API Error Response
export interface APIError {
  error?: string;
  message?: string;
  detail?: string;
}

// Checklist Types
export interface ChecklistSection {
  component: string;
  props: Record<string, unknown>;
}

export interface ChecklistPage {
  name: string;
  path: string;
  sections: ChecklistSection[];
}

export interface ChecklistBranding {
  colors: {
    primary: string;
    secondary: string;
    accent: string;
  };
}

export interface Checklist {
  branding: ChecklistBranding;
  pages: ChecklistPage[];
}

// API Request/Response Types
export interface GenerateWebsiteRequest {
  checklist: Checklist;
}

export type GenerateWebsiteResponse = GenerationResult;

// Validation Result
export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

// Component Props
export interface PromptInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  error?: string;
}

export interface ConfigPanelProps {
  config: WebsiteConfig;
  onChange: (config: WebsiteConfig) => void;
  disabled?: boolean;
  errors?: Partial<Record<keyof WebsiteConfig, string>>;
}

export interface ProgressTrackerProps {
  status: GenerationStatus;
}

export interface ResultDisplayProps {
  result: GenerationResult;
  onReset: () => void;
}
