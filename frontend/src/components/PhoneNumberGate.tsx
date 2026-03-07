import { useAuth } from '../contexts/AuthContext';
import { PhoneNumberModal } from './PhoneNumberModal';

export function PhoneNumberGate() {
    const { user, phoneNumber, phoneRequired, updatePhoneNumber } = useAuth();

    if (!user || !phoneRequired) {
        return null;
    }

    return (
        <PhoneNumberModal
            open={phoneRequired}
            required
            initialPhoneNumber={phoneNumber}
            onSave={updatePhoneNumber}
        />
    );
}
