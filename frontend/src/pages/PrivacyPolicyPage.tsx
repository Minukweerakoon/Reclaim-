import { Link } from 'react-router-dom';

function PrivacyPolicyPage() {
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
                        <h1 className="text-3xl md:text-4xl font-bold tracking-tight">Privacy Policy</h1>
                        <p className="text-sm text-slate-400 mt-2">Effective date: April 1, 2026</p>
                    </header>

                    <section className="space-y-3 text-slate-300">
                        <p>
                            Reclaim collects and processes personal information to operate a lost-and-found matching platform.
                            This policy explains what we collect, why we collect it, and how you can control your information.
                        </p>
                    </section>

                    <section className="space-y-3 text-slate-300">
                        <h2 className="text-xl font-semibold text-white">1. Information We Collect</h2>
                        <ul className="list-disc pl-5 space-y-2">
                            <li>Account details from sign-in providers: name, email, profile image, and account identifier.</li>
                            <li>Report content: item details, location, time, brand, color, descriptions, and uploaded images.</li>
                            <li>Contact details you provide for coordination (for example, phone number).</li>
                            <li>Technical usage data such as device/browser information and service logs for security and reliability.</li>
                        </ul>
                    </section>

                    <section className="space-y-3 text-slate-300">
                        <h2 className="text-xl font-semibold text-white">2. How We Use Information</h2>
                        <ul className="list-disc pl-5 space-y-2">
                            <li>To validate reports and match lost items with found-item reports.</li>
                            <li>To contact users and coordinate returns where a legitimate match is detected.</li>
                            <li>To prevent abuse, fraud, spam, or unsafe platform behavior.</li>
                            <li>To improve matching quality, reliability, and platform experience.</li>
                        </ul>
                    </section>

                    <section className="space-y-3 text-slate-300">
                        <h2 className="text-xl font-semibold text-white">3. Sharing and Disclosure</h2>
                        <ul className="list-disc pl-5 space-y-2">
                            <li>We share limited contact/report information only when needed to facilitate a likely item return.</li>
                            <li>We use trusted infrastructure and service providers to host, authenticate, and process platform data.</li>
                            <li>We may disclose information when required by law, legal process, or to protect user safety.</li>
                        </ul>
                    </section>

                    <section className="space-y-3 text-slate-300">
                        <h2 className="text-xl font-semibold text-white">4. Data Retention</h2>
                        <p>
                            We retain data as long as needed to provide matching and safety operations, resolve disputes, comply
                            with legal obligations, and maintain service integrity. You may request deletion of your account and
                            associated report data, subject to legal/safety exceptions.
                        </p>
                    </section>

                    <section className="space-y-3 text-slate-300">
                        <h2 className="text-xl font-semibold text-white">5. Security</h2>
                        <p>
                            We use reasonable technical and organizational safeguards, including encrypted transport and access
                            controls. No system can guarantee absolute security, but we continuously work to reduce risk.
                        </p>
                    </section>

                    <section className="space-y-3 text-slate-300">
                        <h2 className="text-xl font-semibold text-white">6. Your Rights and Choices</h2>
                        <ul className="list-disc pl-5 space-y-2">
                            <li>Access, update, or correct your personal information.</li>
                            <li>Request deletion of your account or reports where applicable.</li>
                            <li>Opt out of non-essential communications.</li>
                        </ul>
                    </section>

                    <section className="space-y-3 text-slate-300">
                        <h2 className="text-xl font-semibold text-white">7. Children’s Privacy</h2>
                        <p>
                            Reclaim is not intended for children under 13. If you believe a child has provided personal data,
                            contact us so we can remove it.
                        </p>
                    </section>

                    <section className="space-y-3 text-slate-300">
                        <h2 className="text-xl font-semibold text-white">8. Contact</h2>
                        <p>
                            For privacy requests, contact: <a href="mailto:privacy@reclaim.ai" className="text-indigo-300 hover:text-indigo-200">privacy@reclaim.ai</a>
                        </p>
                    </section>
                </article>
            </main>
        </div>
    );
}

export default PrivacyPolicyPage;

