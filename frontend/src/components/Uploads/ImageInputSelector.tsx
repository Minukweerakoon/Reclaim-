import React from 'react';

interface ImageInputSelectorProps {
    onCameraSelect: () => void;
    onFileSelect: () => void;
}

export const ImageInputSelector: React.FC<ImageInputSelectorProps> = ({
    onCameraSelect,
    onFileSelect
}) => {
    return (
        <div className="image-input-selector">
            <h3 className="image-input-selector__title">
                How would you like to add a photo?
            </h3>

            <div className="image-input-selector__buttons">
                <button
                    className="image-input-selector__button"
                    onClick={onCameraSelect}
                    type="button"
                >
                    <span className="image-input-selector__icon">📷</span>
                    <span className="image-input-selector__label">Take Photo</span>
                    <span className="image-input-selector__hint">Use camera</span>
                </button>

                <button
                    className="image-input-selector__button"
                    onClick={onFileSelect}
                    type="button"
                >
                    <span className="image-input-selector__icon">📁</span>
                    <span className="image-input-selector__label">Upload File</span>
                    <span className="image-input-selector__hint">Choose from device</span>
                </button>
            </div>
        </div>
    );
};
