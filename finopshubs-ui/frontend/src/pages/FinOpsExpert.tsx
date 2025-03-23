import React, { useState } from "react";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { SendIcon, Loader2, ExternalLink } from "lucide-react";
import { api } from "../lib/api";

interface Source {
  title: string;
  url: string;
  description?: string;
}

interface Citation {
  number: string;
  url: string;
  title: string;
}

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  sources?: Source[];
  citations?: Citation[];
}

const FinOpsExpert: React.FC = () => {
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversation, setConversation] = useState<Message[]>([
    {
      role: "system",
      content: "Welcome to the FinOps Expert Assistant! Ask me anything about FinOps, Azure cost management, or cloud financial operations.",
      timestamp: new Date().toISOString()
    }
  ]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!question.trim()) {
      alert("Please enter a question to continue.");
      return;
    }

    // Add user message to conversation
    const userMessage: Message = {
      role: "user",
      content: question,
      timestamp: new Date().toISOString(),
    };
    
    setConversation([...conversation, userMessage]);
    setIsLoading(true);

    try {
      // Add loading indicator message
      const loadingMessage: Message = {
        role: "system",
        content: "Thinking...",
        timestamp: new Date().toISOString(),
      };
      setConversation(prev => [...prev, loadingMessage]);
      
      // Make API request
      const response = await api.post('/api/finops/expert/ask', { question });
      
      // Remove loading message
      setConversation(prev => prev.filter(msg => msg.content !== "Thinking..."));
      
      // Add assistant response to conversation
      const assistantMessage: Message = {
        role: "assistant",
        content: response.data.formatted_answer || response.data.answer || "Sorry, I couldn't process your request.",
        timestamp: new Date().toISOString(),
        citations: response.data.citations || [] // Store citations from the API response
      };
      
      setConversation(prev => [...prev, assistantMessage]);
      setQuestion("");
    } catch (error) {
      console.error("Error asking question:", error);
      
      // Remove loading message
      setConversation(prev => prev.filter(msg => msg.content !== "Thinking..."));
      
      // Add error message to conversation
      const errorMessage: Message = {
        role: "system",
        content: "Sorry, there was an error processing your request. Please try again later.",
        timestamp: new Date().toISOString(),
      };
      
      setConversation(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Function to render markdown for assistant messages
  const renderMarkdown = (content: string) => {
    // This is a simple markdown renderer
    // For a real app, you would use a library like react-markdown
    
    // First, let's handle the Sources section separately to avoid line break issues
    let sourcesSection = '';
    const sourcesSectionRegex = /Sources:[\s\n]+((\[[0-9]+\]\s+\[[^\]]+\]\([^)]+\)[\s\n]*)+)$/;
    const fallbackSourcesRegex = /Sources:[\s\n]+(.+)$/s;
    const sourcesMatch = content.match(sourcesSectionRegex);
    
    if (sourcesMatch) {
      // Extract the sources section
      sourcesSection = sourcesMatch[0];
      // Remove it from the main content for now
      content = content.replace(sourcesSectionRegex, '');
    } else {
      // Check for any sources section that doesn't match our expected format
      const fallbackMatch = content.match(fallbackSourcesRegex);
      if (fallbackMatch) {
        sourcesSection = fallbackMatch[0];
        content = content.replace(fallbackSourcesRegex, '');
      }
    }
    
    // Replace markdown links with HTML links in the main content
    let processedContent = content.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, text, url) => {
      return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="text-blue-500 hover:underline">${text}</a>`;
    });
    
    // Replace headers
    processedContent = processedContent.replace(/^# (.*?)$/gm, '<h1 class="text-xl font-bold my-2">$1</h1>');
    processedContent = processedContent.replace(/^## (.*?)$/gm, '<h2 class="text-lg font-bold my-2">$1</h2>');
    processedContent = processedContent.replace(/^### (.*?)$/gm, '<h3 class="text-md font-bold my-2">$1</h3>');
    
    // Replace bold text
    processedContent = processedContent.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Replace line breaks with <br> tags for the main content
    processedContent = processedContent.replace(/\n/g, '<br>');
    
    // Now handle the sources section if we found one
    if (sourcesSection) {
      const sources = sourcesSection.replace(/^Sources:[\s\n]+/, '');
      
      // Check if the sources match our expected format
      const hasExpectedFormat = /\[([0-9]+)\]\s+\[(.*?)\]\((.*?)\)/.test(sources);
      
      if (hasExpectedFormat) {
        const formattedSources = `<div class="mt-6 pt-3 border-t border-gray-200 bg-gray-50 rounded-md p-4">
          <p class="text-sm font-semibold mb-3 flex items-center text-gray-700">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            References
          </p>
          <ul class="text-sm space-y-3">
            ${sources.split(/[\r\n]+/).filter((line: string) => line.trim()).map((line: string) => {
              // Extract source number, title and URL from the markdown format
              const match = line.match(/\[([0-9]+)\]\s+\[(.*?)\]\((.*?)\)/);
              if (match) {
                const [_, number, title, url] = match;
                return `<li class="flex items-start">
                  <div class="flex-shrink-0 bg-blue-100 text-blue-800 rounded-full h-5 w-5 flex items-center justify-center mr-2 mt-0.5">
                    <span class="text-xs font-medium">${number}</span>
                  </div>
                  <a href="${url}" 
                     target="_blank" 
                     rel="noopener noreferrer" 
                     class="text-blue-600 hover:text-blue-800 hover:underline transition-colors duration-200 flex-grow"
                     title="Open reference in new tab">
                    ${title}
                    <svg xmlns="http://www.w3.org/2000/svg" class="inline-block h-3 w-3 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                </li>`;
              }
              return '';
            }).join('')}
          </ul>
        </div>`;
        
        // Append the formatted sources section to the main content
        processedContent += formattedSources;
      } else {
        // Fallback formatting for sources that don't match our expected pattern
        const fallbackSources = `<div class="mt-6 pt-3 border-t border-gray-200 bg-gray-50 rounded-md p-4">
          <p class="text-sm font-semibold mb-3 flex items-center text-gray-700">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            References
          </p>
          <div class="text-sm pl-2">${sources}</div>
        </div>`;
        
        processedContent += fallbackSources;
      }
    }
    
    return { __html: processedContent };
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>FinOps Expert Assistant</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Ask questions about Microsoft's FinOps toolkit, Azure cost management, 
            or general FinOps principles. The assistant will search for 
            the most relevant information to answer your questions.
          </p>
        </CardContent>
      </Card>

      <div className="flex flex-col h-[calc(100vh-350px)]">
        <div className="flex-1 overflow-auto mb-4 border rounded-md p-4">
          <div className="space-y-4">
            {conversation.map((message, index) => (
              <div
                key={index}
                className={`flex ${
                  message.role === "user" ? "justify-end" : 
                  message.role === "system" ? "justify-center" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : message.role === "system"
                      ? "bg-secondary text-secondary-foreground"
                      : "bg-muted"
                  }`}
                >
                  {message.role === "assistant" ? (
                    <>
                      <div dangerouslySetInnerHTML={renderMarkdown(message.content)} />
                      {/* Sources are rendered as part of the formatted_answer content */}
                    </>
                  ) : (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  )}
                  <p className="text-xs opacity-70 mt-1">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="flex gap-2 items-start">
          <Textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about FinOps, Azure cost management, or the Microsoft FinOps toolkit..."
            className="flex-1 min-h-[80px]"
            disabled={isLoading}
          />
          <Button type="submit" size="icon" disabled={isLoading}>
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <SendIcon className="h-5 w-5" />
            )}
          </Button>
        </form>
      </div>
    </div>
  );
};

export default FinOpsExpert; 