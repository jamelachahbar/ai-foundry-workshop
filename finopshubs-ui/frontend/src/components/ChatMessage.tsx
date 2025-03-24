import React, { useState, useEffect } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { Light as SyntaxHighlighter } from "react-syntax-highlighter"
import { github } from "react-syntax-highlighter/dist/esm/styles/hljs"
import { ChevronDown, ChevronRight } from "lucide-react"

interface Source {
  title: string
  url: string
  description?: string
}

interface MessageProps {
  role: "user" | "assistant" | "system"
  content: string
  timestamp: string
  sources?: Source[]
}

// Regex for <think> blocks in assistant messages
const THINK_REGEX = /<think>([\s\S]*?)<\/think>/im

const ChatMessage: React.FC<{ message: MessageProps }> = ({ message }) => {
  // 1) Detect a “Thinking...” system message
  const isThinking =
    message.role === "system" && message.content.includes("Thinking...")

  // 2) Array of mental gymnastics emojis we cycle through
  const mentalGymnastics = ["🤸", "🩰", "🤼", "🏋️", "🤾", "🤹"]
  const [gymIndex, setGymIndex] = useState(0)

  // 3) Array of funny/insightful quotes
  const quotes = [
    "“Imagination is more important than knowledge.” – Albert Einstein",
    "“The secret of getting ahead is getting started.” – Mark Twain",
    "“In the midst of chaos, there is also opportunity.” – Sun Tzu",
    "“If you think you can or you think you can’t, you’re right.” – Henry Ford",
    "“Life is 10% what happens to us and 90% how we react to it.” – Charles R. Swindoll",
    "“You miss 100% of the shots you don’t take.” – Wayne Gretzky"
  ]
  // We'll choose one random quote each time
  const [quoteIndex] = useState(() => Math.floor(Math.random() * quotes.length))

  // 4) If isThinking → rotate the mentalGymnastics emojis
  useEffect(() => {
    if (isThinking) {
      const interval = setInterval(() => {
        setGymIndex((prev) => (prev + 1) % mentalGymnastics.length)
      }, 500)
      return () => clearInterval(interval)
    }
  }, [isThinking])

  // 5) Extract <think> block from assistant content
  const match = THINK_REGEX.exec(message.content)
  const agentThinking = match ? match[1].trim() : null
  const userFacingContent = match
    ? message.content.replace(THINK_REGEX, "").trim()
    : message.content

  // For collapsible chain-of-thought
  const [showThoughtProcess, setShowThoughtProcess] = useState(false)

  // 6) Syntax highlight logic
  const renderers = {
    code({ node, inline, className, children, ...props }: any) {
      const cMatch = /language-(\w+)/.exec(className || "")
      return !inline ? (
        <SyntaxHighlighter
          language={cMatch?.[1] || "bash"}
          style={github}
          PreTag="div"
          CodeTag={
            "code"
          }
          {...props}
        >
          {String(children).replace(/\n$/, "")}
        </SyntaxHighlighter>
      ) : (
        <code className="bg-muted px-1 py-0.5 rounded text-sm font-mono">
          {children}
        </code>
      )
    },
  }

  return (
    <div
      className={`flex my-2 ${
        message.role === "user"
          ? "justify-end"
          : message.role === "system"
          ? "justify-center"
          : "justify-start"
      }`}
    >
      <div
        className={`max-w-[80%] rounded-lg p-3 whitespace-pre-wrap text-sm ${
          message.role === "user"
            ? "bg-primary text-primary-foreground"
            : message.role === "system"
            ? "bg-secondary text-secondary-foreground"
            : "bg-muted text-foreground"
        }`}
      >
        {/* 7) If system => check for \"Thinking...\" */}
        {isThinking ? (
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <span className="font-medium">
                Agent is doing mental gymnastics{" "}
                <span className="text-lg animate-bounce">
                  {mentalGymnastics[gymIndex]}
                </span>
                <span className="ml-1 animate-pulse">🧠</span>
              </span>
            </div>
            <div className="text-xs text-foreground/70 italic">
              Here’s a quote while you wait:
              <br />
              <strong>{quotes[quoteIndex]}</strong>
            </div>
          </div>
        ) : message.role === "assistant" ? (
          <>
            {/* 8) If <think> block => collapsible */}
            {agentThinking && (
              <details
                className="my-2 cursor-pointer"
                open={showThoughtProcess}
                onToggle={(e) => setShowThoughtProcess(e.currentTarget.open)}
              >
                <summary className="flex items-center gap-2 text-xs select-none">
                  {showThoughtProcess ? (
                    <ChevronDown className="w-3 h-3" />
                  ) : (
                    <ChevronRight className="w-3 h-3" />
                  )}
                  <span className="font-semibold">🤔 Agent Thought Process</span>
                  {showThoughtProcess ? "💡" : "🤫"}
                </summary>
                <div className="mt-2 text-xs italic">{agentThinking}</div>
              </details>
            )}

            {/* Assistant’s final markdown answer */}
            <ReactMarkdown
              className="prose prose-sm dark:prose-invert max-w-none"
              remarkPlugins={[remarkGfm]}
              components={renderers}
            >
              {userFacingContent}
            </ReactMarkdown>

            {/* Timestamp */}
            <p className="text-[0.7rem] opacity-70 mt-2 text-right">
              {new Date(message.timestamp).toLocaleTimeString()}
            </p>
          </>
        ) : (
          // 9) If user or system message (no \"Thinking...\"):
          <>
            <p className="whitespace-pre-wrap">{message.content}</p>
            <p className="text-[0.7rem] opacity-70 mt-2 text-right">
              {new Date(message.timestamp).toLocaleTimeString()}
            </p>
          </>
        )}
      </div>
    </div>
  )
}

export default ChatMessage
