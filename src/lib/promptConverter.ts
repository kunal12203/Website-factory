/**
 * Convert natural language prompt to structured checklist
 */

import { WebsiteConfig, Checklist, ChecklistPage, ChecklistSection } from './types';
import { COMPONENT_TYPES } from './constants';

/**
 * Detect sections from prompt keywords
 */
function detectSections(prompt: string): ChecklistSection[] {
  const lowerPrompt = prompt.toLowerCase();
  const sections: ChecklistSection[] = [];

  // Hero section detection
  if (
    lowerPrompt.includes('hero') ||
    lowerPrompt.includes('landing') ||
    lowerPrompt.includes('banner') ||
    lowerPrompt.includes('header section')
  ) {
    sections.push({
      component: COMPONENT_TYPES.HERO,
      props: {
        title: 'Welcome to Our Website',
        description: 'Discover amazing experiences',
        showCTA: true,
      },
    });
  }

  // Features section detection
  if (
    lowerPrompt.includes('feature') ||
    lowerPrompt.includes('benefit') ||
    lowerPrompt.includes('services') ||
    lowerPrompt.includes('what we do')
  ) {
    sections.push({
      component: COMPONENT_TYPES.FEATURES,
      props: {
        title: 'Our Features',
        items: [],
      },
    });
  }

  // Testimonials section detection
  if (
    lowerPrompt.includes('testimonial') ||
    lowerPrompt.includes('review') ||
    lowerPrompt.includes('customer feedback')
  ) {
    sections.push({
      component: COMPONENT_TYPES.TESTIMONIALS,
      props: {
        title: 'What Our Customers Say',
        testimonials: [],
      },
    });
  }

  // Gallery section detection
  if (
    lowerPrompt.includes('gallery') ||
    lowerPrompt.includes('portfolio') ||
    lowerPrompt.includes('showcase') ||
    lowerPrompt.includes('images')
  ) {
    sections.push({
      component: COMPONENT_TYPES.GALLERY,
      props: {
        title: 'Gallery',
        images: [],
      },
    });
  }

  // Pricing section detection
  if (
    lowerPrompt.includes('pricing') ||
    lowerPrompt.includes('plans') ||
    lowerPrompt.includes('packages')
  ) {
    sections.push({
      component: COMPONENT_TYPES.PRICING,
      props: {
        title: 'Pricing Plans',
        plans: [],
      },
    });
  }

  // Contact form detection
  if (
    lowerPrompt.includes('contact') ||
    lowerPrompt.includes('form') ||
    lowerPrompt.includes('get in touch') ||
    lowerPrompt.includes('reach out')
  ) {
    sections.push({
      component: COMPONENT_TYPES.CONTACT_FORM,
      props: {
        title: 'Contact Us',
      },
    });
  }

  // If no sections detected, add default sections
  if (sections.length === 0) {
    sections.push(
      {
        component: COMPONENT_TYPES.HERO,
        props: {
          title: 'Welcome',
          description: 'Built with AI',
        },
      },
      {
        component: COMPONENT_TYPES.FEATURES,
        props: {
          title: 'Features',
          items: [],
        },
      },
      {
        component: COMPONENT_TYPES.CONTACT_FORM,
        props: {
          title: 'Get in Touch',
        },
      }
    );
  }

  return sections;
}

/**
 * Detect additional pages from prompt
 */
function detectPages(prompt: string): string[] {
  const lowerPrompt = prompt.toLowerCase();
  const detectedPages: string[] = [];

  const pageKeywords: Record<string, string[]> = {
    About: ['about', 'who we are', 'our story', 'team'],
    Services: ['services', 'what we offer', 'solutions'],
    Blog: ['blog', 'articles', 'news', 'posts'],
    Contact: ['contact', 'reach us'],
    Portfolio: ['portfolio', 'work', 'projects'],
    Pricing: ['pricing', 'plans', 'packages'],
  };

  for (const [pageName, keywords] of Object.entries(pageKeywords)) {
    if (keywords.some((keyword) => lowerPrompt.includes(keyword))) {
      if (!detectedPages.includes(pageName)) {
        detectedPages.push(pageName);
      }
    }
  }

  return detectedPages;
}

/**
 * Create page object
 */
function createPage(name: string, isHome: boolean = false): ChecklistPage {
  const path = isHome ? '/' : `/${name.toLowerCase().replace(/\s+/g, '-')}`;

  if (isHome) {
    return {
      name: 'Home',
      path,
      sections: [],
    };
  }

  // Create sections based on page type
  const sections: ChecklistSection[] = [
    {
      component: COMPONENT_TYPES.PAGE_HEADER,
      props: {
        title: name,
        description: `Learn more about our ${name.toLowerCase()}`,
      },
    },
    {
      component: COMPONENT_TYPES.CONTENT,
      props: {
        content: `${name} content goes here`,
      },
    },
  ];

  return {
    name,
    path,
    sections,
  };
}

/**
 * Main conversion function
 */
export async function convertPromptToChecklist(
  config: WebsiteConfig
): Promise<Checklist> {
  const prompt = config.prompt.toLowerCase();
  const pages: ChecklistPage[] = [];

  // Create home page
  const homeSections = detectSections(config.prompt);
  const homePage = createPage('Home', true);
  homePage.sections = homeSections;
  pages.push(homePage);

  // Add pages from explicit configuration
  const allPageNames = new Set<string>(config.additionalPages);

  // Add pages detected from prompt
  const detectedPages = detectPages(prompt);
  detectedPages.forEach((page) => allPageNames.add(page));

  // Create page objects
  for (const pageName of Array.from(allPageNames)) {
    if (pageName.trim() && pageName.toLowerCase() !== 'home') {
      pages.push(createPage(pageName.trim()));
    }
  }

  // Special handling for specific page types
  for (const page of pages) {
    if (page.name.toLowerCase() === 'services' && page.sections.length <= 2) {
      page.sections.push({
        component: COMPONENT_TYPES.SERVICE_GRID,
        props: {
          services: [],
        },
      });
    }

    if (page.name.toLowerCase() === 'portfolio' && page.sections.length <= 2) {
      page.sections.push({
        component: COMPONENT_TYPES.GALLERY,
        props: {
          title: 'Our Work',
          images: [],
        },
      });
    }

    if (page.name.toLowerCase() === 'contact' && page.sections.length <= 2) {
      page.sections.push({
        component: COMPONENT_TYPES.CONTACT_FORM,
        props: {
          title: 'Get in Touch',
        },
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
