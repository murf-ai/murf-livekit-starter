'use client';

import React, { useState } from 'react';
import {
  AlertOctagon,
  ArrowRight,
  Award,
  Check,
  Download,
  HelpCircle,
  Info,
  Lock,
  RefreshCcw,
  ShieldCheck,
  X,
} from 'lucide-react';

interface Question {
  id: number;
  text: string;
  options: string[];
  correct: number;
  explanation: string;
}

const SAFETY_TIPS = [
  {
    title: 'Never Share OTPs or PINs',
    desc: 'OTPs (One Time Passwords) and UPI/ATM PINs are highly confidential. Bank officials, police, or government coordinators will NEVER ask for them.',
    type: 'critical',
  },
  {
    title: 'Beware of Urgent Account Suspensions',
    desc: 'Fraudsters often create panic by claiming your bank account, SIM card, or scheme benefits will be suspended unless you pay or provide details immediately.',
    type: 'warning',
  },
  {
    title: 'Verify Official Communication Channels',
    desc: 'Double check phone numbers, web addresses, and emails. Official government sites always end in ".gov.in" or ".nic.in". Official banks use verified handles.',
    type: 'info',
  },
  {
    title: 'Do Not Click Unknown Links',
    desc: 'Avoid clicking links in SMS or WhatsApp claiming you have won a lottery, PM loan benefit, or tax refund. These links are phishing templates designed to steal money.',
    type: 'warning',
  },
];

const QUIZ_QUESTIONS: Question[] = [
  {
    id: 1,
    text: 'A person claiming to be a Jan Sahay scheme coordinator calls and asks for your 4-digit bank OTP to transfer your pension benefit. What should you do?',
    options: [
      "Share the OTP immediately so you don't miss the pension.",
      'Refuse to share, hang up, and visit your official bank branch.',
      'Provide a wrong OTP first to check if they are real.',
    ],
    correct: 1,
    explanation:
      'No official, bank clerk, or government representative will ever ask for your OTP. Sharing an OTP gives complete access to drain your bank account.',
  },
  {
    id: 2,
    text: 'You receive an SMS saying: "Urgent! Your PMJDY bank account is locked. Click here www.pmjdy-verify.com to unlock." What is this?',
    options: [
      'An official verification link from the government.',
      'A safe bank security protocol.',
      'A phishing scam designed to steal your credentials.',
    ],
    correct: 2,
    explanation:
      'This is a phishing message. Official government websites always end with .gov.in or .nic.in. The URL "pmjdy-verify.com" is fake and dangerous.',
  },
  {
    id: 3,
    text: 'When is it safe to type your 4-digit UPI PIN or ATM PIN?',
    options: [
      'Only when you are making a payment or checking your balance yourself on a trusted banking app/machine.',
      'When a bank helper on a phone call asks you to do it to "receive" cash.',
      'When someone is transferring money to your account.',
    ],
    correct: 0,
    explanation:
      'You only need to enter your PIN to spend/withdraw money, never to receive money. Anyone asking you to enter your PIN to "receive" funds is trying to defraud you.',
  },
  {
    id: 4,
    text: 'You suspect you have been victims of a digital banking fraud. What is the official government national helpline number to report cybercrime?',
    options: ['1930 (or cybercrime.gov.in)', '100', 'Contact local newspaper'],
    correct: 0,
    explanation:
      '1930 is the official National Cyber Crime Helpline number in India. You should call it immediately within the golden hour to freeze fraudulent transfers.',
  },
];

