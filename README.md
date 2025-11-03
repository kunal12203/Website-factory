# AI Website Factory

An interactive AI-powered website builder that creates complete, production-ready websites from natural language descriptions.

## Features

- 🤖 **AI-Powered Generation**: Describe your website in plain English and watch it come to life
- 🎨 **Customizable Themes**: Choose your color scheme and branding
- 📄 **Multi-Page Support**: Automatically generate multiple pages with intelligent component selection
- 🧪 **Built-in Testing**: Components are tested automatically during generation
- ⚡ **Real-time Progress**: Watch your website being built step-by-step
- 🚀 **Production Ready**: Generated websites are optimized and ready to deploy

## Architecture

The system consists of two main parts:

### Frontend (Next.js 15 + React 19)
- Interactive prompt-based interface
- Real-time progress tracking
- Color scheme customization
- Page management

### Backend (FastAPI + Python)
- 8 specialized AI agents working together:
  1. **Project Manager**: Plans the website structure
  2. **UI Designer**: Designs component specifications
  3. **Copywriter**: Generates compelling content
  4. **Frontend Developer**: Generates React/TypeScript code
  5. **QA Tester**: Creates and runs tests
  6. **Debuggers**: Fix build and runtime errors
  7. **E2E Tester**: Validates user flows
  8. **Knowledge Base**: Learns from past generations

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- OpenAI API key or Anthropic API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd Website-factory
   ```

2. **Install frontend dependencies**
   ```bash
   npm install
   ```

3. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirement.txt
   ```

4. **Configure environment variables**

   For the frontend, create `.env.local`:
   ```bash
   cp .env.example .env.local
   ```

   For the backend, update `backend/.env`:
   ```bash
   AI_PROVIDER=openai  # or 'anthropic'
   OPENAI_API_KEY=your_api_key_here
   # or
   ANTHROPIC_API_KEY=your_api_key_here
   ```

### Running the Application

1. **Start the backend server**
   ```bash
   cd backend
   python main.py
   ```
   The backend will run on `http://localhost:8000`

2. **Start the frontend (in a new terminal)**
   ```bash
   npm run dev
   ```
   The frontend will run on `http://localhost:3000`

3. **Open your browser**
   Navigate to `http://localhost:3000` and start building!

## Usage

1. **Describe Your Website**
   Enter a natural language description of the website you want to create. For example:
   - "A modern portfolio website with a hero section, project gallery, and contact form"
   - "A SaaS landing page with features, pricing, testimonials, and a signup form"
   - "A restaurant website with menu, gallery, about us, and reservation system"

2. **Customize Colors**
   Choose your primary, secondary, and accent colors using the color pickers.

3. **Add Additional Pages**
   Specify any extra pages you need beyond the home page (e.g., About, Services, Blog).

4. **Generate**
   Click "Generate Website" and watch the AI build your site in real-time!

5. **Deploy**
   Once generated, follow the on-screen instructions to run your new website locally or deploy it to your favorite hosting platform.

## Example Prompts

- **Portfolio**: "A minimalist portfolio website showcasing my photography work with a grid gallery, about section, and contact form"
- **Business**: "A professional consulting firm website with services overview, team profiles, client testimonials, and a consultation booking form"
- **E-commerce**: "An online store for handmade jewelry with product listings, shopping cart, checkout, and customer reviews"
- **Blog**: "A tech blog with article listings, categories, search functionality, and author profiles"

## Project Structure

```
Website-factory/
├── src/
│   ├── app/                 # Next.js app router
│   │   ├── page.tsx        # Main page
│   │   ├── layout.tsx      # Root layout
│   │   └── globals.css     # Global styles
│   └── components/          # React components
│       ├── WebsiteBuilder.tsx    # Main builder component
│       ├── PromptInput.tsx       # Prompt input interface
│       ├── ConfigPanel.tsx       # Configuration panel
│       ├── ProgressTracker.tsx   # Progress visualization
│       └── ResultDisplay.tsx     # Results and next steps
├── backend/
│   ├── app/
│   │   ├── api/endpoints/   # API routes
│   │   ├── agents/          # AI agents
│   │   ├── services/        # Business logic
│   │   ├── core/            # Configuration
│   │   └── models.py        # Data models
│   └── main.py              # FastAPI app
├── public/                  # Static assets
└── package.json
```

## Technologies Used

### Frontend
- Next.js 15.5.0
- React 19.1.0
- TypeScript
- Tailwind CSS 4

### Backend
- FastAPI
- OpenAI / Anthropic Claude
- Playwright (E2E testing)
- Jest (Component testing)
- MySQL (Knowledge base)

## API Endpoints

### `POST /api/generate`

Generates a complete website from a structured checklist.

**Request Body:**
```json
{
  "checklist": {
    "branding": {
      "colors": {
        "primary": "#3b82f6",
        "secondary": "#8b5cf6",
        "accent": "#10b981"
      }
    },
    "pages": [
      {
        "name": "Home",
        "path": "/",
        "sections": [
          {
            "component": "Hero",
            "props": {
              "title": "Welcome",
              "description": "Your amazing website"
            }
          }
        ]
      }
    ]
  }
}
```

**Response:**
```json
{
  "output_path": "output/site-20250101-120000/",
  "pages": ["Home", "About"],
  "components_generated": 15,
  "tests_passed": true,
  "message": "Website generated successfully"
}
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Troubleshooting

### Backend won't start
- Make sure you have set your API key in `backend/.env`
- Check that all Python dependencies are installed: `pip install -r backend/requirement.txt`

### Frontend build errors
- Try deleting `node_modules` and reinstalling: `rm -rf node_modules && npm install`
- Clear Next.js cache: `rm -rf .next`

### Generation fails
- Check that the backend is running on port 8000
- Verify your AI provider API key is valid
- Check the backend logs for detailed error messages

## Support

For issues and questions, please open an issue on GitHub.
