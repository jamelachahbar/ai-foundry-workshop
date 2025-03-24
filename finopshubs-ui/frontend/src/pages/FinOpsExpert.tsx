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

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  sources?: Source[];
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
        content: response.data.answer || "Sorry, I couldn't process your request.",
        timestamp: new Date().toISOString(),
        sources: response.data.sources || [] // Add sources from the API response
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
    
    // Replace markdown links with HTML links
    let processedContent = content.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, text, url) => {
      return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="text-blue-500 hover:underline">${text}</a>`;
    });
    
    // Replace headers
    processedContent = processedContent.replace(/^# (.*?)$/gm, '<h1 class="text-xl font-bold my-2">$1</h1>');
    processedContent = processedContent.replace(/^## (.*?)$/gm, '<h2 class="text-lg font-bold my-2">$1</h2>');
    processedContent = processedContent.replace(/^### (.*?)$/gm, '<h3 class="text-md font-bold my-2">$1</h3>');
    
    // Replace bold text
    processedContent = processedContent.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Replace line breaks with <br> tags
    processedContent = processedContent.replace(/\n/g, '<br>');
    
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
                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-4 pt-2 border-t border-gray-200">
                          <p className="text-sm font-semibold mb-1">Sources:</p>
                          <ul className="text-sm space-y-1">
                            {message.sources.map((source, idx) => (
                              <li key={idx} className="flex items-start gap-1">
                                <ExternalLink className="h-4 w-4 mt-0.5 flex-shrink-0" />
                                <a 
                                  href={source.url} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="text-blue-500 hover:underline"
                                  title={source.description || ""}
                                >
                                  {source.title}
                                </a>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
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