export function FraudView() {
  const [currentIdx, setCurrentIdx] = useState(0);
  const [selectedAns, setSelectedAns] = useState<number | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [score, setScore] = useState(0);
  const [quizFinished, setQuizFinished] = useState(false);

  const activeQuestion = QUIZ_QUESTIONS[currentIdx];

  const handleSelectOption = (optIdx: number) => {
    if (showResult) return;
    setSelectedAns(optIdx);
    setShowResult(true);
    if (optIdx === activeQuestion.correct) {
      setScore((prev) => prev + 1);
    }
  };

  const handleNext = () => {
    setShowResult(false);
    setSelectedAns(null);
    if (currentIdx < QUIZ_QUESTIONS.length - 1) {
      setCurrentIdx((prev) => prev + 1);
    } else {
      setQuizFinished(true);
    }
  };

  const handleRestart = () => {
    setCurrentIdx(0);
    setSelectedAns(null);
    setShowResult(false);
    setScore(0);
    setQuizFinished(false);
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] p-6 font-sans text-slate-800 md:p-8">
      <div className="mx-auto max-w-7xl">
        {/* Title */}
        <div className="mb-8 border-b border-slate-200 pb-6">
          <h1 className="flex items-center gap-3 text-2xl font-bold text-[#0f294a] md:text-3xl">
            <span className="rounded-xl bg-blue-50 p-2 text-[#0c538e]">
              <Lock className="size-6 md:size-8" />
            </span>
            Fraud Prevention & Digital Safety
          </h1>
          <p className="mt-1.5 text-sm text-slate-500 md:text-base">
            Learn safe digital banking practices and test your cyber-safety knowledge.
          </p>
        </div>

        {/* Safety Tips Cards */}
        <div className="mb-10 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
          {SAFETY_TIPS.map((tip, idx) => (
            <div
              key={idx}
              className={`rounded-2xl border-l-4 bg-white p-5 shadow-sm transition hover:shadow-md ${
                tip.type === 'critical'
                  ? 'border-l-rose-500'
                  : tip.type === 'warning'
                    ? 'border-l-amber-500'
                    : 'border-l-blue-500'
              }`}
            >
              <div className="mb-3 flex items-center gap-2.5">
                {tip.type === 'critical' ? (
                  <AlertOctagon className="size-5 shrink-0 text-rose-500" />
                ) : tip.type === 'warning' ? (
                  <AlertOctagon className="size-5 shrink-0 text-amber-500" />
                ) : (
                  <Info className="size-5 shrink-0 text-blue-500" />
                )}
                <h3 className="text-sm font-bold text-slate-800">{tip.title}</h3>
              </div>
              <p className="text-xs leading-relaxed font-medium text-slate-500 md:text-sm">
                {tip.desc}
              </p>
            </div>
          ))}
        </div>

        {/* Main Quiz & Cert Panel */}
        <div className="grid grid-cols-1 items-start gap-8 lg:grid-cols-12">
          {/* Cyber Safety Quiz Card */}
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm md:p-8 lg:col-span-8">
            <div className="mb-6 flex items-center justify-between border-b border-slate-100 pb-4">
              <h3 className="flex items-center gap-2 text-base font-bold text-slate-800 md:text-lg">
                <HelpCircle className="size-5 text-[#0c538e]" />
                Interactive Cyber Safety Quiz
              </h3>
              {!quizFinished && (
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-400">
                  Question {currentIdx + 1} of {QUIZ_QUESTIONS.length}
                </span>
              )}
            </div>

            {!quizFinished ? (
              <div>
                <p className="mb-6 text-sm leading-relaxed font-bold text-slate-800 md:text-base">
                  {activeQuestion.text}
                </p>

                <div className="mb-6 space-y-3.5">
                  {activeQuestion.options.map((opt, oIdx) => {
                    const isSelected = selectedAns === oIdx;
                    const isCorrect = oIdx === activeQuestion.correct;
                    const showSuccess = showResult && isCorrect;
                    const showFail = showResult && isSelected && !isCorrect;

                    return (
                      <button
                        key={oIdx}
                        onClick={() => handleSelectOption(oIdx)}
                        disabled={showResult}
                        className={`flex w-full items-center justify-between gap-3 rounded-2xl border p-4 text-left text-xs font-semibold transition duration-150 md:text-sm ${
                          showSuccess
                            ? 'border-emerald-300 bg-emerald-50 text-emerald-900 shadow-sm'
                            : showFail
                              ? 'border-rose-300 bg-rose-50 text-rose-900 shadow-sm'
                              : isSelected
                                ? 'border-slate-400 bg-slate-100 text-slate-900'
                                : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                        }`}
                      >
                        <span>{opt}</span>
                        {showSuccess && <Check className="size-5 shrink-0 text-emerald-600" />}
                        {showFail && <X className="size-5 shrink-0 text-rose-600" />}
                      </button>
                    );
                  })}
                </div>

                {showResult && (
                  <div className="mb-6 rounded-2xl border border-slate-100 bg-slate-50 p-4">
                    <p className="mb-1.5 text-xs font-bold tracking-wider text-slate-400 uppercase">
                      {selectedAns === activeQuestion.correct
                        ? '🎉 Correct Answer!'
                        : '❌ Incorrect Answer'}
                    </p>
                    <p className="text-xs leading-relaxed font-medium text-slate-600 md:text-sm">
                      {activeQuestion.explanation}
                    </p>
                  </div>
                )}

                {showResult && (
                  <div className="flex justify-end">
                    <button
                      onClick={handleNext}
                      className="inline-flex items-center gap-2 rounded-xl bg-[#0f4a73] px-5 py-2.5 text-xs font-bold text-white shadow transition hover:bg-[#0c538e] md:text-sm"
                    >
                      {currentIdx === QUIZ_QUESTIONS.length - 1 ? 'Finish Quiz' : 'Next Question'}
                      <ArrowRight className="size-4" />
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-6 text-center">
                <div className="mb-4 inline-flex rounded-3xl bg-blue-50 p-4 text-[#0c538e]">
                  <Award className="size-12" />
                </div>
                <h4 className="text-xl font-extrabold text-slate-800">Quiz Completed!</h4>
                <p className="mt-1.5 text-sm font-semibold text-slate-500">
                  You scored{' '}
                  <span className="font-bold text-[#0c538e]">
                    {score} out of {QUIZ_QUESTIONS.length}
                  </span>{' '}
                  questions correctly.
                </p>

                {score === QUIZ_QUESTIONS.length ? (
                  <p className="mt-4 inline-block rounded-full border border-emerald-100 bg-emerald-50 px-4 py-2 text-sm font-bold text-emerald-600">
                    🏆 Flawless Score! You are a Certified Safe Citizen.
                  </p>
                ) : (
                  <p className="mt-3 text-xs font-medium text-slate-500">
                    Try again to get a perfect score and unlock your safety certificate!
                  </p>
                )}

                <div className="mt-8 flex justify-center gap-4">
                  <button
                    onClick={handleRestart}
                    className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
                  >
                    <RefreshCcw className="size-4" />
                    Retake Quiz
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Certificate Sidebar Preview */}
          <div className="rounded-3xl border border-slate-200 bg-white p-6 text-center shadow-sm lg:col-span-4">
            <h3 className="mb-4 text-sm font-bold tracking-wider text-slate-500 uppercase">
              Digital Literacy Status
            </h3>

            {score === QUIZ_QUESTIONS.length && quizFinished ? (
              <div className="flex flex-col items-center rounded-2xl border-2 border-dashed border-amber-300 bg-amber-50/20 p-5">
                <div className="mb-3.5 flex size-14 items-center justify-center rounded-full bg-amber-100 text-amber-600">
                  <Award className="size-8" />
                </div>
                <h4 className="text-xs font-bold tracking-wide text-amber-800 uppercase">
                  Citizen Certificate
                </h4>
                <p className="mt-0.5 text-[10px] text-slate-400">
                  Jan Sahay Grievance & Safety Portal
                </p>

                <div className="relative my-4 w-full overflow-hidden rounded-lg border border-slate-200/60 bg-white p-3 text-left shadow-sm">
                  <div className="absolute top-0 right-0 flex size-8 items-center justify-center rounded-bl-full bg-amber-500/10 text-amber-500">
                    <ShieldCheck className="size-3.5" />
                  </div>
                  <h5 className="text-[10px] font-extrabold text-[#0f294a]">
                    CERTIFICATE OF SAFETY
                  </h5>
                  <p className="mt-0.5 text-[8px] text-slate-400">
                    Awarded to you for completing the Jan Sahay Cyber-Safety test with 100% score.
                  </p>
                  <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-2 text-[8px] font-semibold text-slate-400">
                    <span>Verified: OK</span>
                    <span>13-Aug-2026</span>
                  </div>
                </div>

                <button
                  onClick={() => alert('Certificate downloaded successfully!')}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-amber-500 py-2 text-xs font-bold text-white shadow-sm transition hover:bg-amber-600"
                >
                  <Download className="size-3.5" />
                  Download PDF
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-center rounded-2xl border border-slate-100 bg-slate-50 p-6">
                <Lock className="mb-3 size-10 text-slate-300" />
                <h4 className="text-xs font-bold tracking-wide text-slate-500 uppercase">
                  Certificate Locked
                </h4>
                <p className="mt-1 max-w-[200px] text-[10px] text-slate-400">
                  Finish the safety quiz with a perfect 4/4 score to unlock your Cyber-Safety
                  Citizen Badge.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
