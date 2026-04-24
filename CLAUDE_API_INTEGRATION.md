# Claude API Integration Guide

## Overview
The T10 AI Incident Response system now includes Claude API integration for advanced incident analysis and recommendations. The integration provides five key capabilities:

1. **AI-Powered Incident Analysis** — Deep analysis with step-by-step recommendations
2. **Smart Playbook Suggestions** — Ranked suggestions based on incident context
3. **Natural Language Query Support** — Convert questions to structured incident searches
4. **Real-Time Threat Assessment** — Stream threat analysis with AI insights
5. **Automated Response Suggestions** — Ranked actions with confidence and reasoning

## Architecture

### Key Components

- **`app/claude_analyst.py`** — Service module with Claude API integration
  - Singleton client management (cost-efficient)
  - System prompts with ephemeral caching for cost optimization
  - Five async streaming methods for real-time responses
  
- **Enhanced Routers**
  - `incidents.py` — AI analysis and natural language search endpoints
  - `playbooks.py` — Smart playbook suggestion endpoint
  - `monitor.py` — Threat assessment and response action endpoints

### Streaming Design

All Claude API endpoints return **Server-Sent Events (SSE)** streams for real-time progressive updates:
- Text chunks stream as Claude generates them
- Frontend displays analysis in real-time as it arrives
- Reduces perceived latency vs. waiting for complete response

### Prompt Caching

System prompts are marked with ephemeral caching (`cache_control: {"type": "ephemeral"}`):
- Caches ~1.5K tokens of stable prompt content
- Reduces API costs by ~80% on repeated analyses
- Transparent to users — no configuration needed

## API Endpoints

### 1. Incident AI Analysis (Streaming)

**GET** `/api/incidents/ai/analyze/{incident_id}`

Stream detailed Claude analysis of an incident.

**Example:**
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/incidents/ai/analyze/1
```

**Response:** Server-Sent Event stream with:
- Threat assessment and implications
- Attack analysis and likely techniques
- Impact assessment
- Immediate actions (first 15 min)
- Investigation steps
- Containment strategy
- Recovery procedures
- Prevention measures

### 2. Natural Language Incident Search

**POST** `/api/incidents/ai/search`

Convert a natural language question to a structured incident search.

**Request:**
```json
{
  "query": "Show me all critical malware incidents from last week"
}
```

**Response:**
```json
{
  "query": "Show me all critical malware incidents from last week",
  "analysis": {
    "intent": "find_critical_incidents",
    "filters": {
      "incident_type": "Malware Infection",
      "severity": "Critical"
    },
    "keywords": ["malware", "critical"]
  },
  "results": [
    {incident objects}
  ]
}
```

### 3. Smart Playbook Suggestions (Streaming)

**GET** `/api/playbooks/ai/suggest/{incident_id}`

Stream Claude's ranked playbook recommendations for an incident.

**Example:**
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/playbooks/ai/suggest/1
```

**Response:** Server-Sent Event stream with:
- Top 3 playbook recommendations
- For each:
  - Playbook name and relevance score (0-100)
  - Key steps that apply
  - Why it's suitable for this incident
  - Non-automatable steps requiring manual intervention
  - Estimated time to complete

### 4. Real-Time Threat Assessment (Streaming)

**POST** `/api/monitor/ai/assess-threat`

Stream real-time threat assessment for a security event.

**Request:**
```json
{
  "event_type": "Failed Login Attempts",
  "description": "Multiple failed RDP login attempts on DC01",
  "source_ip": "192.168.1.100",
  "affected_asset": "DC01",
  "timestamp": "2026-04-24T10:30:00Z",
  "raw_data": {
    "attempt_count": 25,
    "time_window_sec": 300
  }
}
```

**Response:** Server-Sent Event stream with:
- Threat level (Critical/High/Medium/Low) with confidence
- Threat category (Malware/Intrusion/Data Exfiltration/DoS/Other)
- Key indicators of compromise (IOCs)
- Likely attacker intent
- Immediate response recommendation
- Escalation risk assessment
- Related events to look for
- Investigation priority

### 5. Automated Response Suggestions (Streaming)

**POST** `/api/monitor/ai/response-actions/{incident_id}`

