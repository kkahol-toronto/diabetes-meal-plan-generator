import React, { useState, useRef, useEffect } from 'react';
import ChatIcon from '@mui/icons-material/Chat';
import CloseIcon from '@mui/icons-material/Close';
import SendIcon from '@mui/icons-material/Send';
import CircularProgress from '@mui/material/CircularProgress';
import CameraAltIcon from '@mui/icons-material/CameraAlt';
import MinimizeIcon from '@mui/icons-material/Minimize';
import PendingConsumptionDialog from './PendingConsumptionDialog';
import { useApp } from '../contexts/AppContext';
import config from '../config/environment';

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  imageUrl?: string;
}

interface ChatWidgetProps {
  userToken: string;
}

const ChatWidget: React.FC<ChatWidgetProps> = ({ userToken }) => {
  const { triggerFoodLogged } = useApp();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: "👋 Hi! I'm your comprehensive health coach AI. I can help you with meal suggestions, food analysis, and health coaching based on your complete profile and health conditions. How can I assist you today?",
      isUser: false,
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  
  // Pending consumption dialog state
  const [showPendingDialog, setShowPendingDialog] = useState(false);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [pendingAnalysis, setPendingAnalysis] = useState<any>(null);
  const [pendingImageUrl, setPendingImageUrl] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleImageSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedImage(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handlePendingAccept = () => {
    // Close dialog and reset state
    setPendingId(null);
    setPendingAnalysis(null);
    setPendingImageUrl(null);
    triggerFoodLogged(); // Refresh homepage data
  };

  const handlePendingDelete = () => {
    // Reset state
    setPendingId(null);
    setPendingAnalysis(null);
    setPendingImageUrl(null);
  };

  const removeImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const sendMessage = async () => {
    if ((!inputMessage.trim() && !selectedImage) || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage,
      isUser: true,
      timestamp: new Date(),
      imageUrl: imagePreview || undefined
    };

    setMessages(prev => [...prev, userMessage]);
    const originalInput = inputMessage;
    setInputMessage('');
    setIsLoading(true);

    try {
      // Check if this is food logging intent with an image
      const isFoodLogging = selectedImage && originalInput.toLowerCase().includes('log') && 
        (originalInput.toLowerCase().includes('food') || originalInput.toLowerCase().includes('meal'));
      
      if (isFoodLogging) {
        // Use analyze-only endpoint for food logging
        const formData = new FormData();
        formData.append('image', selectedImage!);
        formData.append('meal_type', ''); // Could be parsed from message

        const response = await fetch(`${config.API_URL}/consumption/analyze-only`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${userToken}`
          },
          body: formData
        });

        if (!response.ok) {
          throw new Error('Failed to analyze food');
        }

        const data = await response.json();
        
        // Store pending data and show dialog
        setPendingId(data.pending_id);
        setPendingAnalysis(data.analysis);
        setPendingImageUrl(data.analysis?.image_url || null);
        setShowPendingDialog(true);
        
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: 'Food analyzed! Please use the Accept/Edit/Delete options to proceed with logging.',
          isUser: false,
          timestamp: new Date()
        };

        setMessages(prev => [...prev, aiMessage]);
        
      } else {
        // Regular chat functionality
        const formData = new FormData();
        formData.append('message', originalInput);
        if (selectedImage) {
          formData.append('image', selectedImage);
        }
        formData.append('session_id', 'homepage_widget');

        const response = await fetch(`${config.API_URL}/chat/message-with-image`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${userToken}`
          },
          body: formData
        });

        if (!response.ok) {
          throw new Error('Failed to send message');
        }

        const data = await response.json();
        
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: data.assistant_message || data.message || 'Sorry, I encountered an error. Please try again.',
          isUser: false,
          timestamp: new Date()
        };

        setMessages(prev => [...prev, aiMessage]);
        
        // Trigger homepage refresh if this was a food logging operation (for text-based logging)
        if (originalInput.toLowerCase().includes('log') && (originalInput.toLowerCase().includes('food') || originalInput.toLowerCase().includes('meal'))) {
          triggerFoodLogged();
        }
      }
      
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error. Please try again later.',
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      removeImage();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <>
      {/* Floating Chat Button - Left Side */}
      {!isOpen && (
        <div className="fixed left-6 top-1/2 transform -translate-y-1/2 z-50">
          <button
            onClick={() => setIsOpen(true)}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-full p-4 shadow-2xl transition-all duration-300 hover:scale-110 group flex flex-col items-center"
            style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }}
          >
            <ChatIcon sx={{ fontSize: 28, marginBottom: 1 }} />
            <span className="text-xs font-semibold tracking-wider">HEALTH AI</span>
            <div className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-6 h-6 flex items-center justify-center animate-pulse">
              🤖
            </div>
          </button>
        </div>
      )}

      {/* Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity duration-300"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Left Side Sliding Panel */}
      <div className={`fixed left-0 top-0 h-full w-96 bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="w-4 h-4 bg-green-400 rounded-full animate-pulse"></div>
            <div>
              <h2 className="text-xl font-bold">Health Coach AI</h2>
              <p className="text-blue-100 text-sm">Comprehensive Health Assistant</p>
            </div>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="text-white hover:text-gray-200 transition-colors p-2 hover:bg-white hover:bg-opacity-20 rounded-full"
          >
            <CloseIcon sx={{ fontSize: 24 }} />
          </button>
        </div>

        {/* Quick Actions */}
        <div className="p-4 bg-gray-50 border-b">
          <div className="grid grid-cols-2 gap-2">
            <button className="bg-blue-100 text-blue-700 px-3 py-2 rounded-lg text-sm font-medium hover:bg-blue-200 transition-colors">
              📊 Analyze Food
            </button>
            <button className="bg-green-100 text-green-700 px-3 py-2 rounded-lg text-sm font-medium hover:bg-green-200 transition-colors">
              🍽️ Meal Plan
            </button>
            <button className="bg-purple-100 text-purple-700 px-3 py-2 rounded-lg text-sm font-medium hover:bg-purple-200 transition-colors">
              💊 Medications
            </button>
            <button className="bg-orange-100 text-orange-700 px-3 py-2 rounded-lg text-sm font-medium hover:bg-orange-200 transition-colors">
              📈 Progress
            </button>
          </div>
        </div>

        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50" style={{ height: 'calc(100vh - 280px)' }}>
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] p-4 rounded-2xl ${
                  message.isUser
                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-br-md'
                    : 'bg-white text-gray-800 rounded-bl-md shadow-md border border-gray-200'
                }`}
              >
                {message.imageUrl && (
                  <img
                    src={message.imageUrl}
                    alt="Uploaded"
                    className="w-full h-40 object-cover rounded-lg mb-3"
                  />
                )}
                <div className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</div>
                <div className={`text-xs mt-2 ${message.isUser ? 'text-blue-100' : 'text-gray-500'}`}>
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white text-gray-800 rounded-2xl rounded-bl-md shadow-md border border-gray-200 p-4 flex items-center space-x-3">
                <CircularProgress size={20} />
                <span className="text-sm">AI is analyzing...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Image Preview */}
        {imagePreview && (
          <div className="p-4 bg-white border-t">
            <div className="relative">
              <img
                src={imagePreview}
                alt="Preview"
                className="w-full h-24 object-cover rounded-lg"
              />
              <button
                onClick={removeImage}
                className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs hover:bg-red-600"
              >
                ×
              </button>
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="p-4 bg-white border-t border-gray-200">
          <div className="flex items-end space-x-3">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImageSelect}
              accept="image/*"
              className="hidden"
            />
            
            <button
              onClick={() => fileInputRef.current?.click()}
              className="bg-gray-100 hover:bg-gray-200 text-gray-600 p-3 rounded-full transition-colors"
            >
              <CameraAltIcon sx={{ fontSize: 20 }} />
            </button>

            <div className="flex-1">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about nutrition, meal plans, or health..."
                className="w-full p-3 border border-gray-300 rounded-2xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={2}
                disabled={isLoading}
              />
            </div>

            <button
              onClick={sendMessage}
              disabled={(!inputMessage.trim() && !selectedImage) || isLoading}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-400 text-white p-3 rounded-full transition-all duration-200 disabled:cursor-not-allowed"
            >
              <SendIcon sx={{ fontSize: 20 }} />
            </button>
          </div>
        </div>
      </div>

      {/* Pending Consumption Dialog */}
      <PendingConsumptionDialog
        open={showPendingDialog}
        onClose={() => setShowPendingDialog(false)}
        pendingId={pendingId}
        analysisData={pendingAnalysis}
        imageUrl={pendingImageUrl || undefined}
        onAccept={handlePendingAccept}
        onDelete={handlePendingDelete}
      />
    </>
  );
};

export default ChatWidget; 