import axios from 'axios';

// Get the API URL from environment variables or use default
const baseURL = 'http://localhost:3000';

export const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Add request interceptor for authentication if needed
api.interceptors.request.use(
  (config) => {
    // Add authentication token from local storage if available
    const token = localStorage.getItem('authToken');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle global error responses (like 401 Unauthorized)
    if (error.response && error.response.status === 401) {
      // Handle unauthorized access - e.g., redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

// Types for our API requests and responses
export interface FinOpsQuestion {
  question: string;
  options?: {
    enhancement_enabled?: boolean;
    quality_check_enabled?: boolean;
    auto_improve_enabled?: boolean;
    quality_threshold?: number;
    cleanup_agent?: boolean;
    force_github_knowledge?: boolean;
  };
}

export interface FinOpsResponse {
  answer: string;
  citations?: Array<{ title: string; url: string }>;
}

export interface ApiResponse<T> {
  data: T | null;
  error: string | null;
}

export interface ApiEvent {
  type: string;
  content: any;
}

// API service for FinOps Expert
export const apiService = {
  // Ask a FinOps question and get a streaming response
  askFinOpsQuestionStream: async (
    question: string,
    onEvent: (event: ApiEvent) => void
  ): Promise<ApiResponse<FinOpsResponse>> => {
    try {
      const response = await api.post('/finops/ask_stream', { question });
      
      if (!response.data) {
        throw new Error('No response data received');
      }

      const reader = new ReadableStream({
        async start(controller) {
          const decoder = new TextDecoder();
          let buffer = "";
          let finalResult: FinOpsResponse | null = null;

          const processLine = (line: string) => {
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6).trim();
              if (!dataStr) return;
              try {
                const parsed = JSON.parse(dataStr);
                
                if (parsed.type === 'error') {
                  throw new Error(parsed.content);
                }
                
                if (parsed.type === 'status') {
                  // Pass status messages to UI
                  onEvent({ type: 'status', content: parsed.content });
                }
                
                // Check if this is the final result event
                if (line.startsWith('event: result')) {
                  finalResult = parsed;
                  onEvent({ type: 'result', content: parsed });
                }
              } catch (e) {
                console.error('Error parsing SSE data:', e);
              }
            }
          };

          const processBuffer = () => {
            const lines = buffer.split("\n\n");
            buffer = lines.pop() || "";
            
            lines.forEach(processLine);
          };

          processBuffer();

          while (true) {
            const { done, value } = await response.data.getReader().read();
            if (done) break;

            const chunk = new TextDecoder().decode(value, { stream: true });
            buffer += chunk;
            processBuffer();
          }

          if (!finalResult) {
            throw new Error('Stream ended without valid final response');
          }
          
          return finalResult;
        }
      });

      return { data: await response.data, error: null };
    } catch (error) {
      return { 
        data: null, 
        error: error instanceof Error ? error.message : 'Failed to process FinOps question'
      };
    }
  },

  // Ask a FinOps question and get a complete response
  askFinOpsQuestion: async (question: string): Promise<ApiResponse<FinOpsResponse>> => {
    try {
      const response = await api.post('/finops/ask', { question });

      if (!response.data) {
        throw new Error('No response data received');
      }

      return { data: response.data, error: null };
    } catch (error) {
      return {
        data: null,
        error: error instanceof Error ? error.message : 'Failed to process FinOps question'
      };
    }
  },

  // Test the Bing connection
  testBingConnection: async (): Promise<ApiResponse<{ success: boolean; message: string }>> => {
    try {
      const response = await api.post('/finops/test-bing');

      if (!response.data) {
        throw new Error('No response data received');
      }

      return { data: response.data, error: null };
    } catch (error) {
      return {
        data: null,
        error: error instanceof Error ? error.message : 'Failed to test Bing connection'
      };
    }
  }
}; 