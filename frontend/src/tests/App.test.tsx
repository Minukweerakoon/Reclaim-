import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';
import { vi } from 'vitest';

// Mock the useWebSocket and useValidation hooks
vi.mock('../hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    wsConnected: true,
    lastMessage: null,
    sendMessage: vi.fn(),
  }),
}));

vi.mock('../hooks/useValidation', () => ({
  useValidation: () => ({
    isLoading: false,
    error: null,
    validateText: vi.fn((text: string) => {
      if (text.includes("good description")) {
        return Promise.resolve({
          valid: true,
          completeness: { entities: ["phone", "red"], missing_info: [] },
        });
      }
      return Promise.resolve({
        valid: false,
        completeness: { entities: [], missing_info: ["color", "location"] },
      });
    }),
    validateImage: vi.fn(() => Promise.resolve({
      valid: true,
      sharpness: { valid: true },
      objects: { valid: true, detections: [{ class: "phone" }] },
    })),
    validateVoice: vi.fn(() => Promise.resolve({
      valid: true,
      transcription: { transcription: "This is a test." },
    })),
    validateComplete: vi.fn(() => Promise.resolve({
      cross_modal: { image_text: { valid: true }, voice_text: { valid: true } },
      confidence: { overall_confidence: 0.9, action: "forward_to_matching" },
      feedback: { strengths: ["Good image", "Good text"] },
    })),
  }),
}));

describe('App', () => {
  it('renders the initial welcome message', () => {
    render(<App />);
    expect(screen.getByText(/Hi! I'm here to help you report your lost item/i)).toBeInTheDocument();
  });

  it('handles text input and transitions to awaiting_image state', async () => {
    render(<App />);
    
    // Simulate initial bot message
    fireEvent.change(screen.getByPlaceholderText(/Type your message.../i), { target: { value: 'I lost my red phone' } });
    fireEvent.click(screen.getByRole('button', { name: /Send/i }));

    await waitFor(() => {
      expect(screen.getByText(/Excellent description!/i)).toBeInTheDocument();
      expect(screen.getByText(/Now, if you have a photo of your item/i)).toBeInTheDocument();
    });
  });

  // Add more tests for image upload, voice recording, and complete validation flow
});
