import React from 'react';
import { Calendar, Plus, Sparkles, BarChart3 } from 'lucide-react';
import { X, Maximize2 } from 'lucide-react';
import AnimatedThinkingText from '../../../components/AnimatedThinkingText';
import PulseTrace from '../../../components/PulseTrace';
import { CommandInput } from '../../../components/CommandInput';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

interface PulseChatSidebarProps {
  messages: Message[];
  inputValue: string;
  isTyping: boolean;
  conversationName: string;
  onClose: () => void;
  onInputChange: (value: string) => void;
  onSendMessage: () => void;
  onFullscreen: () => void;
  messagesEndRef: React.RefObject<HTMLDivElement>;
  userName: string;
}

export const PulseChatSidebar: React.FC<PulseChatSidebarProps> = ({
  messages,
  inputValue,
  isTyping,
  conversationName,
  onClose,
  onInputChange,
  onSendMessage,
  onFullscreen,
  messagesEndRef,
  userName,
}) => {

  return (
    <div 
      className="w-[370px] h-full flex flex-col border-l border-white/10"
      style={{ backgroundColor: '#111111' }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
        <div className="flex items-center gap-2">
          <span className="text-white text-sm font-medium">{conversationName}</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={onFullscreen}
            className="p-1.5 hover:bg-white/5 rounded-md transition-colors"
            title="Open in full view"
          >
            <Maximize2 size={14} className="text-gray-400 hover:text-white" />
          </button>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-white/5 rounded-md transition-colors"
            title="Close"
          >
            <X size={14} className="text-gray-400 hover:text-white" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.length === 0 && (
          <>
            <div className="flex gap-2 mb-3">
              <div className="w-6 h-6 flex items-center justify-center flex-shrink-0 mt-0.5">
                <PulseTrace active={false} width={20} height={20} />
              </div>
              <div className="flex-1">
                <p className="text-white text-base font-semibold leading-tight">Hey {userName}, how can I help</p>
              </div>
            </div>

            {/* Quick actions (calendar-focused) */}
            <div className="space-y-2 mb-3">
              <button 
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/5 transition-colors text-left"
                onClick={() => onInputChange('Schedule my week')}
              >
                <Sparkles size={14} className="text-gray-300" />
                <span className="text-sm text-white">Schedule my week</span>
              </button>
              <button 
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/5 transition-colors text-left"
                onClick={() => onInputChange('Create a new event for tomorrow at 9am')}
              >
                <Plus size={14} className="text-gray-300" />
                <span className="text-sm text-white">Create a new event</span>
              </button>
              <button 
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/5 transition-colors text-left"
                onClick={() => onInputChange('Find a 1-hour focus block this afternoon')}
              >
                <Calendar size={14} className="text-gray-300" />
                <span className="text-sm text-white">Find time for a focus block</span>
              </button>
              <button 
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/5 transition-colors text-left"
                onClick={() => onInputChange('Show my productivity stats')}
              >
                <BarChart3 size={14} className="text-gray-300" />
                <span className="text-sm text-white">Show my productivity stats</span>
              </button>
            </div>
          </>
        )}
        {messages.map((message) => (
          <div key={message.id}>
            {message.isUser ? (
              // User message - Right aligned with gray bubble (matches ChatPage)
              <div className="flex justify-end">
                <div className="max-w-[85%] bg-[#2E2E30] rounded-3xl px-3 py-2">
                  <p className="text-white text-sm leading-5 font-normal">{message.text}</p>
                </div>
              </div>
            ) : (
              // AI message - Left aligned with PulseTrace avatar
              <div className="flex gap-2">
                <div className="w-6 h-6 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <PulseTrace active={false} width={20} height={20} />
                </div>
                <div className="flex-1">
                  <p className="text-white text-sm leading-5">{message.text}</p>
                </div>
              </div>
            )}
          </div>
        ))}
        {isTyping && (
          <div className="flex gap-2">
            <div className="w-6 h-6 flex items-center justify-center flex-shrink-0 mt-0.5">
              <PulseTrace active={true} width={20} height={20} />
            </div>
            <div className="flex-1 flex items-center">
              <AnimatedThinkingText 
                text="Thinking"
                className="text-gray-400 text-sm"
              />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-3 py-3 border-t border-white/10">
        <CommandInput
          value={inputValue}
          onChange={onInputChange}
          onSubmit={onSendMessage}
          disabled={isTyping}
          placeholder="Ask anything..."
        />
      </div>
    </div>
  );
};

