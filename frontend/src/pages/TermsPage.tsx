import { Link } from 'react-router-dom';

function TermsPage() {
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
                        <h1 className="text-3xl md:text-4xl font-bold tracking-tight">Terms of Service</h1>
                        <p className="text-sm text-slate-400 mt-2">Effective date: April 1, 2026</p>
                    </header>

                    <section className="space-y-3 text-slate-300">
                        <p>
                            These Terms govern your use of Reclaim. By accessing or using the service, you agree to these Terms.
                            If you do not agree, you must stop using the platform.
                        </p>
                    </section>

                    <section className="space-y-3 text-slate-300">
                        <h2 className="text-xl font-semibold text-white">1. Service Overview</h2>
                        <p>
                            Reclaim helps users report lost and found items, match reports, and facilitate communication between
                            relevant users. Reclaim does not guarantee item recovery or identity verification beyond platform checks.
                        </p>
                    </section>

                    <section className="space-y-3 text-slate-300">
                        <h2 className="text-xl font-semibold text-white">2. Eligibility and Accounts</h2>
                        <ul className="list-disc pl-5 space-y-2">
                            <li>You must provide accurate account information and keep it up to date.</li>
                            <li>You are responsible for activity under your account.</li>
                            <li>You must not impersonate others or provide false identity details.</li>
                        </ul>
                    </section>

                    <section className="space-y-3 text-slate-300">
                        <h2 className="text-xl font-semibold text-white">3. User Responsibilities</h2>
                        <ul className="list-disc pl-5 space-y-2">
                            <li>Submit truthful item reports and accurate location/time details.</li>
                            <li>Upload images you are authorized to use.</li>
                            <li>Do not post harmful, illegal, fraudulent, or abusive content.</li>
                            <li>Do not attempt to scrape, disrupt, or reverse-engineer the platform.</li>
                        </ul>
                    </section>

                    <section className="space-y-3 text-slate-300">
                        <h2 className="text-xl font-semibold text-white">4. Content and License</h2>
                        <p>
                            You retain ownership of content you submit. You grant Reclaim a limited license to store, process,
                            display, and analyze that content to operate and improve matching, security, and support functions.
                        </p>
                    </section>

                    <section className="space-y-3 text-slate-300">
                        <h2 className="text-xl font-semibold text-white">5. Safety and Contact Sharing</h2>
                        <p>
                            Reclaim may display limited report/contact details when needed to support legitimate return workflows.
                            Users are responsible for safe, lawful, and respectful communication.
                        </p>
                    </section>

                    <section className="space-y-3 text-slate-300">
                        <h2 className="text-xl font-semibold text-white">6. Suspension and Termination</h2>
                        <p>
                            We may suspend or terminate access for policy violations, abuse, fraud, legal risk, or safety concerns.
                            We may remove content that violates these Terms.
                        </p>
                    </section>

                    <section className="space-y-3 text-slate-300">
                        <h2 className="text-xl font-semibold text-white">7. Disclaimer and Limitation of Liability</h2>
                        <p>
                            The service is provided on an “as is” and “as available” basis. To the extent permitted by law,
                            Reclaim is not liable for indirect, incidental, or consequential damages, data loss, or unrecovered items.
                        </p>
                    </section>

                    <section className="space-y-3 text-slate-300">
                        <h2 className="text-xl font-semibold text-white">8. Changes to Terms</h2>
                        <p>
                            We may update these Terms periodically. Continued use after updates means you accept the revised Terms.
                        </p>
                    </section>

                    <section className="space-y-3 text-slate-300">
                        <h2 className="text-xl font-semibold text-white">9. Contact</h2>
                        <p>
                            For Terms questions, contact: <a href="mailto:legal@reclaim.ai" className="text-indigo-300 hover:text-indigo-200">legal@reclaim.ai</a>
                        </p>
                    </section>
                </article>
            </main>
        </div>
    );
}

export default TermsPage;