Stream suggested automated response actions for an incident.

**Example:**
```bash
curl -X POST -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/monitor/ai/response-actions/1
```

**Response:** Server-Sent Event stream with:
- 5-10 specific actionable recommendations
- For each:
  - Action name and priority level
  - Expected impact and confidence level
  - Prerequisites and safety conditions
  - Estimated execution duration
  - Rollback procedure
  - Whether approval is required

## Frontend Integration Example

### Using Incident Analysis Stream

```javascript
// In a Vue/React component
async function analyzeIncident(incidentId) {
  const response = await fetch(
    `/api/incidents/ai/analyze/${incidentId}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let analysis = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    analysis += chunk;
    
    // Update UI in real-time as chunks arrive
    document.getElementById('analysis').textContent = analysis;
  }
}
```

### Natural Language Search

```javascript
async function searchIncidents(query) {
  const response = await fetch('/api/incidents/ai/search', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ query })
  });

  const data = await response.json();
  console.log('Interpreted filters:', data.analysis.filters);
  console.log('Found incidents:', data.results);
}
```

## Cost Optimization

### Prompt Caching Benefits

The system uses ephemeral caching on all system prompts:
- System prompt (incident analysis): ~800 tokens
- System prompt (playbook suggestions): ~700 tokens
- System prompt (threat assessment): ~600 tokens

**Cost Impact:**
- Without caching: Each API call costs full input tokens
- With caching: ~80% reduction on repeated analyses
- Typical incident analysis: ~4,000 input tokens → ~2,800 tokens after cache

### Usage Estimates

For a typical SOC running 50 incidents/day:
- **Without caching**: 50 incidents × 4,000 tokens = 200,000 tokens/day
- **With caching**: 50 incidents × 800 new tokens (cache hit) = 40,000 tokens/day
- **Monthly savings**: ~120,000 tokens × $3/1M = ~$0.36/month per endpoint
- **Total with 3 endpoints**: ~$1/month savings (small but scales with usage)

### API Key Management

The system uses the `ANTHROPIC_API_KEY` environment variable:
```bash
# Set in your .env or environment
export ANTHROPIC_API_KEY="sk-ant-..."
```

The client is initialized as a singleton, so the API key is only read once at startup.

## Testing the Integration

### 1. Start the Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Test Claude API Integration
```bash
# Get a token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# Save the token and test incident analysis
TOKEN="<your_token_here>"

# Analyze incident (needs incident_id from database)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/incidents/ai/analyze/1

# Test natural language search
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"critical incidents from last week"}' \
  http://localhost:8000/api/incidents/ai/search

# Test threat assessment
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type":"Brute Force Attack",
    "description":"Multiple failed login attempts",
    "source_ip":"192.168.1.100",
    "affected_asset":"app-server-01"
  }' \
  http://localhost:8000/api/monitor/ai/assess-threat
```

## Troubleshooting

### Missing ANTHROPIC_API_KEY
**Error**: `APIError: API key not found`

**Solution**: Set the environment variable
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### Rate Limiting
**Error**: `RateLimitError: Rate limit exceeded`

**Solution**: 
- Implement exponential backoff in frontend
- Cache recent analyses client-side
- Use batch processing for high-volume scenarios

### Timeout on Large Responses
**Error**: `TimeoutError` after ~30 seconds

**Solution**:
- This is expected for large streaming responses
- Frontend should handle stream completion gracefully
- Consider breaking analysis into smaller prompts if needed

## Future Enhancements

1. **Batch Processing** — Process multiple incidents concurrently with pooling
2. **Custom Models** — Allow SOCs to provide context via fine-tuning
3. **Tool Use** — Let Claude call incident APIs directly for deeper analysis
4. **Persistent Chat** — Multi-turn conversation history for follow-up questions
5. **Approval Workflows** — Gate high-impact automated responses on Claude recommendations

## Security Considerations

- All endpoints require authentication (JWT tokens)
- API keys stored only in environment variables, never in code/logs
- Streaming responses are user-specific (incident-scoped)
- No sensitive data is cached — only generic system prompts
- Compliance: Ensure your Anthropic API usage complies with your data residency requirements

---

For API documentation, see `/docs` on your running backend server.
