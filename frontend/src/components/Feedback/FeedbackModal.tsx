import React, { useState } from 'react';
import { X, CheckCircle, AlertCircle } from 'lucide-react';

interface FeedbackModalProps {
    isOpen: boolean;
    onClose: () => void;
    originalInput: string;
    prediction: any;
    onSubmit: (correction: any) => Promise<void>;
}

export const FeedbackModal: React.FC<FeedbackModalProps> = ({
    isOpen,
    onClose,
    originalInput,
    prediction,
    onSubmit
}) => {
    const [corrections, setCorrections] = useState<any>({});
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');
    const [message, setMessage] = useState('');

    if (!isOpen) return null;

    const handleSubmit = async () => {
        setIsSubmitting(true);
        setSubmitStatus('idle');

        try {
            await onSubmit(corrections);
            setSubmitStatus('success');
            setMessage('Thank you! Your feedback helps improve the AI.');
            setTimeout(() => {
                onClose();
                setCorrections({});
                setSubmitStatus('idle');
            }, 2000);
        } catch (error) {
            setSubmitStatus('error');
            setMessage('Failed to submit feedback. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    const hasCorrections = Object.keys(corrections).length > 0;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-900 rounded-lg p-6 max-w-md w-full mx-4 border border-gray-700">
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                        📝 Help Improve AI
                    </h3>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-white transition-colors"
                    >
                        <X size={24} />
                    </button>
                </div>

                {/* Success/Error Messages */}
                {submitStatus === 'success' && (
                    <div className="mb-4 p-3 bg-green-500 bg-opacity-20 border border-green-500 rounded flex items-center gap-2 text-green-400">
                        <CheckCircle size={20} />
                        <span>{message}</span>
                    </div>
                )}

                {submitStatus === 'error' && (
                    <div className="mb-4 p-3 bg-red-500 bg-opacity-20 border border-red-500 rounded flex items-center gap-2 text-red-400">
                        <AlertCircle size={20} />
                        <span>{message}</span>
                    </div>
                )}

                {/* Description */}
                <p className="text-gray-400 mb-4 text-sm">
                    Was the AI prediction incorrect? Help us improve by providing the correct information.
                </p>

                {/* Original Input */}
                <div className="mb-4 p-3 bg-gray-800 rounded">
                    <label className="text-xs text-gray-500 uppercase">Your Input</label>
                    <p className="text-white mt-1">{originalInput}</p>
                </div>

                {/* Correction Fields */}
                <div className="space-y-3 mb-6">
                    {/* Item Type */}
                    {prediction?.item_type && (
                        <div>
                            <label className="text-sm text-gray-400 mb-1 block">
                                Item Type
                                <span className="text-xs text-gray-600 ml-2">(predicted: {prediction.item_type})</span>
                            </label>
                            <input
                                type="text"
                                defaultValue={prediction.item_type}
                                onChange={(e) => setCorrections({ ...corrections, item_type: e.target.value })}
                                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white focus:border-blue-500 focus:outline-none"
                                placeholder="e.g., laptop, phone, wallet"
                            />
                        </div>
                    )}

                    {/* Color */}
                    {prediction?.color && (
                        <div>
                            <label className="text-sm text-gray-400 mb-1 block">
                                Color
                                <span className="text-xs text-gray-600 ml-2">(predicted: {prediction.color})</span>
                            </label>
                            <input
                                type="text"
                                defaultValue={prediction.color}
                                onChange={(e) => setCorrections({ ...corrections, color: e.target.value })}
                                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white focus:border-blue-500 focus:outline-none"
                                placeholder="e.g., blue, red, black"
                            />
                        </div>
                    )}

                    {/* Brand */}
                    {prediction?.brand && (
                        <div>
                            <label className="text-sm text-gray-400 mb-1 block">
                                Brand
                                <span className="text-xs text-gray-600 ml-2">(predicted: {prediction.brand})</span>
                            </label>
                            <input
                                type="text"
                                defaultValue={prediction.brand}
                                onChange={(e) => setCorrections({ ...corrections, brand: e.target.value })}
                                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white focus:border-blue-500 focus:outline-none"
                                placeholder="e.g., Dell, Apple, Samsung"
                            />
                        </div>
                    )}
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3">
                    <button
                        onClick={onClose}
                        className="flex-1 px-4 py-2 bg-gray-800 text-gray-300 rounded hover:bg-gray-700 transition-colors"
                        disabled={isSubmitting}
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={!hasCorrections || isSubmitting}
                        className={`flex-1 px-4 py-2 rounded font-medium transition-colors ${hasCorrections && !isSubmitting
                                ? 'bg-blue-600 text-white hover:bg-blue-700'
                                : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                            }`}
                    >
                        {isSubmitting ? 'Submitting...' : 'Submit Correction'}
                    </button>
                </div>
            </div>
        </div>
    );
};
