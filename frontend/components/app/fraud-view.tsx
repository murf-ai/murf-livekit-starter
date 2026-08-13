'use client';

import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Lock, 
  AlertOctagon, 
  HelpCircle, 
  Award, 
  Check, 
  X, 
  RefreshCcw, 
  ArrowRight, 
  Download,
  Info
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
    type: 'critical'
  },
  {
    title: 'Beware of Urgent Account Suspensions',
    desc: 'Fraudsters often create panic by claiming your bank account, SIM card, or scheme benefits will be suspended unless you pay or provide details immediately.',
    type: 'warning'
  },
  {
    title: 'Verify Official Communication Channels',
    desc: 'Double check phone numbers, web addresses, and emails. Official government sites always end in ".gov.in" or ".nic.in". Official banks use verified handles.',
    type: 'info'
  },
  {
    title: 'Do Not Click Unknown Links',
    desc: 'Avoid clicking links in SMS or WhatsApp claiming you have won a lottery, PM loan benefit, or tax refund. These links are phishing templates designed to steal money.',
    type: 'warning'
  }
];

const QUIZ_QUESTIONS: Question[] = [
  {
    id: 1,
    text: 'A person claiming to be a Jan Sahay scheme coordinator calls and asks for your 4-digit bank OTP to transfer your pension benefit. What should you do?',
    options: [
      'Share the OTP immediately so you don\'t miss the pension.',
      'Refuse to share, hang up, and visit your official bank branch.',
      'Provide a wrong OTP first to check if they are real.'
    ],
    correct: 1,
    explanation: 'No official, bank clerk, or government representative will ever ask for your OTP. Sharing an OTP gives complete access to drain your bank account.'
  },
  {
    id: 2,
    text: 'You receive an SMS saying: "Urgent! Your PMJDY bank account is locked. Click here www.pmjdy-verify.com to unlock." What is this?',
    options: [
      'An official verification link from the government.',
      'A safe bank security protocol.',
      'A phishing scam designed to steal your credentials.'
    ],
    correct: 2,
    explanation: 'This is a phishing message. Official government websites always end with .gov.in or .nic.in. The URL "pmjdy-verify.com" is fake and dangerous.'
  },
  {
    id: 3,
    text: 'When is it safe to type your 4-digit UPI PIN or ATM PIN?',
    options: [
      'Only when you are making a payment or checking your balance yourself on a trusted banking app/machine.',
      'When a bank helper on a phone call asks you to do it to "receive" cash.',
      'When someone is transferring money to your account.'
    ],
    correct: 0,
    explanation: 'You only need to enter your PIN to spend/withdraw money, never to receive money. Anyone asking you to enter your PIN to "receive" funds is trying to defraud you.'
  },
  {
    id: 4,
    text: 'You suspect you have been victims of a digital banking fraud. What is the official government national helpline number to report cybercrime?',
    options: [
      '1930 (or cybercrime.gov.in)',
      '100',
      'Contact local newspaper'
    ],
    correct: 0,
    explanation: '1930 is the official National Cyber Crime Helpline number in India. You should call it immediately within the golden hour to freeze fraudulent transfers.'
  }
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
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 font-sans p-6 md:p-8">
      <div className="mx-auto max-w-7xl">
        {/* Title */}
        <div className="border-b border-slate-200 pb-6 mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-[#0f294a] flex items-center gap-3">
            <span className="p-2 rounded-xl bg-blue-50 text-[#0c538e]">
              <Lock className="size-6 md:size-8" />
            </span>
            Fraud Prevention & Digital Safety
          </h1>
          <p className="mt-1.5 text-sm md:text-base text-slate-500">
            Learn safe digital banking practices and test your cyber-safety knowledge.
          </p>
        </div>

        {/* Safety Tips Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
          {SAFETY_TIPS.map((tip, idx) => (
            <div 
              key={idx} 
              className={`bg-white border-l-4 rounded-2xl p-5 shadow-sm hover:shadow-md transition ${
                tip.type === 'critical' ? 'border-l-rose-500' :
                tip.type === 'warning' ? 'border-l-amber-500' : 'border-l-blue-500'
              }`}
            >
              <div className="flex items-center gap-2.5 mb-3">
                {tip.type === 'critical' ? (
                  <AlertOctagon className="size-5 text-rose-500 shrink-0" />
                ) : tip.type === 'warning' ? (
                  <AlertOctagon className="size-5 text-amber-500 shrink-0" />
                ) : (
                  <Info className="size-5 text-blue-500 shrink-0" />
                )}
                <h3 className="text-sm font-bold text-slate-800">{tip.title}</h3>
              </div>
              <p className="text-xs md:text-sm text-slate-500 leading-relaxed font-medium">
                {tip.desc}
              </p>
            </div>
          ))}
        </div>

        {/* Main Quiz & Cert Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Cyber Safety Quiz Card */}
          <div className="lg:col-span-8 bg-white border border-slate-200 rounded-3xl p-6 md:p-8 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-6">
              <h3 className="text-base md:text-lg font-bold text-slate-800 flex items-center gap-2">
                <HelpCircle className="size-5 text-[#0c538e]" />
                Interactive Cyber Safety Quiz
              </h3>
              {!quizFinished && (
                <span className="text-xs font-bold text-slate-400 bg-slate-100 px-3 py-1 rounded-full">
                  Question {currentIdx + 1} of {QUIZ_QUESTIONS.length}
                </span>
              )}
            </div>

            {!quizFinished ? (
              <div>
                <p className="text-sm md:text-base font-bold text-slate-800 mb-6 leading-relaxed">
                  {activeQuestion.text}
                </p>

                <div className="space-y-3.5 mb-6">
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
                        className={`w-full text-left p-4 text-xs md:text-sm font-semibold rounded-2xl border transition duration-150 flex items-center justify-between gap-3 ${
                          showSuccess
                            ? 'bg-emerald-50 border-emerald-300 text-emerald-900 shadow-sm'
                            : showFail
                            ? 'bg-rose-50 border-rose-300 text-rose-900 shadow-sm'
                            : isSelected
                            ? 'bg-slate-100 border-slate-400 text-slate-900'
                            : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-slate-300'
                        }`}
                      >
                        <span>{opt}</span>
                        {showSuccess && <Check className="size-5 text-emerald-600 shrink-0" />}
                        {showFail && <X className="size-5 text-rose-600 shrink-0" />}
                      </button>
                    );
                  })}
                </div>

                {showResult && (
                  <div className="p-4 bg-slate-50 border border-slate-100 rounded-2xl mb-6">
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                      {selectedAns === activeQuestion.correct ? '🎉 Correct Answer!' : '❌ Incorrect Answer'}
                    </p>
                    <p className="text-xs md:text-sm text-slate-600 leading-relaxed font-medium">
                      {activeQuestion.explanation}
                    </p>
                  </div>
                )}

                {showResult && (
                  <div className="flex justify-end">
                    <button
                      onClick={handleNext}
                      className="inline-flex items-center gap-2 px-5 py-2.5 text-xs md:text-sm font-bold text-white bg-[#0f4a73] hover:bg-[#0c538e] rounded-xl shadow transition"
                    >
                      {currentIdx === QUIZ_QUESTIONS.length - 1 ? 'Finish Quiz' : 'Next Question'}
                      <ArrowRight className="size-4" />
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-6">
                <div className="inline-flex p-4 rounded-3xl bg-blue-50 text-[#0c538e] mb-4">
                  <Award className="size-12" />
                </div>
                <h4 className="text-xl font-extrabold text-slate-800">Quiz Completed!</h4>
                <p className="text-slate-500 text-sm mt-1.5 font-semibold">
                  You scored <span className="text-[#0c538e] font-bold">{score} out of {QUIZ_QUESTIONS.length}</span> questions correctly.
                </p>

                {score === QUIZ_QUESTIONS.length ? (
                  <p className="mt-4 text-emerald-600 text-sm font-bold bg-emerald-50 inline-block px-4 py-2 rounded-full border border-emerald-100">
                    🏆 Flawless Score! You are a Certified Safe Citizen.
                  </p>
                ) : (
                  <p className="mt-3 text-slate-500 text-xs font-medium">
                    Try again to get a perfect score and unlock your safety certificate!
                  </p>
                )}

                <div className="mt-8 flex justify-center gap-4">
                  <button
                    onClick={handleRestart}
                    className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 transition shadow-sm"
                  >
                    <RefreshCcw className="size-4" />
                    Retake Quiz
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Certificate Sidebar Preview */}
          <div className="lg:col-span-4 bg-white border border-slate-200 rounded-3xl p-6 shadow-sm text-center">
            <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-4">
              Digital Literacy Status
            </h3>

            {score === QUIZ_QUESTIONS.length && quizFinished ? (
              <div className="border-2 border-dashed border-amber-300 bg-amber-50/20 rounded-2xl p-5 flex flex-col items-center">
                <div className="size-14 rounded-full bg-amber-100 flex items-center justify-center text-amber-600 mb-3.5">
                  <Award className="size-8" />
                </div>
                <h4 className="text-xs font-bold text-amber-800 uppercase tracking-wide">Citizen Certificate</h4>
                <p className="text-[10px] text-slate-400 mt-0.5">Jan Sahay Grievance & Safety Portal</p>
                
                <div className="border border-slate-200/60 bg-white w-full rounded-lg p-3 my-4 text-left shadow-sm relative overflow-hidden">
                  <div className="absolute top-0 right-0 size-8 bg-amber-500/10 rounded-bl-full flex items-center justify-center text-amber-500">
                    <ShieldCheck className="size-3.5" />
                  </div>
                  <h5 className="text-[10px] font-extrabold text-[#0f294a]">CERTIFICATE OF SAFETY</h5>
                  <p className="text-[8px] text-slate-400 mt-0.5">Awarded to you for completing the Jan Sahay Cyber-Safety test with 100% score.</p>
                  <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-2 text-[8px] text-slate-400 font-semibold">
                    <span>Verified: OK</span>
                    <span>13-Aug-2026</span>
                  </div>
                </div>

                <button 
                  onClick={() => alert('Certificate downloaded successfully!')}
                  className="w-full inline-flex items-center justify-center gap-2 py-2 text-xs font-bold text-white bg-amber-500 hover:bg-amber-600 rounded-xl transition shadow-sm"
                >
                  <Download className="size-3.5" />
                  Download PDF
                </button>
              </div>
            ) : (
              <div className="bg-slate-50 rounded-2xl p-6 flex flex-col items-center border border-slate-100">
                <Lock className="size-10 text-slate-300 mb-3" />
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wide">Certificate Locked</h4>
                <p className="text-[10px] text-slate-400 mt-1 max-w-[200px]">
                  Finish the safety quiz with a perfect 4/4 score to unlock your Cyber-Safety Citizen Badge.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
