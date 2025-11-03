/**
 * Application Constants
 */

// API Configuration
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const API_TIMEOUT = 600000; // 10 minutes for website generation
export const API_RETRY_ATTEMPTS = 3;
export const API_RETRY_DELAY = 2000; // 2 seconds

// Component Types
export const COMPONENT_TYPES = {
  HERO: 'Hero',
  FEATURES: 'Features',
  TESTIMONIALS: 'Testimonials',
  CONTACT_FORM: 'ContactForm',
  GALLERY: 'Gallery',
  PRICING: 'Pricing',
  PAGE_HEADER: 'PageHeader',
  CONTENT: 'Content',
  SERVICE_GRID: 'ServiceGrid',
} as const;

// Default Colors
export const DEFAULT_COLORS = {
  primary: '#3b82f6',
  secondary: '#8b5cf6',
  accent: '#10b981',
} as const;

// Generation Stages
export const GENERATION_STAGES = {
  IDLE: 'idle',
  PLANNING: 'planning',
  BUILDING: 'building',
  TESTING: 'testing',
  COMPLETE: 'complete',
  ERROR: 'error',
} as const;

// Progress Percentages
export const PROGRESS_PERCENTAGES = {
  [GENERATION_STAGES.IDLE]: 0,
  [GENERATION_STAGES.PLANNING]: 10,
  [GENERATION_STAGES.BUILDING]: 30,
  [GENERATION_STAGES.TESTING]: 80,
  [GENERATION_STAGES.COMPLETE]: 100,
  [GENERATION_STAGES.ERROR]: 0,
} as const;

// Common Pages
export const COMMON_PAGES = [
  'About',
  'Services',
  'Blog',
  'Contact',
  'Team',
  'Portfolio',
] as const;

// Example Prompts
export const EXAMPLE_PROMPTS = [
  'A modern portfolio website with a hero section, project gallery, and contact form',
  'A SaaS landing page with features, pricing, testimonials, and a signup form',
  'A restaurant website with menu, gallery, about us, and reservation system',
  'An e-commerce store with product listings, shopping cart, and checkout',
  'A blog with article listings, categories, and author profiles',
] as const;

// Validation Rules
export const VALIDATION_RULES = {
  MIN_PROMPT_LENGTH: 10,
  MAX_PROMPT_LENGTH: 1000,
  MIN_PAGE_NAME_LENGTH: 1,
  MAX_PAGE_NAME_LENGTH: 50,
  MAX_ADDITIONAL_PAGES: 10,
  COLOR_REGEX: /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/,
} as const;

// Error Messages
export const ERROR_MESSAGES = {
  PROMPT_TOO_SHORT: `Prompt must be at least ${VALIDATION_RULES.MIN_PROMPT_LENGTH} characters`,
  PROMPT_TOO_LONG: `Prompt must be less than ${VALIDATION_RULES.MAX_PROMPT_LENGTH} characters`,
  PAGE_NAME_REQUIRED: 'Page name is required',
  PAGE_NAME_TOO_LONG: `Page name must be less than ${VALIDATION_RULES.MAX_PAGE_NAME_LENGTH} characters`,
  INVALID_COLOR: 'Invalid color format. Use hex colors like #FF0000',
  TOO_MANY_PAGES: `Maximum ${VALIDATION_RULES.MAX_ADDITIONAL_PAGES} additional pages allowed`,
  API_CONNECTION_ERROR: 'Could not connect to the API. Make sure the backend is running.',
  API_TIMEOUT: 'Request timed out. The generation is taking longer than expected.',
  GENERATION_FAILED: 'Website generation failed. Please try again.',
  UNKNOWN_ERROR: 'An unknown error occurred. Please try again.',
} as const;

// Success Messages
export const SUCCESS_MESSAGES = {
  GENERATION_COMPLETE: 'Your website has been generated successfully!',
  READY_TO_DEPLOY: 'Your website is ready to deploy!',
} as const;
