import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { getAdminContactEmail } from '../config/adminContact';

const inputClass =
  'mt-2 w-full bg-slate-900/80 border border-white/10 rounded-lg p-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none';
const labelClass = 'text-[11px] uppercase tracking-widest text-slate-400';

function ContactUsPage() {
  const adminEmail = useMemo(() => getAdminContactEmail(), []);
  const [missingItem, setMissingItem] = useState('');
  const [venue, setVenue] = useState('');
  const [whenLocal, setWhenLocal] = useState('');
  const [contactName, setContactName] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [extraNotes, setExtraNotes] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const whenDisplay = whenLocal
      ? new Date(whenLocal).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
      : '(not specified)';

    const bodyLines = [
      'Missing item report (Reclaim contact form)',
      '',
      `Missing item: ${missingItem.trim()}`,
      `Venue / place: ${venue.trim()}`,
      `When (local): ${whenDisplay}`,
      '',
      'Contact',
      `Name: ${contactName.trim()}`,
      `Email: ${contactEmail.trim()}`,
      `Phone: ${contactPhone.trim() || '(not provided)'}`,
      '',
      extraNotes.trim() ? `Additional notes:\n${extraNotes.trim()}` : '',
    ].filter(Boolean);

    const subject = 'Reclaim: Missing item at a venue';
    const params = new URLSearchParams({
      subject,
      body: bodyLines.join('\n'),
    });
    window.location.href = `mailto:${adminEmail}?${params.toString()}`;
  };

  return (
    <div className="min-h-screen w-full bg-[#08080f] text-white relative overflow-x-hidden">
      <div className="fixed top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-600/10 blur-[120px] pointer-events-none" />
      <div className="fixed bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-cyan-600/10 blur-[120px] pointer-events-none" />

      <main className="pt-14 pb-16 px-4 md:px-8 max-w-4xl mx-auto relative z-10">
        <div className="mb-8">
          <Link to="/reclaim" className="text-sm text-slate-400 hover:text-white transition-colors">
            Back to Home
          </Link>
        </div>

        <article className="glass-panel rounded-2xl p-5 md:p-8 space-y-6">
          <header>
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight">Contact us</h1>
            <p className="text-sm text-slate-400 mt-2">
              Tell us if something is missing at a venue. Submitting opens your email app with a draft to our team.
            </p>
          </header>

          <section className="text-slate-300 text-sm space-y-2">
            <p>
              We use the details you provide only to respond about this report. For broader privacy questions, see our{' '}
              <Link to="/privacy" className="text-indigo-300 hover:text-indigo-200">
                Privacy Policy
              </Link>
              .
            </p>
          </section>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="missing-item" className={labelClass}>
                Missing item
              </label>
              <input
                id="missing-item"
                type="text"
                value={missingItem}
                onChange={(ev) => setMissingItem(ev.target.value)}
                className={inputClass}
                placeholder="What is missing?"
                required
                autoComplete="off"
              />
            </div>

            <div>
              <label htmlFor="venue" className={labelClass}>
                Venue / place
              </label>
              <input
                id="venue"
                type="text"
                value={venue}
                onChange={(ev) => setVenue(ev.target.value)}
                className={inputClass}
                placeholder="Building, room, area, or address"
                required
                autoComplete="street-address"
              />
            </div>

            <div>
              <label htmlFor="when" className={labelClass}>
                When (date &amp; time)
              </label>
              <input
                id="when"
                type="datetime-local"
                value={whenLocal}
                onChange={(ev) => setWhenLocal(ev.target.value)}
                className={inputClass}
              />
              <p className="mt-1 text-xs text-slate-500">Optional but helpful if you know when the item was last seen.</p>
            </div>

            <div className="pt-2 border-t border-white/10 space-y-5">
              <p className="text-sm font-semibold text-white">Your contact details</p>
              <div>
                <label htmlFor="contact-name" className={labelClass}>
                  Name
                </label>
                <input
                  id="contact-name"
                  type="text"
                  value={contactName}
                  onChange={(ev) => setContactName(ev.target.value)}
                  className={inputClass}
                  required
                  autoComplete="name"
                />
              </div>
              <div>
                <label htmlFor="contact-email" className={labelClass}>
                  Email
                </label>
                <input
                  id="contact-email"
                  type="email"
                  value={contactEmail}
                  onChange={(ev) => setContactEmail(ev.target.value)}
                  className={inputClass}
                  required
                  autoComplete="email"
                />
              </div>
              <div>
                <label htmlFor="contact-phone" className={labelClass}>
                  Phone
                </label>
                <input
                  id="contact-phone"
                  type="tel"
                  value={contactPhone}
                  onChange={(ev) => setContactPhone(ev.target.value)}
                  className={inputClass}
                  placeholder="Optional"
                  autoComplete="tel"
                />
              </div>
            </div>

            <div>
              <label htmlFor="notes" className={labelClass}>
                Additional notes
              </label>
              <textarea
                id="notes"
                value={extraNotes}
                onChange={(ev) => setExtraNotes(ev.target.value)}
                className={`${inputClass} min-h-[100px] resize-y`}
                placeholder="Anything else that might help"
                rows={4}
              />
            </div>

            <button
              type="submit"
              className="w-full sm:w-auto px-6 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-colors"
            >
              Open email draft
            </button>
            <p className="text-xs text-slate-500">
              Your email app opens with a draft to <span className="text-slate-400">{adminEmail}</span>
              {import.meta.env.VITE_ADMIN_CONTACT_EMAIL?.trim() ? ' (from VITE_ADMIN_CONTACT_EMAIL).' : '.'}
            </p>
          </form>
        </article>
      </main>
    </div>
  );
}

export default ContactUsPage;
