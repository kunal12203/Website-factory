# AI Website Factory - Architecture Overview

## System Overview

The AI Website Factory is a sophisticated system that uses multiple specialized AI agents to generate complete, tested websites from natural language descriptions. The system emphasizes **root cause analysis** over quick fixes.

## Architecture Layers

### 1. Frontend Layer (Next.js + React)
**Location**: `/src`

**Components**:
- **WebsiteBuilder**: Main orchestrator component
- **PromptInput**: Natural language input interface
- **ConfigPanel**: Color and page customization
- **ProgressTracker**: Real-time generation visualization
- **ResultDisplay**: Success screen with deployment instructions
- **ErrorBoundary**: Graceful error handling

**Libraries** (`/src/lib`):
- `api.ts`: Robust API client with retry logic
- `constants.ts`: Centralized configuration
- `types.ts`: TypeScript type definitions
- `validation.ts`: Input validation and sanitization
- `promptConverter.ts`: Natural language to checklist conversion

### 2. Backend Layer (FastAPI + Python)
**Location**: `/backend`

**Main Components**:
- `main.py`: FastAPI application with health checks and validation
- `app/api/endpoints/generate.py`: Website generation orchestration
- `app/agents/`: AI agent implementations
- `app/services/`: Business logic and utilities
- `app/core/`: Configuration management

### 3. AI Agent Layer

**8 Specialized AI Agents**:

1. **Project Manager Agent**
   - Parses user requirements
   - Creates structured project plan
   - Organizes components and pages

2. **UI Designer Agent**
   - Designs component specifications
   - Defines props and structure
   - Creates design placeholders

3. **Copywriter Agent**
   - Generates compelling copy
   - Replaces placeholders with content
   - Ensures consistent tone

4. **Frontend Developer Agent**
   - Writes React/TypeScript code
   - Follows Next.js conventions
   - Implements components and pages

5. **QA Tester Agent**
   - Writes Jest tests
   - Includes accessibility checks
   - Validates functionality

6. **File Analyzer Agent**
   - Identifies files causing errors
   - Finds root sources, not symptoms
   - Targets debugging efforts

7. **Debugger Agent** ⭐ **ROOT CAUSE SPECIALIST**
   - Performs deep root cause analysis
   - Distinguishes patches from real fixes
   - Uses known solutions as reference only
   - Proposes fixes for underlying issues

8. **E2E Tester Agent**
   - Creates Playwright tests
   - Validates user flows
   - Tests complete scenarios

## Data Flow

### Generation Pipeline

```
1. USER INPUT
   ↓
   User provides: prompt, colors, pages
   ↓
2. FRONTEND VALIDATION
   ↓
   Validates input, checks backend health
   ↓
3. PROMPT CONVERSION
   ↓
   Converts natural language to structured checklist
   ↓
4. PROJECT PLANNING (PM Agent)
   ↓
   Creates task list: components first, then pages
   ↓
5. COMPONENT GENERATION (per component)
   ├─ UI Designer → Design spec
   ├─ Copywriter → Content generation
   ├─ Frontend Dev → Code implementation
   ├─ QA Tester → Test creation
   └─ Jest Runner → Validation

   ↓ (if tests fail)

   ROOT CAUSE ANALYSIS CYCLE:
   ├─ File Analyzer → Identify problem files
   ├─ Knowledge Base → Fetch similar incidents (as reference)
   ├─ Debugger Agent → ROOT CAUSE analysis
   ├─ Frontend Dev → Generate fix for root cause
   └─ Verification → Run tests again

   ↓
6. PAGE ASSEMBLY
   ↓
   Frontend Dev composes pages from components
   ↓
7. FINAL VALIDATION (up to 5 attempts)
   ├─ npm run build → Compile check
   ├─ Playwright → E2E tests
   └─ Lighthouse → Performance/Accessibility

   ↓ (if fails)

   ROOT CAUSE ANALYSIS CYCLE

   ↓
8. KNOWLEDGE BASE LEARNING
   ↓
   Save root cause analysis and fixes
   ↓
9. RESULT DELIVERY
   ↓
   Return output path and metadata
```

## Root Cause Analysis System

### Problem: Quick Fixes vs Real Solutions

Traditional systems often apply patches:
- Add null checks everywhere
- Wrap code in try-catch
- Use type assertions
- Copy-paste previous solutions

### Solution: AI-Driven Root Cause Analysis

