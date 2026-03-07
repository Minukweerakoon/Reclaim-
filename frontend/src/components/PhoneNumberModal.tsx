import { useEffect, useState } from 'react';

interface PhoneNumberModalProps {
    open: boolean;
    required?: boolean;
    initialPhoneNumber?: string;
    onSave: (phoneNumber: string) => Promise<void>;
    onClose?: () => void;
}

export function PhoneNumberModal({
    open,
    required = false,
    initialPhoneNumber = '',
    onSave,
    onClose,
}: PhoneNumberModalProps) {
    const [phoneNumber, setPhoneNumber] = useState(initialPhoneNumber);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        if (open) {
            setPhoneNumber(initialPhoneNumber || '');
            setError('');
            setSaving(false);
        }
    }, [open, initialPhoneNumber]);

    if (!open) return null;

    const validatePhone = (value: string) => {
        const clean = value.trim();
        if (!clean) return 'Mobile number is required.';
        const ok = /^\+?[0-9\s()-]{7,20}$/.test(clean);
        if (!ok) return 'Enter a valid mobile number.';
        return '';
    };

    const handleSave = async () => {
        const validationError = validatePhone(phoneNumber);
        if (validationError) {
            setError(validationError);
            return;
        }
        setSaving(true);
        setError('');
        try {
            await onSave(phoneNumber.trim());
            if (onClose) onClose();
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Failed to save mobile number.';
            setError(message);
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
            <div className="w-full max-w-md glass-panel rounded-2xl border border-white/10 shadow-[0_24px_80px_rgba(0,0,0,0.55)] p-6 animate-fade-in">
                <h3 className="text-lg font-semibold text-white">{required ? 'Add Your Mobile Number' : 'Change Mobile Number'}</h3>
                <p className="text-sm text-slate-400 mt-1">
                    {required
                        ? 'Please add your mobile number to continue. We will ask this on login until saved.'
                        : 'Update your mobile number for your profile.'}
                </p>

                <div className="mt-5">
                    <label className="text-xs uppercase tracking-wider text-slate-400">Mobile Number</label>
                    <input
                        value={phoneNumber}
                        onChange={(e) => setPhoneNumber(e.target.value)}
                        placeholder="e.g. +94 77 123 4567"
                        className="mt-2 w-full rounded-xl bg-white/[0.03] border border-white/10 px-3 py-2.5 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                    />
                    {error ? <p className="mt-2 text-xs text-red-400">{error}</p> : null}
                </div>

                <div className="mt-6 flex items-center justify-end gap-2">
                    {!required ? (
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-sm rounded-lg border border-white/10 text-slate-300 hover:bg-white/5"
                        >
                            Cancel
                        </button>
                    ) : null}
                    <button
                        type="button"
                        onClick={handleSave}
                        disabled={saving}
                        className="px-4 py-2 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-60"
                    >
                        {saving ? 'Saving...' : 'Save Number'}
                    </button>
                </div>
            </div>
        </div>
    );
}
