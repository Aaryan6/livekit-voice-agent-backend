# Frontend Changes Required for Enhanced Interview Agent

## Overview

The interview agent has been significantly enhanced with structured interview flow, timing tracking, grammar assessment, and comprehensive reporting. The frontend needs to be updated to support these new features.

## Backend Changes Summary

### 1. **Structured Interview Flow**

- Maximum 5 questions per interview
- Structured stages: Welcome → Introduction → 5 Questions → Wrap-up
- Automatic progression through stages
- Predefined questions based on role and skill level

### 2. **Enhanced Timing & Analytics**

- Total interview duration tracking
- Candidate speaking time vs. interviewer time
- Stage-wise timing breakdown
- Real-time progress tracking

### 3. **Grammar Assessment**

- Real-time grammar analysis of candidate responses
- Overall grammar accuracy scoring (70% threshold)
- Question-specific grammar tracking
- Detailed grammar feedback

### 4. **Comprehensive Reporting**

- Mandatory questions coverage tracking
- Detailed interview summary with all metrics
- Grammar assessment reports
- Stage timing analysis

---

## Required Frontend Changes

### 1. **User Information Collection** (Priority: HIGH)

#### Current State

The agent currently fetches user info from:

- Room name parsing
- Participant metadata
- Next.js API endpoint
- Environment variables

#### Action Required

**Update the connection page/form to collect:**

```javascript
// Required fields for interview setup
const interviewForm = {
  candidateName: string, // Candidate's full name
  role: string, // Job role (e.g., "Software Engineer")
  skillLevel: string, // "junior", "mid", "senior", "staff"
  // Optional fields
  email: string,
  phoneNumber: string,
};
```

**API Endpoint Updates:**

```typescript
// Update /api/connection-details/route.ts
// Add interview info endpoint
// POST /api/interview-setup
{
  candidateName: string,
  role: string,
  skillLevel: string,
  roomName: string,
  participantId: string
}
```

### 2. **Real-time Interview Progress Display** (Priority: HIGH)

#### Components to Add/Update

**Interview Progress Component:**

```typescript
interface InterviewProgress {
  currentStage:
    | "welcome"
    | "introduction"
    | "questions"
    | "wrap_up"
    | "completed";
  questionsAsked: number;
  totalQuestions: number; // Always 5
  currentQuestionIndex: number;
  elapsedTime: number; // in seconds
  candidateSpeakingTime: number;
}
```

**Implementation in `components/TranscriptionView.tsx`:**

```tsx
// Add progress indicator
<div className="interview-progress">
  <div className="stage-indicator">Current Stage: {progress.currentStage}</div>
  <div className="question-counter">
    Question {progress.currentQuestionIndex + 1} of {progress.totalQuestions}
  </div>
  <div className="timer">Elapsed: {formatTime(progress.elapsedTime)}</div>
</div>
```

### 3. **Live Grammar Feedback Display** (Priority: MEDIUM)

#### New Component: `GrammarFeedback.tsx`

```tsx
interface GrammarAssessment {
  accuracy_percentage: number;
  meets_threshold: boolean;
  issues: string[];
  word_count: number;
}

export function GrammarFeedback({
  assessment,
}: {
  assessment: GrammarAssessment;
}) {
  return (
    <div className="grammar-feedback">
      <div className="accuracy-score">
        Grammar Accuracy: {assessment.accuracy_percentage}%
      </div>
      {assessment.issues.length > 0 && (
        <div className="grammar-issues">
          <h4>Suggestions:</h4>
          <ul>
            {assessment.issues.map((issue, index) => (
              <li key={index}>{issue}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

### 4. **Interview Summary Page** (Priority: HIGH)

#### New Component: `InterviewSummary.tsx`

```tsx
interface InterviewSummary {
  interview_metadata: {
    candidate_name: string;
    role: string;
    skill_level: string;
    interview_date: string;
    total_duration_minutes: number;
    candidate_speaking_time_minutes: number;
    interviewer_time_percentage: number;
  };
  questions_coverage: {
    total_predefined_questions: number;
    questions_asked_count: number;
    questions_missed_count: number;
    all_mandatory_questions_asked: boolean;
    questions_asked: string[];
    questions_missed: string[];
  };
  grammar_assessment: {
    overall_feedback: {
      average_accuracy_percentage: number;
      meets_70_percent_threshold: boolean;
      assessment: "Yes" | "No";
    };
    qa_section_feedback: {
      total_answers_assessed: number;
      answers_below_70_percent: number;
      answers_with_poor_grammar_count: number;
    };
  };
}

