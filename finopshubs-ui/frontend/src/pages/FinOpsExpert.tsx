import React, { useState } from "react";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { SendIcon, Loader2 } from "lucide-react";
import { api } from "../lib/api";

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
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
                  <p className="whitespace-pre-wrap">{message.content}</p>
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