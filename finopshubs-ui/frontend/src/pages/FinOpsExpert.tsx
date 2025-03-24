// pages/FinOpsExpert.tsx (or wherever your main chat is)
import React, { useState } from "react";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { SendIcon, Loader2, ExternalLink } from "lucide-react";
import { api } from "../lib/api";
import ChatMessage from "../components/ChatMessage";

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

  // Initial system message
  const [conversation, setConversation] = useState<Message[]>([
    {
      role: "system",
      content:
        "Welcome to the FinOps Expert Assistant! Ask me anything about FinOps, Azure cost management, or cloud financial operations.",
      timestamp: new Date().toISOString(),
    },
  ]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!question.trim()) return;

    // 1) Add user message
    const userMessage: Message = {
      role: "user",
      content: question,
      timestamp: new Date().toISOString(),
    };
    setConversation((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // 2) Insert a 'Thinking...' system message
      const loadingMessage: Message = {
        role: "system",
        content: "Thinking...",
        timestamp: new Date().toISOString(),
      };
      setConversation((prev) => [...prev, loadingMessage]);

      // 3) Call your API
      const response = await api.post("/api/finops/expert/ask", { question });

      // 4) Remove 'Thinking...' from conversation
      setConversation((prev) =>
        prev.filter((msg) => msg.content !== "Thinking...")
      );

      // 5) Build assistant message
      const assistantMessage: Message = {
        role: "assistant",
        content: response.data.answer ?? "Sorry, I couldn't process your request.",
        timestamp: new Date().toISOString(),
        sources: response.data.sources ?? [],
      };

      setConversation((prev) => [...prev, assistantMessage]);

      setQuestion("");
    } catch (error) {
      console.error("Error asking question:", error);

      // Remove 'Thinking...'
      setConversation((prev) =>
        prev.filter((msg) => msg.content !== "Thinking...")
      );

      // Show error message
      const errorMessage: Message = {
        role: "system",
        content:
          "Sorry, there was an error processing your request. Please try again later.",
        timestamp: new Date().toISOString(),
      };
      setConversation((prev) => [...prev, errorMessage]);
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
            Ask questions about FinOps, Azure cost management, or the Microsoft FinOps toolkit.
          </p>
        </CardContent>
      </Card>

      <div className="flex flex-col h-[calc(100vh-350px)]">
        <div className="flex-1 overflow-auto mb-4 border rounded-md p-4">
          <div className="space-y-4">
            {/* 6) Render each message using ChatMessage if role != user, else plain text, or unify them. */}
            {conversation.map((message, index) => (
              <div
                key={index}
                className={`flex ${
                  message.role === "user"
                    ? "justify-end"
                    : message.role === "system"
                    ? "justify-center"
                    : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : message.role === "system"
                      ? "bg-secondary text-secondary-foreground"
                      : "bg-muted text-foreground"
                  }`}
                >
                  {message.role === "user" ? (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  ) : (
                    // 💡 If system or assistant, we pass to ChatMessage
                    <ChatMessage key={index} message={message} />
                  )}

                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-4 pt-2 border-t border-gray-200">
                      <p className="text-sm font-semibold mb-1">Sources:</p>
                      <ul className="text-sm space-y-1">
                        {message.sources.map((src, idx2) => (
                          <li key={idx2} className="flex gap-2 items-center">
                            <ExternalLink className="h-4 w-4 text-blue-500" />
                            <a
                              href={src.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-500 hover:underline"
                              title={src.description || ""}
                            >
                              {src.title}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <p className="text-xs opacity-70 mt-1 text-right">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 7) Input form */}
        <form onSubmit={handleSubmit} className="flex gap-2 items-start">
          <Textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask about cloud cost optimization or the FinOps Toolkit..."
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
