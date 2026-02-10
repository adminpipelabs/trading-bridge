"use client"

import React from "react"

import { useState, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"
import {
  Send,
  X,
  Sparkles,
  Bot,
  User,
  ArrowDown,
  Loader2,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

const suggestions = [
  "Show me my best performing bot",
  "What spread should I set for SHARP?",
  "Analyze my 24h trading volume",
  "Help me create a new volume bot",
]

const initialMessages: Message[] = [
  {
    id: "1",
    role: "assistant",
    content:
      "Hi! I'm your Pipe Labs AI assistant. I can help you manage your bots, analyze performance, adjust strategies, or answer questions about market making. What would you like to do?",
    timestamp: new Date(),
  },
]

interface AiChatPanelProps {
  onClose: () => void
}

export function AiChatPanel({ onClose }: AiChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [input, setInput] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, isTyping])

  const handleSend = (text?: string) => {
    const messageText = text || input.trim()
    if (!messageText) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: messageText,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsTyping(true)

    // Simulate AI response
    setTimeout(() => {
      const responses: Record<string, string> = {
        "Show me my best performing bot":
          "Your best performing bot is **Sharp-SB-BitMart** with a P&L of **+$482.30**. It has completed 142 buys and 89 sells today with a consistent spread. The bot has been running smoothly for the past 72 hours.",
        "What spread should I set for SHARP?":
          "Based on current market conditions, I'd recommend a spread of **0.12% - 0.18%** for SHARP pairs. Your current Sharp-SB-BitMart bot is running at 0.15% which is performing well. Consider tightening to 0.12% during high-volume periods.",
        "Analyze my 24h trading volume":
          "Your combined 24h volume is **$24,891** across all bots. That's **+8.2%** compared to yesterday. Volume Bot on Coinstore is currently stopped - restarting it could add approximately $4,000-6,000 to daily volume.",
        "Help me create a new volume bot":
          "I can help you set up a new volume bot. Which exchange would you like to target? Your current active exchanges are BitMart, Coinstore, MEXC, Binance, and Gate. I'd recommend **Gate.io** since your current Gate bot is stopped and has available balance.",
      }

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          responses[messageText] ||
          `I understand you're asking about "${messageText}". Let me analyze your bot data and market conditions to give you the best recommendation. Based on your current portfolio of 6 bots (4 active), I can see several optimization opportunities.`,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, aiMessage])
      setIsTyping(false)
    }, 1500)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10">
            <Sparkles className="h-3.5 w-3.5 text-primary" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">AI Assistant</h3>
            <p className="text-xs text-muted-foreground">Powered by Pipe Labs</p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
          className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
          aria-label="Close AI panel"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex gap-3",
                message.role === "user" ? "flex-row-reverse" : "flex-row"
              )}
            >
              {/* Avatar */}
              <div
                className={cn(
                  "flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full",
                  message.role === "assistant"
                    ? "bg-primary/10"
                    : "bg-secondary"
                )}
              >
                {message.role === "assistant" ? (
                  <Bot className="h-3.5 w-3.5 text-primary" />
                ) : (
                  <User className="h-3.5 w-3.5 text-muted-foreground" />
                )}
              </div>

              {/* Bubble */}
              <div
                className={cn(
                  "max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed",
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-secondary-foreground"
                )}
              >
                {message.content.split("**").map((part, i) =>
                  i % 2 === 1 ? (
                    <strong key={i} className="font-semibold">
                      {part}
                    </strong>
                  ) : (
                    <span key={i}>{part}</span>
                  )
                )}
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {isTyping && (
            <div className="flex gap-3">
              <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-primary/10">
                <Bot className="h-3.5 w-3.5 text-primary" />
              </div>
              <div className="flex items-center gap-1.5 rounded-2xl bg-secondary px-4 py-3">
                <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:0ms]" />
                <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:150ms]" />
                <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:300ms]" />
              </div>
            </div>
          )}
        </div>

        {/* Suggestion chips - show only when there's 1 message */}
        {messages.length <= 1 && !isTyping && (
          <div className="mt-4 space-y-2">
            <p className="text-xs font-medium text-muted-foreground">Quick actions</p>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => handleSend(suggestion)}
                  className="rounded-full border border-border bg-card px-3 py-1.5 text-xs text-foreground transition-colors hover:border-primary/30 hover:bg-primary/5"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="border-t border-border p-3">
        <div className="flex items-end gap-2 rounded-xl border border-border bg-background px-3 py-2 focus-within:border-primary/40 focus-within:ring-1 focus-within:ring-primary/20">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your bots..."
            rows={1}
            className="max-h-24 flex-1 resize-none bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
          />
          <Button
            size="sm"
            onClick={() => handleSend()}
            disabled={!input.trim() || isTyping}
            className="h-8 w-8 flex-shrink-0 rounded-lg bg-primary p-0 text-primary-foreground hover:bg-primary/90 disabled:opacity-40"
            aria-label="Send message"
          >
            {isTyping ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Send className="h-3.5 w-3.5" />
            )}
          </Button>
        </div>
        <p className="mt-1.5 text-center text-[10px] text-muted-foreground">
          AI can make mistakes. Verify important trading decisions.
        </p>
      </div>
    </div>
  )
}