Our system:
1. **Never auto-applies** known solutions
2. **Always uses AI** to analyze errors
3. **Provides context** from knowledge base as suggestions
4. **Focuses on** underlying causes, not symptoms
5. **Saves analysis** for continuous learning

### Error Handling Flow

```
ERROR OCCURS
   ↓
   Create error signature
   ↓
   Fetch known solutions (if any)
   ↓
┌──────────────────────────────┐
│  AI ROOT CAUSE ANALYSIS      │
│                              │
│  Inputs:                     │
│  • Error log                 │
│  • Relevant code files       │
│  • Known solutions (ref)     │
│  • Similar past incidents    │
│                              │
│  Analysis:                   │
│  • What's the real problem?  │
│  • Where does it originate?  │
│  • What's the proper fix?    │
│                              │
│  Output:                     │
│  • Root cause explanation    │
│  • Fix suggestion            │
│  • File to modify            │
└──────────────────────────────┘
   ↓
   AI generates code fix
   ↓
   Apply fix and verify
   ↓
   Save to knowledge base with root cause
```

## Knowledge Base

### Purpose
- Store error patterns and solutions
- Provide historical context to AI
- Track fix effectiveness
- Enable continuous improvement

### Storage
- **Error Signature**: Hash of error message
- **Error Log**: Full error details
- **Root Cause**: AI's analysis
- **Fix Prompt**: Instructions given to AI
- **Fix Code**: Generated solution
- **Agent**: Which agent fixed it
- **Attempt**: How many tries it took

### Usage
Known solutions are **suggestions**, not auto-applied:
```python
# ❌ OLD WAY: Auto-apply
if known_solution:
    apply_solution(known_solution)

# ✅ NEW WAY: Suggest to AI
ai_context = {
    "error": error_log,
    "known_solution_suggestion": {
        "note": "Use as reference only",
        "solution": known_solution
    }
}
ai_analysis = debugger_agent.analyze(ai_context)
```

## Configuration

### Backend Configuration (`backend/.env`)
```bash
# AI Provider
AI_PROVIDER=openai  # or anthropic

# API Keys
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key

# Models
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_MODEL=claude-3-haiku-20240307

# Database
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=website_factory_kb
```

### Frontend Configuration (`/.env.local`)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Error Recovery

### Retry Strategy
- **Component Tests**: 3 attempts with root cause analysis
- **Final Build**: 5 attempts with root cause analysis
- **API Calls**: 3 attempts with exponential backoff

### Self-Healing
Each failure triggers:
1. Root cause identification
2. AI-generated fix
3. Verification
4. Knowledge base update

## Security

### Input Validation
- Prompt length limits (10-1000 chars)
- Color format validation (hex only)
- Page name sanitization
- XSS prevention

### API Security
- CORS configuration
- API key validation
- Request timeout limits
- Error message sanitization

## Performance

### Optimization Strategies
- Parallel AI agent calls when possible
- Targeted file analysis (not full codebase)
- Incremental component testing
- Smart retry with backoff

### Caching
- Knowledge base for known patterns
- Similar incident lookup
- File reading optimization

## Monitoring

### Logging
- Structured logging with timestamps
- Error tracking with context
- Root cause documentation
- Fix effectiveness tracking

### Metrics
- Generation success rate
- Average attempts per component
- Root cause identification rate
- Fix application success

## Future Enhancements

1. **Root Cause Classification**
   - Categorize types of root causes
   - Predict likely root causes
   - Preventive analysis

2. **Multi-Model Support**
   - Use different models for different agents
   - Ensemble approaches for critical decisions
   - Model performance tracking

3. **Advanced Learning**
   - Pattern recognition across projects
   - Predictive error prevention
   - Automated refactoring suggestions

4. **Enhanced Testing**
   - Visual regression testing
   - Performance monitoring
   - Security vulnerability scanning

## Development Workflow

### Adding New Features
1. Update agent prompts if needed
2. Modify generation pipeline
3. Update knowledge base schema
4. Test with various inputs
5. Monitor root cause effectiveness

### Debugging
1. Check backend logs for root cause analysis
2. Review knowledge base entries
3. Verify AI agent responses
4. Test error handling paths
5. Validate fix quality

## See Also
- [ROOT_CAUSE_ANALYSIS.md](./ROOT_CAUSE_ANALYSIS.md) - Detailed explanation of root cause approach
- [README.md](../README.md) - User-facing documentation
- [backend/.env.example](./backend/.env.example) - Configuration template
