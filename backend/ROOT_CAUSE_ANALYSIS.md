# Root Cause Analysis Approach

## Philosophy

The AI Website Factory uses an **AI-driven root cause analysis** approach for error handling, rather than automatically applying known solutions from a database.

## Why Root Cause Analysis?

### Problems with Auto-Applying Known Solutions:
1. **Patches vs Fixes**: Previous solutions may have been quick patches that suppress symptoms rather than fixing underlying issues
2. **Context Differences**: What worked for one error might not be appropriate for a similar but different error
3. **Technical Debt**: Auto-applying patches accumulates technical debt over time
4. **Missed Learning**: The system doesn't learn to identify true root causes

### Benefits of AI-Driven Analysis:
1. **True Fixes**: AI analyzes the actual problem and proposes genuine solutions
2. **Context-Aware**: AI considers the specific codebase and error context
3. **Adaptable**: Known solutions are used as reference, not gospel
4. **Continuous Improvement**: Each fix is evaluated for root cause, improving over time

## How It Works

### 1. Error Detection
When an error occurs (build failure, test failure, etc.), the system captures the error log.

### 2. File Analysis
An AI agent analyzes the error log to identify which files are likely causing the **root problem**, not just where symptoms appear.

### 3. Knowledge Base Consultation
The system checks for:
- **Known solutions** for identical error signatures
- **Similar past incidents** that might provide context

**IMPORTANT**: These are provided to the AI as **suggestions and reference**, not automatically applied.

### 4. Root Cause Analysis
The Debugger AI performs deep analysis:
- Reads error messages carefully to understand the true issue
- Examines code flow to find where the problem originates
- Considers dependencies, types, and API usage
- Thinks systemically about design issues

The AI is explicitly instructed to differentiate between:
- ❌ **Patches**: Quick fixes that suppress symptoms
- ✅ **Root Causes**: Underlying issues that need fixing

### 5. Fix Generation
Based on root cause analysis, the AI:
- Proposes a fix targeting the **underlying issue**
- Ensures the fix prevents the entire class of errors
- Validates that known solutions truly address root causes

### 6. Learning
The root cause analysis and fix are saved to the knowledge base for future reference, including:
- The identified root cause
- The reasoning process
- The applied fix

## Examples

### Scenario 1: Import Error

**Error**: `Cannot find module 'react'`

**❌ Patch Approach**:
```javascript
// Just add a try-catch
try {
  import React from 'react';
} catch (e) {
  console.error('React not found');
}
```

**✅ Root Cause Approach**:
```bash
# Root cause: react is not installed
npm install react
# Fix the package.json to include react as a dependency
```

### Scenario 2: Type Error

**Error**: `Property 'name' does not exist on type 'User'`

**❌ Patch Approach**:
```typescript
// Just add type assertion
const userName = (user as any).name;
```

**✅ Root Cause Approach**:
```typescript
// Root cause: User interface is incomplete
interface User {
  id: string;
  name: string;  // Add missing property
  email: string;
}
```

### Scenario 3: Null Reference

**Error**: `Cannot read property 'id' of undefined`

**❌ Patch Approach**:
```javascript
// Just add null check everywhere
const id = user?.id || 'default';
```

**✅ Root Cause Approach**:
```javascript
// Root cause: User object not initialized properly
// Fix the data fetching logic to ensure user is loaded
async function loadUserData() {
  const user = await fetchUser();
  if (!user) {
    throw new Error('User data required');
  }
  return user;
}
```

## Configuration

The root cause analysis behavior is configured in `backend/app/api/endpoints/generate.py`:

### Key Parameters:
- `MAX_TRIALS_PER_COMPONENT = 3`: Number of attempts to fix component issues
- `MAX_TRIALS_FINAL = 5`: Number of attempts for final validation

### Debugger Prompt
The `DEBUGGER_PROMPT` includes explicit instructions for root cause analysis and warns against:
- Adding null checks without fixing data flow
- Wrapping code in try-catch without fixing the problem
- Using type assertions to bypass TypeScript
- Applying known solutions blindly

## Monitoring

Watch for these log messages to understand the process:

```
🤖 Delegating to AI Debugger for ROOT CAUSE analysis...
📚 Found a known solution. Providing to AI as REFERENCE (not auto-applying)...
📚 Found N similar past incidents. Providing as reference to AI...
🎯 ROOT CAUSE IDENTIFIED: [description]
🔧 Proposed fix: [fix description]
✅ ROOT CAUSE fix applied successfully.
```

## Benefits

1. **Higher Quality Fixes**: Solutions address underlying problems
2. **Reduced Technical Debt**: No accumulation of symptomatic patches
3. **Better Learning**: Knowledge base contains actual root causes
4. **Adaptability**: AI can adapt solutions to different contexts
5. **Transparency**: Root cause analysis is logged and saved

## Future Improvements

- **Root Cause Classification**: Categorize types of root causes for better learning
- **Fix Quality Metrics**: Track whether fixes truly prevent error recurrence
- **Pattern Recognition**: Identify common root cause patterns across projects
- **Preventive Analysis**: Use root cause knowledge to prevent errors during generation