export function InterviewSummary({ summary }: { summary: InterviewSummary }) {
  // Render comprehensive summary with charts and metrics
}
```

### 5. **API Endpoints for Data Access** (Priority: HIGH)

#### Required API Routes

**1. Interview Data Endpoint**

```typescript
// /api/interview-data/[roomName]/route.ts
// GET: Fetch interview data and summary
export async function GET(
  request: Request,
  { params }: { params: { roomName: string } }
) {
  // Return interview data from agent logs
}
```

**2. Live Updates Endpoint (WebSocket or Server-Sent Events)**

```typescript
// /api/interview-live/[roomName]/route.ts
// For real-time updates during interview
export async function GET(
  request: Request,
  { params }: { params: { roomName: string } }
) {
  // Stream live interview updates
}
```

### 6. **Enhanced Transcription View** (Priority: MEDIUM)

#### Updates to `TranscriptionView.tsx`

```tsx
// Add stage-aware transcription display
interface TranscriptionSegment {
  speaker: "interviewer" | "candidate";
  text: string;
  timestamp: string;
  stage: string;
  questionIndex?: number;
  grammarAssessment?: GrammarAssessment;
}

// Enhanced display with stage indicators and grammar feedback
```

### 7. **Post-Interview Report Generation** (Priority: HIGH)

#### New Page: `/interview-report/[roomName]`

```tsx
// Complete interview report with:
// - Interview metadata
// - Questions coverage analysis
// - Grammar assessment report
// - Timing breakdown
// - Exportable summary (PDF/CSV)
```

---

## Implementation Priority

### Phase 1 (Critical - Week 1)

1. **User information collection form**
2. **Interview progress tracking**
3. **Basic summary display**
4. **API endpoints for data access**

### Phase 2 (Important - Week 2)

1. **Real-time grammar feedback**
2. **Enhanced transcription view**
3. **Live interview updates**

### Phase 3 (Nice-to-have - Week 3)

1. **Advanced reporting and analytics**
2. **Export functionality**
3. **Historical interview data**

---

## Technical Implementation Notes

### State Management

```typescript
// Use React Context or Zustand for interview state
interface InterviewState {
  currentStage: InterviewStage;
  progress: InterviewProgress;
  summary: InterviewSummary | null;
  grammarFeedback: GrammarAssessment[];
}
```

### WebSocket Integration

```typescript
// For real-time updates from the interview agent
const interviewSocket = new WebSocket(
  `ws://localhost:8000/interview/${roomName}`
);
```

### Data Persistence

```typescript
// Store interview data in database
interface InterviewRecord {
  id: string;
  roomName: string;
  candidateName: string;
  role: string;
  skillLevel: string;
  startTime: Date;
  endTime: Date;
  summary: InterviewSummary;
  rawData: any;
}
```

---

## Testing Requirements

1. **End-to-end interview flow testing**
2. **Real-time data synchronization testing**
3. **Grammar assessment accuracy validation**
4. **Performance testing with long interviews**
5. **Error handling for network interruptions**

---

## Security Considerations

1. **Candidate data privacy and encryption**
2. **Secure API endpoints with authentication**
3. **Interview recording consent management**
4. **Data retention and deletion policies**

---

This comprehensive update will transform the interview experience from a simple voice chat to a professional, structured interview platform with detailed analytics and reporting capabilities.
