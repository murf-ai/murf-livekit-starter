'use client';

import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  BookOpen,
  Building,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  Landmark,
  Mic,
  Search,
  Shield,
  ShieldAlert,
  Sparkles,
  Wallet,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
  isCallEnded?: boolean;
  onRestartCall?: () => void;
  micError?: boolean;
  onDismissMicError?: () => void;
  currentTab?: 'home' | 'schemes' | 'fraud' | 'complaint' | 'escalations';
  onTabChange?: (tab: 'home' | 'schemes' | 'fraud' | 'complaint' | 'escalations') => void;
  callDuration?: number | null;
}

const TRANSLATIONS: Record<string, Record<string, string>> = {
  English: {
    platformTitle: 'Jana Sahaya (ಜನ ಸಹಾಯ)',
    platformSubtitle: 'Sita AI — Your Trusted Digital Saathi',
    navHome: 'Home',
    navSchemes: 'Schemes Search',
    navFraud: 'Fraud Prevention',
    navComplaint: 'Complaint Helpline',
    navEscalations: 'Open Escalations',
    heroTitle: 'Discover Welfare Schemes & Prevent Scams via Sita AI Voice Assistant',
    heroDesc:
      'Start a real-time voice call with Sita AI (ಸೀತಾ) in Kannada, English, and Hindi. Ask queries on scheme eligibility, documents, or report digital fraud seamlessly.',
    startCallLabel: 'Click to speak with Sita',
    btnStart: 'Talk to Sita AI',
    badgeSecure: '🛡️ 100% Encrypted & Safe',
    badgeVerified: '🏛️ Official 2026 Guidelines',
    badgeDirect: '📞 Direct Helplines',
    cardSchemesTitle: 'Government Schemes',
    cardSchemesDesc:
      'PMJDY, SSY, APY, PMSBY, PMJJBY, PM-KISAN, and MUDRA scheme rules & document checklists.',
    cardFraudTitle: 'Fraud Protection',
    cardFraudDesc:
      'UPI collect scam warnings, OTP safety tips, fake electricity link alerts, and instant loan app warnings.',
    cardFinancialTitle: 'Financial Literacy',
    cardFinancialDesc:
      'Safe digital banking practices, DBT bank account linking, and zero-balance savings guides.',
    cardComplaintTitle: 'Complaint Helplines',
    cardComplaintDesc:
      'Step-by-step guidance to report cyber fraud on 1930, RBI Ombudsman, or PG Portal.',
    warningTitle: '🚨 Cyber Fraud & Scam Alert Bulletin',
    warningFooter: 'Safety Action:',
    schemeSearchTitle: '🏛️ National Welfare Schemes Directory',
    schemePlaceholder: 'Search schemes by name, eligibility, or keywords...',
    eligibilityTitle: 'Eligibility Criteria',
    documentsTitle: 'Mandatory Document Checklist',
    applyTitle: 'Official Application Process',
    backDashboard: 'Back to Dashboard',
    noSchemes: 'No schemes found',
    noSchemesDesc: "We couldn't find any government schemes matching your search parameters.",
    fraudHubTitle: '🛡️ Digital Safety & Scam Prevention Center',
    fraudBanner:
      '⚠️ Official Security Warning: Keep your bank details safe. Bank managers and government representatives will NEVER contact you demanding your UPI PIN, password, or OTP code.',
    reportActiveBtn: '🚨 Report Fraud Complaint',
    defensiveStepTitle: 'Safety Precaution:',
    complaintHeader: '📞 Step-by-Step Complaint Filing Assistance',
    complaintSub: 'Choose the category of grievance or fraud incident you wish to report:',
    wizardTitle: 'Grievance Helpline Wizard',
    stepText: 'Step',
    complaintType1: 'Cyber Crime, Phishing Link, or Electricity SMS Fraud',
    complaintType1Sub: 'Links claiming bill overdue, lottery winning SMS, or OTP leak.',
    complaintType2: 'Banking Fraud or Unauthorized UPI Collect Transaction',
    complaintType2Sub: 'Unauthorized money debits, ATM skimming, or UPI collect scam.',
    complaintType3: 'Government Scheme Disbursement / DBT Issue',
    complaintType3Sub:
      'PM-Kisan installment delays, SSY interest queries, or DBT unlinked bank accounts.',
    btnBack: 'Back to Category Selection',
    disclaimerText:
      'Disclaimer: Jan Sahay is an AI citizen awareness and guidance platform created by Mr. HEMANTH S.P. Powered by Sita AI voice assistant. Information is compiled directly from official Indian government scheme portals as of August 2026.',
    footerDev:
      'System architecture and Sita AI voice pipeline developed by Mr. HEMANTH S.P for citizen financial empowerment.',
    footerDirTitle: 'Official National Portals',
    footerHelpTitle: 'Emergency Helplines',
    footerDevTitle: 'Developer & System Information',

    micBlockedTitle: 'Microphone Permission Blocked',
    micBlockedDesc:
      'Sita AI requires microphone permission to listen and respond. Please click the lock/settings icon in your browser address bar, enable the microphone, and reload.',
    btnCancel: 'Cancel',
    btnReload: 'Reload Page',
    callCompletedTitle: 'Consultation Completed',
    callCompletedDesc:
      'Your voice consultation with Sita AI has concluded. You can start a new voice session anytime.',
    btnStartNew: 'Start New Voice Call',
    btnReturnHome: 'Return to Home Portal',
    callDurationLabel: 'Session Duration:',
    secondsLabel: 'seconds',
    minutesLabel: 'minutes',
  },
  'Kannada (ಕನ್ನಡ)': {
    platformTitle: 'ಜನ ಸಹಾಯ (Jan Sahay)',
    platformSubtitle: 'ಸೀತಾ AI — ನಿಮ್ಮ ವಿಶ್ವಸನೀಯ ಡಿಜಿಟಲ್ ಸಾಥಿ',
    navHome: 'ಮುಖಪುಟ',
    navSchemes: 'ಯೋಜನೆಗಳ ಹುಡುಕಾಟ',
    navFraud: 'ವಂಚನೆ ತಡೆಗಟ್ಟುವಿಕೆ',
    navComplaint: 'ಸಹಾಯವಾಣಿ',
    navEscalations: 'ತೆರೆದ ದೂರುಗಳು',
    heroTitle:
      'ಧ್ವನಿ AI ಸಹಾಯಕಿ ಸೀತಾ ಮೂಲಕ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳನ್ನು ಅನ್ವೇಷಿಸಿ ಮತ್ತು ಡಿಜಿಟಲ್ ವಂಚನೆ ತಡೆಯಿರಿ',
    heroDesc:
      'ಕನ್ನಡ, ಇಂಗ್ಲಿಷ್ ಮತ್ತು ಹಿಂದಿ ಭಾಷೆಗಳಲ್ಲಿ ಸೀತಾ (Sita AI) ಅವರೊಂದಿಗೆ ನೇರ ಧ್ವನಿ ಸಂಭಾಷಣೆ ನಡೆಸಿ. ಯೋಜನೆ ಅರ್ಹತೆ, ದಾಖಲೆಗಳು ಮತ್ತು ಸೈಬರ್ ವಂಚನೆ ತಡೆಗೆ ತಕ್ಷಣದ ಮಾಹಿತಿ ಪಡೆಯಿರಿ.',
    startCallLabel: 'ಸೀತಾ ಅವರೊಂದಿಗೆ ಮಾತನಾಡಲು ಕ್ಲಿಕ್ ಮಾಡಿ',
    btnStart: 'ಸೀತಾ AI ಜೊತೆ ಮಾತನಾಡಿ',
    badgeSecure: '🛡️ 100% ಸುರಕ್ಷಿತ ಸಂಭಾಷಣೆ',
    badgeVerified: '🏛️ ಅಧಿಕೃತ 2026 ಮಾರ್ಗದರ್ಶಿಗಳು',
    badgeDirect: '📞 ನೇರ ತುರ್ತು ನೆರವು',
    cardSchemesTitle: 'ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು',
    cardSchemesDesc:
      'PMJDY, SSY, APY, PMSBY, PMJJBY, PM-KISAN ಮತ್ತು ಮುದ್ರಾ ಯೋಜನೆಗಳ ನಿಯಮಗಳು ಹಾಗೂ ಅಗತ್ಯ ದಾಖಲೆಗಳು.',
    cardFraudTitle: 'ವಂಚನೆ ತಡೆಗಟ್ಟುವಿಕೆ',
    cardFraudDesc:
      'UPI ವಂಚನೆ ಎಚ್ಚರಿಕೆಗಳು, OTP ಭದ್ರತೆ, ನಕಲಿ ಕರೆಂಟ್ ಬಿಲ್ SMS ಮತ್ತು ಸಾಲ ಆಪ್ ವಂಚನೆ ಜಾಗೃತಿ.',
    cardFinancialTitle: 'ಹಣಕಾಸು ಸಾಕ್ಷರತೆ',
    cardFinancialDesc:
      'ಸುರಕ್ಷಿತ ಡಿಜಿಟಲ್ ಬ್ಯಾಂಕಿಂಗ್, DBT ಬ್ಯಾಂಕ್ ಖಾತೆ ಲಿಂಕ್ ಮತ್ತು ಶೂನ್ಯ ಬ್ಯಾಲೆನ್ಸ್ ಉಳಿತಾಯ ಖಾತೆ ಮಾಹಿತಿ.',
    cardComplaintTitle: 'ದೂರು ಸಹಾಯವಾಣಿ',
    cardComplaintDesc:
      'ಸೈಬರ್ ಅಪರಾಧ ಸಂಖ್ಯೆ 1930, RBI ಒಂಬುಡ್ಸ್‌ಮನ್ ಮತ್ತು PG ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ದೂರು ಸಲ್ಲಿಸುವ ಮಾರ್ಗದರ್ಶಿ.',
    warningTitle: '🚨 ಸೈಬರ್ ವಂಚನೆ ಜಾಗೃತಿ ಬುಲೆಟಿನ್',
    warningFooter: 'ಸುರಕ್ಷತಾ ಕ್ರಮ:',
    schemeSearchTitle: '🏛️ ರಾಷ್ಟ್ರೀಯ ಕಲ್ಯಾಣ ಯೋಜನೆಗಳ ಡೈರೆಕ್ಟರಿ',
    schemePlaceholder: 'ಯೋಜನೆಯ ಹೆಸರು ಅಥವಾ ಪ್ರಮುಖ ಪದಗಳಿಂದ ಹುಡುಕಿ...',
    eligibilityTitle: 'ಅರ್ಹತಾ ಮಾನದಂಡಗಳು',
    documentsTitle: 'ಅಗತ್ಯ ದಾಖಲೆಗಳ ಪಟ್ಟಿ',
    applyTitle: 'ಅರ್ಜಿ ಸಲ್ಲಿಸುವ ಅಧಿಕೃತ ವಿಧಾನ',
    backDashboard: 'ಮುಖಪುಟಕ್ಕೆ ಹಿಂತಿರುಗಿ',
    noSchemes: 'ಯಾವುದೇ ಯೋಜನೆಗಳು ಕಂಡುಬಂದಿಲ್ಲ',
    noSchemesDesc: 'ನಿಮ್ಮ ಹುಡುಕಾಟಕ್ಕೆ ಸೂಕ್ತವಾದ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು ಕಂಡುಬಂದಿಲ್ಲ.',
    fraudHubTitle: '🛡️ ಡಿಜಿಟಲ್ ಸುರಕ್ಷತೆ ಮತ್ತು ವಂಚನೆ ತಡೆಗಟ್ಟುವಿಕೆ ಕೇಂದ್ರ',
    fraudBanner:
      '⚠️ ಅಧಿಕೃತ ಭದ್ರತಾ ಎಚ್ಚರಿಕೆ: ಬ್ಯಾಂಕ್ ಅಧಿಕಾರಿಗಳು ಅಥವಾ ಸರ್ಕಾರಿ ಪ್ರತಿನಿಧಿಗಳು ಎಂದಿಗೂ ನಿಮ್ಮ UPI PIN, ಪಾಸ್‌ವರ್ಡ್ ಅಥವಾ OTP ಕೋಡ್ ಕೇಳುವುದಿಲ್ಲ. ಯಾರಿಗೂ ನೀಡಬೇಡಿ.',
    reportActiveBtn: '🚨 ವಂಚನೆ ದೂರು ಸಲ್ಲಿಸಿ',
    defensiveStepTitle: 'ಸುರಕ್ಷತಾ ಕ್ರಮ:',
    complaintHeader: '📞 ಹಂತ-ಹಂತದ ದೂರು ಸಹಾಯವಾಣಿ ಮಾರ್ಗದರ್ಶಿ',
    complaintSub: 'ನೀವು ವರದಿ ಮಾಡಲು ಬಯಸುವ ದೂರಿನ ವರ್ಗವನ್ನು ಆಯ್ಕೆಮಾಡಿ:',
    wizardTitle: 'ದೂರು ನೆರವಿನ ವಿಝಾರ್ಡ್',
    stepText: 'ಹಂತ',
    complaintType1: 'ಸೈಬರ್ ಅಪರಾಧ, ಫಿಷಿಂಗ್ ಲಿಂಕ್ ಅಥವಾ ಕರೆಂಟ್ ಬಿಲ್ SMS ವಂಚನೆ',
    complaintType1Sub: 'ಉಚಿತ ಕರೆಂಟ್ ಬಿಲ್ ನವೀಕರಣ, ನಕಲಿ ಲಾಟರಿ SMS ಅಥವಾ OTP ಸೋರಿಕೆಯ ಲಿಂಕ್‌ಗಳು.',
    complaintType2: 'ಬ್ಯಾಂಕಿಂಗ್ ವಂಚನೆ ಅಥವಾ ಅನಧಿಕೃತ UPI ಹಣ ಕಡಿತ',
    complaintType2Sub: 'ಅನಧಿಕೃತ ATM ಹಣ ವಿತ್‌ಡ್ರಾ ಅಥವಾ UPI Collect ಮೂಲಕ ಹಣ ಕಳೆದುಕೊಂಡಿರುವುದು.',
    complaintType3: 'ಸರ್ಕಾರಿ ಯೋಜನೆ ಕಂತು ಬಾರದಿರುವುದು / DBT ಸಮಸ್ಯೆ',
    complaintType3Sub:
      'PM-Kisan ಕಂತುಗಳ ವಿಳಂಬ, ಸುಕನ್ಯಾ ಸಮೃದ್ಧಿ ಯೋಜನೆ ಅಥವಾ ಬ್ಯಾಂಕ್ ಖಾತೆ DBT ಲಿಂಕ್ ತೊಂದರೆ.',
    btnBack: 'ವರ್ಗ ಆಯ್ಕೆಗೆ ಹಿಂತಿರುಗಿ',
    disclaimerText:
      'ಹಕ್ಕುತ್ಯಾಗ: ಜನ ಸಹಾಯವು ಶ್ರೀ ಹೇಮಂತ್ ಎಸ್.ಪಿ (Mr. HEMANTH S.P) ಅವರಿಂದ ನಿರ್ಮಿಸಲ್ಪಟ್ಟ ಸೀತಾ (Sita AI) ಧ್ವನಿ ಸಹಾಯಕ ಆಧಾರಿತ ನಾಗರಿಕ ನೆರವಿನ ವೇದಿಕೆಯಾಗಿದೆ. 2026 ರ ಅಧಿಕೃತ ಸರ್ಕಾರಿ ಮೂಲಗಳಿಂದ ಮಾಹಿತಿ ಪಡೆಯಲಾಗಿದೆ.',
    footerDev:
      'ನಾಗರಿಕರ ಹಣಕಾಸು ಜಾಗೃತಿಗಾಗಿ ಶ್ರೀ ಹೇಮಂತ್ ಎಸ್.ಪಿ (Mr. HEMANTH S.P) ಅವರಿಂದ ರೂಪಿಸಲ್ಪಟ್ಟ ಸೀತಾ AI ವ್ಯವಸ್ಥೆ.',
    footerDirTitle: 'ರಾಷ್ಟ್ರೀಯ ಅಧಿಕೃತ ಪೋರ್ಟಲ್‌ಗಳು',
    footerHelpTitle: 'ತುರ್ತು ಸಹಾಯವಾಣಿಗಳು',
    footerDevTitle: 'ಡೆವಲಪರ್ ಮತ್ತು ಸಿಸ್ಟಮ್ ಮಾಹಿತಿ',

    micBlockedTitle: 'ಮೈಕ್ರೋಫೋನ್ ಅನುಮತಿ ನಿರ್ಬಂಧಿಸಲಾಗಿದೆ',
    micBlockedDesc:
      'ಸೀತಾ AI ಧ್ವನಿ ಸಹಾಯಕಿಗೆ ನಿಮ್ಮ ಮಾತು ಕೇಳಲು ಮೈಕ್ರೋಫೋನ್ ಅನುಮತಿ ಅಗತ್ಯವಿದೆ. ದಯವಿಟ್ಟು ಬ್ರೌಸರ್ ಅಡ್ರೆಸ್ ಬಾರ್‌ನಲ್ಲಿರುವ ಲಾಕ್ ಐಕಾನ್ ಕ್ಲಿಕ್ ಮಾಡಿ ಮೈಕ್ರೋಫೋನ್ ಆನ್ ಮಾಡಿ ರೀಲೋಡ್ ಮಾಡಿ.',
    btnCancel: 'ರದ್ದುಮಾಡಿ',
    btnReload: 'ಮತ್ತೆ ಲೋಡ್ ಮಾಡಿ',
    callCompletedTitle: 'ಸಂಭಾಷಣೆ ಪೂರ್ಣಗೊಂಡಿದೆ',
    callCompletedDesc:
      'ಸೀತಾ AI ಅವರೊಂದಿಗಿನ ಧ್ವನಿ ಸಂಭಾಷಣೆ ಪೂರ್ಣಗೊಂಡಿದೆ. ನೀವು ಯಾವಾಗ ಬೇಕಾದರೂ ಹೊಸ ಕರೆಯನ್ನು ಪ್ರಾರಂಭಿಸಬಹುದು.',
    btnStartNew: 'ಹೊಸ ಧ್ವನಿ ಕರೆ ಪ್ರಾರಂಭಿಸಿ',
    btnReturnHome: 'ಮುಖಪುಟಕ್ಕೆ ಹಿಂತಿರುಗಿ',
    callDurationLabel: 'ಸಂಭಾಷಣೆಯ ಅವಧಿ:',
    secondsLabel: 'ಸೆಕೆಂಡ್‌ಗಳು',
    minutesLabel: 'ನಿಮಿಷಗಳು',
  },
  'Hindi (ಹಿन्दी)': {
    platformTitle: 'जन सहाय (Jan Sahay)',
    platformSubtitle: 'सीता AI — आपकी भरोसेमंद डिजिटल साथी',
    navHome: 'मुख्य पृष्ठ',
    navSchemes: 'योजनाएं खोजें',
    navFraud: 'धोखाधड़ी से सुरक्षा',
    navComplaint: 'शिकायत हेल्पलाइन',
    navEscalations: 'सपोर्ट एस्केलेशन',
    heroTitle:
      'सीता AI वॉइस असिस्टेंट के माध्यम से सरकारी योजनाओं की खोज करें और डिजिटल घोटालों से बचें',
    heroDesc:
      'कन्नड़, अंग्रेजी और हिंदी में सीता AI (Sita AI) के साथ वास्तविक समय में वॉइस कॉल शुरू करें। योजना की पात्रता, दस्तावेजों या डिजिटल धोखाधड़ी की रिपोर्ट करें।',
    startCallLabel: 'सीता से बात करने के लिए क्लिक करें',
    btnStart: 'सीता AI से बात करें',
    badgeSecure: '🛡️ 100% सुरक्षित कॉल',
    badgeVerified: '🏛️ आधिकारिक 2026 गाइडलाइंस',
    badgeDirect: '📞 सीधी हेल्पलाइन',
    cardSchemesTitle: 'सरकारी योजनाएं',
    cardSchemesDesc:
      'PMJDY, SSY, APY, PMSBY, PMJJBY, PM-KISAN और मुद्रा ऋण योजनाओं के नियम और दस्तावेज लिस्ट।',
    cardFraudTitle: 'धोखाधड़ी सुरक्षा',
    cardFraudDesc:
      'UPI कलेक्ट स्कैम चेतावनी, ओटीपी सुरक्षा टिप्स, फर्जी बिजली बिल मैसेज और लोन ऐप से बचाव।',
    cardFinancialTitle: 'वित्तीय साक्षरता',
    cardFinancialDesc:
      'सुरक्षित डिजिटल बैंकिंग, DBT बैंक खाता लिंकिंग और जीरो बैलेंस बचत खाता गाइड।',
    cardComplaintTitle: 'शिकायत हेल्पलाइन',
    cardComplaintDesc:
      'साइबर क्राइम हेल्पलाइन 1930, आरबीआई लोकपाल या पीजी पोर्टल पर शिकायत दर्ज करने का तरीका।',
    warningTitle: '🚨 सट्टेबाजी व साइबर धोखाधड़ी चेतावनी बुलेटिन',
    warningFooter: 'सुरक्षात्मक कदम:',
    schemeSearchTitle: '🏛️ राष्ट्रीय कल्याणकारी योजनाएं डायरेक्टरी',
    schemePlaceholder: 'योजना का नाम या मुख्य शब्दों से खोजें...',
    eligibilityTitle: 'पात्रता मानदंड',
    documentsTitle: 'आवश्यक दस्तावेजों की सूची',
    applyTitle: 'आवेदन की आधिकारिक प्रक्रिया',
    backDashboard: 'डैशबोर्ड पर वापस जाएं',
    noSchemes: 'कोई योजना नहीं मिली',
    noSchemesDesc: 'आपकी खोज के अनुसार कोई सरकारी योजना नहीं मिली।',
    fraudHubTitle: '🛡️ डिजिटल सुरक्षा और धोखाधड़ी निवारण केंद्र',
    fraudBanner:
      '⚠️ आधिकारिक सुरक्षा चेतावनी: अपने बैंक खातों को सुरक्षित रखें। बैंक अधिकारी या सरकारी कर्मचारी कभी भी आपसे आपका UPI PIN, पासवर्ड या OTP कोड नहीं मांगेंगे।',
    reportActiveBtn: '🚨 धोखाधड़ी की शिकायत दर्ज करें',
    defensiveStepTitle: 'सुरक्षात्मक कदम:',
    complaintHeader: '📞 चरण-दर-चरण शिकायत सहायता',
    complaintSub: 'वह श्रेणी चुनें जिसकी शिकायत आप दर्ज करना चाहते हैं:',
    wizardTitle: 'शिकायत हेल्पलाइन विजार्ड',
    stepText: 'चरण',
    complaintType1: 'साइबर अपराध, फ़िशिंग लिंक या बिजली बिल एसएमएस धोखाधड़ी',
    complaintType1Sub: 'बिजली बिल अपडेट, नकद इनाम मैसेज या ओटीपी लीक के फर्जी लिंक।',
    complaintType2: 'बैंकिंग धोखाधड़ी या अनधिकृत यूपीआई कलेक्ट लेनदेन',
    complaintType2Sub: 'अनधिकृत एटीएम निकासी या यूपीआई कलेक्ट फ्रॉड के माध्यम से कटे हुए पैसे।',
    complaintType3: 'सरकारी योजना की किस्त न मिलना / डीबीटी समस्या',
    complaintType3Sub:
      'पीएम-किसान किस्त में देरी, सुकन्या समृद्धि खाता या डीबीटी लिंक न होने की समस्या।',
    btnBack: 'श्रेणी चयन पर वापस जाएं',
    disclaimerText:
      'अस्वीकरण: जन सहाय श्री हेमंत एस.पी (Mr. HEMANTH S.P) द्वारा विकसित सीता (Sita AI) वॉइस असिस्टेंट आधारित नागरिक सहायता पोर्टल है।',
    footerDev:
      'नागरिक वित्तीय साक्षरता के लिए श्री हेमंत एस.पी (Mr. HEMANTH S.P) द्वारा विकसित प्रणाली एवं सीता AI डिजाइन।',
    footerDirTitle: 'राष्ट्रीय आधिकारिक पोर्टल',
    footerHelpTitle: 'आपातकालीन हेल्पलाइन',
    footerDevTitle: 'डेवलपर जानकारी',

    micBlockedTitle: 'माइक्रोफोन अनुमति अवरुद्ध',
    micBlockedDesc:
      'सीता AI को काम करने के लिए माइक्रोफोन अनुमति की आवश्यकता है। कृपया अपने ब्राउज़र एड्रेस बार में लॉक आइकन पर क्लिक करें और अनुमति दें।',
    btnCancel: 'रद्द करें',
    btnReload: 'पेज रीलोड करें',
    callCompletedTitle: 'परामर्श पूरा हुआ',
    callCompletedDesc:
      'सीता AI के साथ आपकी वॉइस कॉल समाप्त हो गई है। आप कभी भी नई कॉल शुरू कर सकते हैं।',
    btnStartNew: 'नया वॉइस कॉल शुरू करें',
    btnReturnHome: 'होम पोर्टल पर वापस जाएं',
    callDurationLabel: 'कॉल की अवधि:',
    secondsLabel: 'सेकंड',
    minutesLabel: 'मिनट',
  },
};

const FRAUD_TYPES = [
  {
    titleEn: 'UPI Collect Request Fraud',
    titleKn: 'UPI Collect ಹಣ ಕಡಿತ ವಂಚನೆ',
    titleHi: 'यूपीआई कलेक्ट रिक्वेस्ट धोखाधड़ी',
    descEn:
      "Scammers send 'Collect Requests' via Google Pay / PhonePe, claiming it is a refund or cashback reward. Remember: You NEVER enter your UPI PIN to receive money.",
    descKn:
      "ವಂಚಕರು PhonePe/GPay ನಲ್ಲಿ ಹಣ ಬಂದಿದೆ ಎಂದು 'Collect Request' ಕಳುಹಿಸುತ್ತಾರೆ. ನೆನಪಿಡಿ: ಬೇರೆಯವರಿಂದ ಹಣ ಪಡೆಯಲು ನೀವು ಎಂದಿಗೂ UPI PIN ಹಾಕಬೇಕಾಗಿಲ್ಲ.",
    descHi:
      "स्कैमर्स GPAY/PhonePe के जरिए 'कलेक्ट रिक्वेस्ट' भेजते हैं, और कहते हैं कि यह रिफंड या इनाम है। याद रखें: पैसे प्राप्त करने के लिए आपको कभी भी यूपीआई पिन दर्ज करने की आवश्यकता नहीं होती है।",
    prevEn: 'Decline any unexpected requests. Only enter PIN to send money.',
    prevKn: "ಅಪರಿಚಿತರ 'Collect' ವಿನಂತಿಯನ್ನು ತಿರಸ್ಕರಿಸಿ. ಹಣ ಕಳುಹಿಸುವಾಗ ಮಾತ್ರ PIN ಹಾಕಿ.",
    prevHi: 'किसी भी अप्रत्याशित अनुरोध को अस्वीकार करें। केवल पैसे भेजने के लिए पिन दर्ज करें।',
    icon: Shield,
    alertLevel: 'high',
  },
  {
    titleEn: 'OTP & Bank Manager Impersonation Scams',
    titleKn: 'OTP ಮತ್ತು ಬ್ಯಾಂಕ್ ಮ್ಯಾನೇಜರ್ ನಕಲಿ ಕರೆ ವಂಚನೆ',
    titleHi: 'ओटीपी और बैंकिंग प्रबंधक घोटाले',
    descEn:
      'Fraudsters call masquerading as bank officers, warning that your account or debit card is blocked and demanding your OTP or card CVV number.',
    descKn:
      'ವಂಚಕರು ಬ್ಯಾಂಕ್ ಅಧಿಕಾರಿಗಳಂತೆ ಕರೆ ಮಾಡಿ, ನಿಮ್ಮ ಖಾತೆ ಅಥವಾ ATM ಕಾರ್ಡ್ ಬ್ಲಾಕ್ ಆಗಿದೆ ಎಂದು ಹೆದರಿಸಿ OTP ಅಥವಾ CVV ಕೇಳುತ್ತಾರೆ.',
    descHi:
      'धोखाधड़ी करने वाले बैंक प्रबंधकों या सरकारी अधिकारियों का रूप धारण करके कॉल करते हैं, चेतावनी देते हैं कि आपका खाता ब्लॉक हो गया है और आपके ओटीपी की मांग करते हैं।',
    prevEn: 'Banks or government portals will never ask for your OTP. Keep it secret.',
    prevKn: 'ಬ್ಯಾಂಕ್ ಅಥವಾ ಸರ್ಕಾರಿ ಅಧಿಕಾರಿಗಳು ಎಂದಿಗೂ OTP ಕೇಳುವುದಿಲ್ಲ. ಅದನ್ನು ಯಾರಿಗೂ ನೀಡಬೇಡಿ.',
    prevHi: 'बैंक या सरकारी पोर्टल कभी भी आपका ओटीपी नहीं मांगेंगे। इसे गुप्त रखें।',
    icon: AlertTriangle,
    alertLevel: 'high',
  },
  {
    titleEn: 'Fake Electricity / Bill Overdue Link SMS',
    titleKn: 'ನಕಲಿ ಕರೆಂಟ್ ಬಿಲ್ SMS & ಲಿಂಕ್ ವಂಚನೆ',
    titleHi: 'फर्जी बिजली / बिल लिंक मैसेज',
    descEn:
      'SMS messages warning that your electricity connection will be disconnected tonight unless you click a link to pay or update KYC.',
    descKn:
      'ರಾತ್ರಿ ಕರೆಂಟ್ ಕಟ್ ಮಾಡಲಾಗುತ್ತದೆ ಎಂದು ಬರುವ SMS ಲಿಂಕ್‌ಗಳನ್ನು ಕ್ಲಿಕ್ ಮಾಡಬೇಡಿ. ಅದು ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಖಾತೆ ಖಾಲಿ ಮಾಡುವ ವಂಚನೆಯಾಗಿದೆ.',
    descHi:
      'एसएमएस चेतावनियां जिसमें दावा किया जाता है कि आज रात आपकी बिजली काट दी जाएगी जब तक कि आप एक लिंक पर क्लिक करके भुगतान नहीं करते।',
    prevEn:
      'Never click links from personal mobile numbers. Verify via official electricity bills.',
    prevKn: 'ವೈಯಕ್ತಿಕ ನಂಬರ್‌ಗಳಿಂದ ಬರುವ ಲಿಂಕ್ ಕ್ಲಿಕ್ ಮಾಡಬೇಡಿ. ಅಧಿಕೃತ ಬಿಲ್ ಮೂಲಕ ಪರಿಶೀಲಿಸಿ.',
    prevHi:
      'व्यक्तिगत मोबाइल नंबरों के लिंक पर कभी क्लिक न करें। आधिकारिक बिलों के माध्यम से सत्यापित करें।',
    icon: Landmark,
    alertLevel: 'medium',
  },
  {
    titleEn: 'Fake Instant Loan Apps & Harassment',
    titleKn: 'ನಕಲಿ ಲೋನ್ ಆಪ್ ಮತ್ತು ಬ್ಲಾಕ್‌ಮೇಲ್ ವಂಚನೆ',
    titleHi: 'फर्जी इंस्टेंट लोन ऐप्स',
    descEn:
      'Malicious illegal mobile apps offering collateral-free instant loans, which steal your phone contacts, gallery photos, and harass you with fake legal threats.',
    descKn:
      'ಯಾವುದೇ ಗ್ಯಾರಂಟಿ ಇಲ್ಲದೆ ತಕ್ಷಣ ಸಾಲ ನೀಡುವ ನಕಲಿ ಆಪ್‌ಗಳು ನಿಮ್ಮ ಫೋನ್ ಕಾಂಟ್ಯಾಕ್ಟ್‌ಗಳನ್ನು ಕದ್ದು ಹೆದರಿಸಿ ಬ್ಲಾಕ್‌ಮೇಲ್ ಮಾಡುತ್ತವೆ.',
    descHi:
      'बिना गारंटी के तुरंत ऋण देने वाले दुर्भावनापूर्ण मोबाइल ऐप, जो आपके फोन संपर्कों को चुराते हैं और ब्लैकमेल करके आपको परेशान करते हैं।',
    prevEn: 'Only use RBI-registered bank apps. Avoid downloading APK files from web links.',
    prevKn:
      'ಆರ್‌ಬಿಐ (RBI) ನೋಂದಾಯಿತ ಬ್ಯಾಂಕ್ ಆಪ್‌ಗಳನ್ನು ಮಾತ್ರ ಬಳಸಿ. ಲಿಂಕ್‌ಗಳಿಂದ APK ಡೌನ್‌ಲೋಡ್ ಮಾಡಬೇಡಿ.',
    prevHi: 'केवल आरबीआई-पंजीकृत बैंक ऐप्स का उपयोग करें। वेब लिंक से ऐप्स डाउनलोड करने से बचें।',
    icon: Wallet,
    alertLevel: 'high',
  },
];

const SCHEMES_DATA = [
  {
    nameEn: 'Pradhan Mantri Jan Dhan Yojana (PMJDY)',
    nameKn: 'ಪ್ರಧಾನ ಮಂತ್ರಿ ಜನ ಧನ್ ಯೋಜನೆ (PMJDY)',
    nameHi: 'प्रधानमंत्री जन धन योजना (पीएमजेडीवाई)',
    categoryEn: 'Banking',
    categoryKn: 'ಬ್ಯಾಂಕಿಂಗ್',
    categoryHi: 'बैंकिंग',
    descEn:
      'National Financial Inclusion mission offering zero-balance savings accounts, free RuPay debit card with ₹2 Lakh accidental insurance cover, and ₹10,000 overdraft facility.',
    descKn:
      'ಶೂನ್ಯ ಬ್ಯಾಲೆನ್ಸ್ ಉಳಿತಾಯ ಖಾತೆ, ₹2 ಲಕ್ಷ ಉಚಿತ ಅಪಘಾತ ವಿಮೆ ಹೊಂದಿರುವ RuPay ಡೆಬಿಟ್ ಕಾರ್ಡ್ ಮತ್ತು ₹10,000 ಓವರ್‌ಡ್ರಾಫ್ಟ್ ಸೌಲಭ್ಯ ಒದಗಿಸುವ ರಾಷ್ಟ್ರೀಯ ಯೋಜನೆ.',
    descHi:
      'शून्य न्यूनतम शेष आवश्यकता वाला बुनियादी बचत खाता, रुपे डेबिट कार्ड के साथ ₹2 लाख का मुफ्त दुर्घटना बीमा और ₹10,000 की ओवरड्राफ्ट सुविधा।',
    eligibilityEn:
      'Resident Indian citizens aged 10 years or above without an existing bank account.',
    eligibilityKn:
      'ಬ್ಯಾಂಕ್ ಖಾತೆ ಇಲ್ಲದಿರುವ 10 ವರ್ಷ ಅಥವಾ ಅದಕ್ಕಿಂತ ಹೆಚ್ಚಿನ ವಯಸ್ಸಿನ ಯಾವುದೇ ಭಾರತೀಯ ಪ್ರಜೆ.',
    eligibilityHi:
      '10 वर्ष या उससे अधिक आयु का कोई भी भारतीय नागरिक जिसके पास अन्य बैंक खाता नहीं है।',
    documentsEn:
      'Aadhaar Card (Primary KYC), PAN Card (if available), or Voter ID / NREGA job card.',
    documentsKn: 'ಆಧಾರ್ ಕಾರ್ಡ್, ಪಾನ್ ಕಾರ್ಡ್ (ಲಭ್ಯವಿದ್ದರೆ) ಅಥವಾ ಮತದಾರರ ಗುರುತಿನ ಚೀಟಿ.',
    documentsHi: 'आधार कार्ड (प्राथमिक KYC), पैन कार्ड, या अन्य वैध पहचान पत्र।',
    applyEn: 'Visit any commercial bank branch or authorized Bank Mitra outlet.',
    applyKn: 'ಯಾವುದೇ ವಾಣಿಜ್ಯ ಬ್ಯಾಂಕ್ ಶಾಖೆ ಅಥವಾ ಅಧಿಕೃತ ಬ್ಯಾಂಕ್ ಮಿತ್ರ ಕೇಂದ್ರಕ್ಕೆ ಭೇಟಿ ನೀಡಿ.',
    applyHi: 'किसी भी वाणिज्यिक बैंक शाखा या अधिकृत बैंक मित्र केंद्र पर जाएं।',
  },
  {
    nameEn: 'Sukanya Samriddhi Yojana (SSY)',
    nameKn: 'ಸುಕನ್ಯಾ ಸಮೃದ್ಧಿ ಯೋಜನೆ (SSY)',
    nameHi: 'सुकन्या समृद्धि योजना (एसएसवाई)',
    categoryEn: 'Banking',
    categoryKn: 'ಬ್ಯಾಂಕಿಂಗ್',
    categoryHi: 'बैंकिंग',
    descEn:
      'Government savings scheme for girl children offering high compound interest (8.2% p.a. for FY 2025-26) with EEE tax exemption under Section 80C.',
    descKn:
      'ಪೆಣ್ಣು ಮಗುವಿನ ಶಿಕ್ಷಣ ಮತ್ತು ಮದುವೆಯ ಭವಿಷ್ಯಕ್ಕಾಗಿ ವಾರ್ಷಿಕ 8.2% ಆಕರ್ಷಕ ಬಡ್ಡಿ ನೀಡುವ ತೆರಿಗೆ ರಹಿತ ಸರ್ಕಾರಿ ಉಳಿತಾಯ ಯೋಜನೆ.',
    descHi:
      'बालिकाओं के भविष्य के लिए 8.2% वार्षिक ब्याज दर और धारा 80C के तहत पूर्ण कर छूट वाली सरकारी बचत योजना।',
    eligibilityEn: 'Girl child aged 10 years or below. Maximum 2 accounts per family.',
    eligibilityKn:
      '10 ವರ್ಷ ಅಥವಾ ಅದಕ್ಕಿಂತ ಕಡಿಮೆ ವಯಸ್ಸಿನ ಹೆಣ್ಣು ಮಗು. ಒಂದು ಕುಟುಂಬದಲ್ಲಿ ಗರಿಷ್ಠ 2 ಖಾತೆಗಳು.',
    eligibilityHi: '10 वर्ष या उससे कम आयु की बालिका। प्रति परिवार अधिकतम 2 खाते।',
    documentsEn:
      'Birth Certificate of girl child, Aadhaar Card and PAN Card of parent/guardian, Proof of address.',
    documentsKn: 'ಮಗುವಿನ ಜನನ ಪ್ರಮಾಣ ಪತ್ರ, ಪೋಷಕರ ಆಧಾರ್ ಕಾರ್ಡ್, ಪಾನ್ ಕಾರ್ಡ್ ಮತ್ತು ವಿಳಾಸದ ಸಾಕ್ಷಿ.',
    documentsHi: 'बालिका का जन्म प्रमाण पत्र, माता-पिता का आधार कार्ड व पैन कार्ड।',
    applyEn: 'Open account at any Post Office branch or authorized public/private commercial bank.',
    applyKn: 'ಯಾವುದೇ ಅಂಚೆ ಕಚೇರಿ (Post Office) ಅಥವಾ ಸರ್ಕಾರಿ/ಖಾಸಗಿ ಬ್ಯಾಂಕ್ ಶಾಖೆಯಲ್ಲಿ ಖಾತೆ ತೆರೆಯಿರಿ.',
    applyHi: 'किसी भी डाकघर या अधिकृत बैंक शाखा में खाता खोलें।',
  },
  {
    nameEn: 'Atal Pension Yojana (APY)',
    nameKn: 'ಅಟಲ್ ಪಿಂಚಣಿ ಯೋಜನೆ (APY)',
    nameHi: 'अटल पेंशन योजना (एपीवाई)',
    categoryEn: 'Pension',
    categoryKn: 'ಪಿಂಚಣಿ',
    categoryHi: 'पेंशन',
    descEn:
      'Government-backed guaranteed minimum monthly pension scheme of ₹1,000 to ₹5,000 per month after age 60 for unorganized sector citizens.',
    descKn:
      '60 ವರ್ಷಗಳ ನಂತರ ಮಾಸಿಕ ₹1,000 ರಿಂದ ₹5,000 ರವರೆಗೆ ಖಾತರಿಪಡಿಸಿದ ಸರ್ಕಾರಿ ಪಿಂಚಣಿ ನೀಡುವ ಯೋಜನೆ.',
    descHi:
      'असंगठित क्षेत्र के नागरिकों के लिए 60 वर्ष की आयु के बाद ₹1,000 से ₹5,000 प्रति माह की गारंटीकृत पेंशन।',
    eligibilityEn:
      'Non-income taxpaying Indian citizens aged between 18 and 40 years with a bank account.',
    eligibilityKn:
      'ಆದಾಯ ತೆರಿಗೆ ಪಾವತಿಸದಿರುವ 18 ರಿಂದ 40 ವರ್ಷ ವಯಸ್ಸಿನ ಬ್ಯಾಂಕ್ ಖಾತೆ ಹೊಂದಿರುವ ಭಾರತೀಯ ಪ್ರಜೆಗಳು.',
    eligibilityHi: '18 से 40 वर्ष की आयु के गैर-करदाता भारतीय नागरिक।',
    documentsEn:
      'Aadhaar Card, Mobile number, Bank savings account details with auto-debit feature.',
    documentsKn: 'ಆಧಾರ್ ಕಾರ್ಡ್, ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ಮತ್ತು ಆಟೋ-ಡೆಬಿಟ್ ಸೌಲಭ್ಯವಿರುವ ಬ್ಯಾಂಕ್ ಉಳಿತಾಯ ಖಾತೆ.',
    documentsHi: 'आधार कार्ड, मोबाइल नंबर, ऑटो-डेबिट के लिए बचत बैंक खाता।',
    applyEn: 'Fill APY enrollment form via internet banking or visit your savings bank branch.',
    applyKn: 'ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಶಾಖೆಯಲ್ಲಿ ಅಥವಾ ಇಂಟರ್ನೆಟ್ ಬ್ಯಾಂಕಿಂಗ್ ಮೂಲಕ APY ಫಾರ್ಮ್ ಸಲ್ಲಿಸಿ.',
    applyHi: 'अपनी बैंक शाखा या इंटरनेट बैंकिंग के माध्यम से APY फॉर्म जमा करें।',
  },
  {
    nameEn: 'Pradhan Mantri Suraksha Bima Yojana (PMSBY)',
    nameKn: 'ಪ್ರಧಾನ ಮಂತ್ರಿ ಸುರಕ್ಷಾ ಬಿಮಾ ಯೋಜನೆ (PMSBY)',
    nameHi: 'प्रधानमंत्री सुरक्षा बीमा योजना (पीएमएसबीवाई)',
    categoryEn: 'Insurance',
    categoryKn: 'ಬೀಮಾ',
    categoryHi: 'बीमा',
    descEn:
      'Accidental insurance coverage offering ₹2 Lakh for accidental death or total disability at a nominal annual premium of just ₹20 per year.',
    descKn:
      'ವರ್ಷಕ್ಕೆ ಕೇವಲ ₹20 ಪ್ರೀಮಿಯಂನಲ್ಲಿ ₹2 ಲಕ್ಷ ಅಪಘಾತ ಮರಣ ಅಥವಾ ಪೂರ್ಣ ಅಂಗವಿಕಲತೆ ವಿಮಾ ರಕ್ಷಣೆ ನೀಡುವ ಯೋಜನೆ.',
    descHi:
      'मात्र ₹20 प्रति वर्ष के प्रीमियम पर आकस्मिक मृत्यु या पूर्ण विकलांगता के लिए ₹2 लाख का दुर्घटना बीमा।',
    eligibilityEn: 'All bank account holders aged between 18 and 70 years.',
    eligibilityKn: 'ಉಳಿತಾಯ ಬ್ಯಾಂಕ್ ಖಾತೆ ಹೊಂದಿರುವ 18 ರಿಂದ 70 ವರ್ಷ ವಯಸ್ಸಿನ ಪ್ರಜೆಗಳು.',
    eligibilityHi: '18 से 70 वर्ष की आयु के सभी बैंक खाताधारक।',
    documentsEn: 'Aadhaar Card, Savings bank account auto-debit consent form.',
    documentsKn: 'ಆಧಾರ್ ಕಾರ್ಡ್ ಮತ್ತು ಬ್ಯಾಂಕ್ ಖಾತೆ ಆಟೋ-ಡೆಬಿಟ್ ಸಮ್ಮತಿ ಫಾರ್ಮ್.',
    documentsHi: 'आधार कार्ड, बचत बैंक खाता ऑटो-डेबिट फॉर्म।',
    applyEn: 'Enroll via SMS, internet banking, or visit your savings bank branch.',
    applyKn: 'ಇಂಟರ್ನೆಟ್ ಬ್ಯಾಂಕಿಂಗ್ ಮೂಲಕ ಅಥವಾ ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಶಾಖೆಯಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ.',
    applyHi: 'इंटरनेट बैंकिंग या अपनी बैंक शाखा के माध्यम से नामांकित करें।',
  },
  {
    nameEn: 'Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY)',
    nameKn: 'ಪ್ರಧಾನ ಮಂತ್ರಿ ಜೀವನ ಜ್ಯೋತಿ ಬಿಮಾ ಯೋಜನೆ (PMJJBY)',
    nameHi: 'प्रधानमंत्री जीवन ज्योति बीमा योजना (पीएमजेजेबीवाई)',
    categoryEn: 'Insurance',
    categoryKn: 'ಬೀಮಾ',
    categoryHi: 'बीमा',
    descEn:
      'Renewable 1-year term life insurance scheme providing ₹2 Lakh life cover for death due to any cause at a premium of ₹436 per annum.',
    descKn:
      'ವರ್ಷಕ್ಕೆ ₹436 ಪ್ರೀಮಿಯಂನಲ್ಲಿ ಯಾವುದೇ ಕಾರಣದಿಂದ ಸಂಭವಿಸುವ ಮರಣಕ್ಕೆ ₹2 ಲಕ್ಷ ಜೀವ ವಿಮಾ ರಕ್ಷಣೆ ನೀಡುವ ಸರ್ಕಾರಿ ಯೋಜನೆ.',
    descHi:
      '₹436 प्रति वर्ष के प्रीमियम पर किसी भी कारण से मृत्यु होने पर ₹2 लाख का जीवन बीमा कवर।',
    eligibilityEn: 'Savings bank account holders aged between 18 and 50 years.',
    eligibilityKn: 'ಉಳಿತಾಯ ಬ್ಯಾಂಕ್ ಖಾತೆ ಹೊಂದಿರುವ 18 ರಿಂದ 50 ವರ್ಷ ವಯಸ್ಸಿನ ವ್ಯಕ್ತಿಗಳು.',
    eligibilityHi: '18 से 50 वर्ष की आयु के सभी बचत बैंक खाताधारक।',
    documentsEn: 'Aadhaar Card, Bank account details, Self-declaration of good health.',
    documentsKn: 'ಆಧಾರ್ ಕಾರ್ಡ್, ಬ್ಯಾಂಕ್ ಖಾತೆ ವಿವರ ಮತ್ತು ಆರೋಗ್ಯದ ಸ್ವಯಂ ಘೋಷಣೆ ಫಾರ್ಮ್.',
    documentsHi: 'आधार कार्ड, बैंक खाता विवरण, अच्छे स्वास्थ्य की स्व-घोषणा।',
    applyEn: 'Subscribe through net banking or submit form at your bank branch.',
    applyKn: 'ನೆಟ್ ಬ್ಯಾಂಕಿಂಗ್ ಅಥವಾ ಬ್ಯಾಂಕ್ ಶಾಖೆಗೆ ಭೇಟಿ ನೀಡಿ ಫಾರ್ಮ್ ತುಂಬಿ ಕೊಡಿ.',
    applyHi: 'नेट बैंकिंग या बैंक शाखा में फॉर्म जमा करके सदस्य बनें।',
  },
  {
    nameEn: 'Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)',
    nameKn: 'ಪ್ರಧಾನ ಮಂತ್ರಿ ಕಿಸಾನ್ ಸಮ್ಮಾನ್ ನಿಧಿ (PM-KISAN)',
    nameHi: 'प्रधानमंत्री किसान सम्मान निधि (पीएम-किसान)',
    categoryEn: 'Agriculture',
    categoryKn: 'ಕೃಷಿ',
    categoryHi: 'कृषि',
    descEn:
      'Income support scheme providing ₹6,000 per year in 3 equal installments of ₹2,000 directly into the bank accounts of landholding farmer families.',
    descKn:
      'ಅರ್ಹ ರೈತ ಕುಟುಂಬಗಳಿಗೆ ವರ್ಷಕ್ಕೆ ₹6,000 ನೇರ ಹಣಕಾಸಿನ ನೆರವನ್ನು 3 ಕಂತುಗಳಲ್ಲಿ (₹2,000 ಪ್ರತಿಕಂತು) ಬ್ಯಾಂಕ್ ಖಾತೆಗೆ ಜಮಾ ಮಾಡುವ ಯೋಜನೆ.',
    descHi:
      'भूमिधारक किसान परिवारों को ₹6,000 प्रति वर्ष की आय सहायता, ₹2,000 की तीन समान किस्तों में सीधे बैंक खाते में।',
    eligibilityEn: 'All landholding farmer families with cultivable land holdings in their name.',
    eligibilityKn: 'ಸಾಗು ಭೂಮಿ ಹೊಂದಿರುವ ಎಲ್ಲಾ ರೈತ ಕುಟುಂಬಗಳು.',
    eligibilityHi: 'अपनी भूमि रखने वाले सभी किसान परिवार।',
    documentsEn: 'Aadhaar Card, Land ownership papers (RTC/Pahani), Aadhaar-seeded bank account.',
    documentsKn: 'ಆಧಾರ್ ಕಾರ್ಡ್, ಜಮೀನಿನ ಪಹಣಿ (RTC) ದಾಖಲೆ ಮತ್ತು ಆಧಾರ್ ಲಿಂಕ್ ಆಗಿರುವ ಬ್ಯಾಂಕ್ ಖಾತೆ.',
    documentsHi: 'आधार कार्ड, भूमि के दस्तावेज (खसरा/खतौनी), आधार-लिंक्ड बैंक खाता।',
    applyEn: 'Register on official PM-Kisan portal (pmkisan.gov.in) or visit nearest CSC center.',
    applyKn:
      'ಅಧಿಕೃತ pmkisan.gov.in ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ಅಥವಾ ಹತ್ತಿರದ ಗ್ರಾಮ ಒನ್/CSC ಕೇಂದ್ರದಲ್ಲಿ ನೋಂದಾಯಿಸಿ.',
    applyHi: 'pmkisan.gov.in पर या नजदीकी जन सेवा केंद्र (CSC) में पंजीकरण करें।',
  },
  {
    nameEn: 'Pradhan Mantri MUDRA Yojana (PMMY)',
    nameKn: 'ಪ್ರಧಾನ ಮಂತ್ರಿ ಮುದ್ರಾ ಯೋಜನೆ (PMMY)',
    nameHi: 'प्रधानमंत्री मुद्रा योजना (पीएमएमवाई)',
    categoryEn: 'Loans',
    categoryKn: 'ಸಾಲಗಳು',
    categoryHi: 'ऋण',
    descEn:
      'Micro-business loan scheme offering collateral-free loans up to ₹20 Lakh under Shishu (up to ₹50k), Kishore (up to ₹5 Lakh), and Tarun (up to ₹20 Lakh) categories.',
    descKn:
      'ಸಣ್ಣ ಮತ್ತು ಅತಿ ಸಣ್ಣ ಉದ್ಯಮಿಗಳಿಗೆ ಶೂನ್ಯ ಗ್ಯಾರಂಟಿಯಲ್ಲಿ ₹20 ಲಕ್ಷದವರೆಗೆ ಶಿಶು, ಕಿಶೋರ ಮತ್ತು ತರುಣ್ ಹಂತಗಳಲ್ಲಿ ಸಾಲ ನೀಡುವ ಯೋಜನೆ.',
    descHi:
      'सूक्ष्म व्यवसायों के लिए बिना गारंटी के शिशु, किशोर और तरुण श्रेणियों के तहत ₹20 लाख तक का ऋण।',
    eligibilityEn: 'Non-corporate, non-farm small/micro-enterprises and self-employed individuals.',
    eligibilityKn: 'ಸಣ್ಣ ವ್ಯಾಪಾರಿಗಳು, ಸ್ವಯಂ ಉದ್ಯೋಗಿಗಳು ಮತ್ತು ಕೃಷಿಯೇತರ ಸಣ್ಣ ಉದ್ಯಮಗಳು.',
    eligibilityHi: 'गैर-कॉर्पोरेट, गैर-कृषि सूक्ष्म और लघु व्यवसाय।',
    documentsEn:
      'Identity proof, Residence proof, Business plan/proposal, Bank statements for last 6 months.',
    documentsKn: 'ಗುರುತಿನ ಚೀಟಿ, ವಿಳಾಸದ ಸಾಕ್ಷಿ, ಉದ್ಯಮದ ಮಾಹಿತಿ ಯೋಜನೆ ಮತ್ತು ಬ್ಯಾಂಕ್ ಸ್ಟೇಟ್‌ಮೆಂಟ್.',
    documentsHi: 'पहचान पत्र, निवास प्रमाण पत्र, व्यवसाय योजना, पिछले 6 महीने का बैंक विवरण।',
    applyEn:
      'Apply online at udyamimitra.in portal or visit any public/private sector bank branch.',
    applyKn: 'udyamimitra.in ವೆಬ್‌ಸೈಟ್‌ನಲ್ಲಿ ಅಥವಾ ಬ್ಯಾಂಕ್ ಶಾಖೆಯಲ್ಲಿ ನೇರವಾಗಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ.',
    applyHi: 'udyamimitra.in पोर्टल पर या किसी भी बैंक शाखा में आवेदन करें।',
  },
];

interface EscalationTicket {
  id: number;
  reference_id: string;
  caller_name?: string;
  situation: string;
  what_happened: string;
  urgency: string;
  status?: string;
  created_at: string;
  follow_up_method: string;
  contact_details: string;
  language: string;
  checked_facts?: Record<string, unknown>;
}

export const WelcomeView = ({
  onStartCall,
  isCallEnded = false,
  onRestartCall,
  micError = false,
  onDismissMicError,
  currentTab = 'home',
  onTabChange,
  ref,
  callDuration = null,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [activeFraudIdx, setActiveFraudIdx] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [textSize, setTextSize] = useState<'normal' | 'large'>('normal');
  const [selectedLanguage, setSelectedLanguage] = useState('English');

  // Call stats states
  const [stats, setStats] = useState<{ total: number; successful: number; failed: number } | null>(null);
  const [loadingStats, setLoadingStats] = useState(false);

  const fetchStats = async () => {
    setLoadingStats(true);
    try {
      const res = await fetch('/api/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Error fetching call stats:', err);
    } finally {
      setLoadingStats(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  // Complaint Wizard States
  const [complaintStep, setComplaintStep] = useState(1);
  const [selectedComplaintType, setSelectedComplaintType] = useState('');

  // Escalations States
  const [escalations, setEscalations] = useState<EscalationTicket[]>([]);
  const [loadingEscalations, setLoadingEscalations] = useState(false);
  const [statusFilter, setStatusFilter] = useState<'all' | 'open' | 'in progress' | 'resolved'>(
    'all'
  );

  useEffect(() => {
    if (currentTab === 'escalations') {
      setLoadingEscalations(true);
      fetch('/api/escalations')
        .then((res) => res.json())
        .then((data) => {
          if (Array.isArray(data)) {
            setEscalations(data);
          }
          setLoadingEscalations(false);
        })
        .catch((err) => {
          console.error('Error fetching escalations:', err);
          setLoadingEscalations(false);
        });
    }
  }, [currentTab]);

  // Load Google Translate Widget dynamically on mount
  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (document.getElementById('google-translate-script')) return;

    (window as any).googleTranslateElementInit = () => {
      new (window as any).google.translate.TranslateElement(
        {
          pageLanguage: 'en',
          includedLanguages: 'en,kn,hi,te,ta,mr,bn,gu,ml,pa,ur',
          layout: (window as any).google.translate.TranslateElement.InlineLayout.SIMPLE,
          autoDisplay: false,
        },
        'google_translate_element'
      );
    };

    const addScript = document.createElement('script');
    addScript.id = 'google-translate-script';
    addScript.src = '//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
    document.body.appendChild(addScript);
  }, []);

  const handlePrevFraud = () => {
    setActiveFraudIdx((prev) => (prev - 1 + FRAUD_TYPES.length) % FRAUD_TYPES.length);
  };

  const handleNextFraud = () => {
    setActiveFraudIdx((prev) => (prev + 1) % FRAUD_TYPES.length);
  };

  // Determine active translation dictionary
  const isKannada = selectedLanguage === 'Kannada (ಕನ್ನಡ)';
  const isHindi = selectedLanguage === 'Hindi (ಹಿन्दी)';
  const t = isKannada
    ? TRANSLATIONS['Kannada (ಕನ್ನಡ)']
    : isHindi
      ? TRANSLATIONS['Hindi (ಹಿन्दी)']
      : TRANSLATIONS['English'];

  // Formatter for dynamic call duration display
  const formatDuration = (secondsTotal: number | null) => {
    if (secondsTotal === null || secondsTotal === undefined) return '';
    const mins = Math.floor(secondsTotal / 60);
    const secs = secondsTotal % 60;

    if (mins > 0) {
      return `${mins} ${t.minutesLabel} ${secs} ${t.secondsLabel}`;
    }
    return `${secs} ${t.secondsLabel}`;
  };

  // Filter schemes based on search query and category
  const filteredSchemes = SCHEMES_DATA.filter((scheme) => {
    const name = isKannada ? scheme.nameKn : isHindi ? scheme.nameHi : scheme.nameEn;
    const desc = isKannada ? scheme.descKn : isHindi ? scheme.descHi : scheme.descEn;
    const category = isKannada
      ? scheme.categoryKn
      : isHindi
        ? scheme.categoryHi
        : scheme.categoryEn;

    const matchesSearch =
      name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      desc.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory =
      selectedCategory === 'All' ||
      category === selectedCategory ||
      (selectedCategory === 'Agriculture' && (category === 'ಕೃಷಿ' || category === 'कृषि')) ||
      (selectedCategory === 'Banking' && (category === 'ಬ್ಯಾಂಕಿಂಗ್' || category === 'बैंकिंग')) ||
      (selectedCategory === 'Insurance' && (category === 'ಬೀಮಾ' || category === 'बीमा')) ||
      (selectedCategory === 'Pension' && (category === 'ಪಿಂಚಣಿ' || category === 'पेंशन')) ||
      (selectedCategory === 'Loans' && (category === 'ಸಾಲಗಳು' || category === 'ऋण'));
    return matchesSearch && matchesCategory;
  });

  const categories = ['All', 'Agriculture', 'Banking', 'Insurance', 'Pension', 'Loans'];

  if (micError) {
    return (
      <div
        ref={ref}
        className="relative flex min-h-screen w-full flex-col bg-slate-950 font-sans text-slate-100"
      >
        <div className="h-1.5 w-full shrink-0 bg-gradient-to-r from-[#FF9933] via-amber-300 via-white to-[#10B981]" />

        <div className="flex items-center justify-between border-b border-slate-800 bg-slate-900/90 px-4 py-3 backdrop-blur-md">
          <span className="bg-gradient-to-r from-amber-400 to-emerald-400 bg-clip-text font-bold text-transparent">
            {t.platformTitle}
          </span>
          <div
            id="google_translate_element"
            className="overflow-hidden rounded border border-slate-700 bg-slate-900 text-xs shadow-inner"
          />
        </div>

        <div className="flex flex-1 items-center justify-center p-4">
          <div className="w-full max-w-xl rounded-2xl border border-rose-500/40 bg-slate-900/90 p-8 text-left shadow-2xl backdrop-blur-xl">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-rose-500/30 bg-rose-500/20 text-rose-400">
              <ShieldAlert className="h-6 w-6" />
            </div>

            <h2 className="mb-2 text-xl font-bold text-white">{t.micBlockedTitle}</h2>
            <p className="mb-6 text-sm leading-relaxed text-slate-300">{t.micBlockedDesc}</p>

            <div className="flex gap-4">
              {onDismissMicError && (
                <Button
                  variant="outline"
                  onClick={onDismissMicError}
                  className="border-slate-700 px-6 text-slate-300 hover:bg-slate-800 hover:text-white"
                >
                  {t.btnCancel}
                </Button>
              )}
              <Button
                onClick={() => window.location.reload()}
                className="border-0 bg-gradient-to-r from-emerald-600 to-teal-600 px-6 font-bold text-white shadow-lg shadow-emerald-900/40 hover:from-emerald-500 hover:to-teal-500"
              >
                {t.btnReload}
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (isCallEnded) {
    return (
      <div
        ref={ref}
        className="relative flex min-h-screen w-full flex-col bg-slate-950 font-sans text-slate-100"
      >
        <div className="h-1.5 w-full shrink-0 bg-gradient-to-r from-[#FF9933] via-amber-300 via-white to-[#10B981]" />

        <div className="flex items-center justify-between border-b border-slate-800 bg-slate-900/90 px-4 py-3 backdrop-blur-md">
          <span className="bg-gradient-to-r from-amber-400 to-emerald-400 bg-clip-text font-bold text-transparent">
            {t.platformTitle}
          </span>
          <div
            id="google_translate_element"
            className="overflow-hidden rounded border border-slate-700 bg-slate-900 text-xs shadow-inner"
          />
        </div>

        <div className="flex flex-1 items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-2xl border border-indigo-500/40 bg-slate-900/90 p-8 text-left shadow-2xl backdrop-blur-xl">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-emerald-500/30 bg-emerald-500/20 text-emerald-400">
              <CheckCircle className="h-6 w-6" />
            </div>

            <h2 className="mb-2 text-xl font-bold text-white">{t.callCompletedTitle}</h2>
            <p className="mb-4 text-sm leading-relaxed text-slate-300">{t.callCompletedDesc}</p>

            {callDuration !== null && (
              <div className="mb-6 flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-950/80 p-3.5 text-xs font-bold text-slate-300">
                <span>⏱️</span>
                <span>
                  {t.callDurationLabel}{' '}
                  <strong className="text-amber-400">{formatDuration(callDuration)}</strong>
                </span>
              </div>
            )}

            <div className="flex flex-col gap-3">
              <Button
                onClick={onRestartCall}
                className="border-0 bg-gradient-to-r from-emerald-600 to-teal-600 py-3.5 font-bold text-white shadow-lg shadow-emerald-900/40 hover:from-emerald-500 hover:to-teal-500"
              >
                {t.btnStartNew}
              </Button>
              <button
                onClick={() => window.location.reload()}
                className="mt-1 text-xs font-semibold text-slate-400 transition-colors hover:text-amber-400 hover:underline"
              >
                {t.btnReturnHome}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const fraudTitle = isKannada
    ? FRAUD_TYPES[activeFraudIdx].titleKn
    : isHindi
      ? FRAUD_TYPES[activeFraudIdx].titleHi
      : FRAUD_TYPES[activeFraudIdx].titleEn;
  const fraudDesc = isKannada
    ? FRAUD_TYPES[activeFraudIdx].descKn
    : isHindi
      ? FRAUD_TYPES[activeFraudIdx].descHi
      : FRAUD_TYPES[activeFraudIdx].descEn;
  const fraudPrev = isKannada
    ? FRAUD_TYPES[activeFraudIdx].prevKn
    : isHindi
      ? FRAUD_TYPES[activeFraudIdx].prevHi
      : FRAUD_TYPES[activeFraudIdx].prevEn;

  return (
    <div
      ref={ref}
      className={`relative flex min-h-screen w-full flex-col overflow-x-hidden bg-slate-950 font-sans text-slate-100 ${textSize === 'large' ? 'text-lg' : 'text-sm'}`}
    >
      {/* Background Subtle Ambient Glow Circles */}
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(120,119,198,0.15),rgba(255,255,255,0))]" />
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_80%_80%,rgba(16,185,129,0.06),transparent)]" />

      {/* Top Banner Ribbon */}
      <div className="h-1.5 w-full shrink-0 bg-gradient-to-r from-[#FF9933] via-amber-300 via-white to-[#10B981] shadow-md" />

      {/* Main Header Logo Strip */}
      <div className="relative z-20 shrink-0 border-b border-slate-800/80 bg-slate-900/90 px-4 py-4 shadow-lg backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-4">
            <div className="flex h-10 w-10 shrink-0 flex-col items-center justify-center overflow-hidden rounded-lg border border-slate-700 shadow-md">
              <div className="h-1/3 w-full bg-[#FF9933]" />
              <div className="flex h-1/3 w-full items-center justify-center bg-white">
                <span className="text-[6px] font-extrabold text-blue-900">☸</span>
              </div>
              <div className="h-1/3 w-full bg-[#10B981]" />
            </div>
            <div className="text-left">
              <h1 className="flex items-center gap-2 bg-gradient-to-r from-amber-400 via-slate-100 to-emerald-400 bg-clip-text text-xl font-extrabold tracking-tight text-transparent">
                {t.platformTitle}
                <span className="rounded-full border border-indigo-500/30 bg-indigo-500/20 px-2 py-0.5 text-[10px] font-bold tracking-widest text-indigo-300 uppercase">
                  AI Voice
                </span>
              </h1>
              <p className="text-xs font-extrabold tracking-wider text-amber-400/90 uppercase">
                {t.platformSubtitle}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Language Selector Toggle */}
            <div className="flex overflow-hidden rounded-xl border border-slate-700/80 bg-slate-900 p-0.5 text-xs font-bold shadow-inner">
              <button
                onClick={() => setSelectedLanguage('English')}
                className={`rounded-lg px-3.5 py-1.5 transition-all ${selectedLanguage === 'English' ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 font-extrabold text-white shadow-md' : 'text-slate-400 hover:bg-slate-800/60 hover:text-white'}`}
              >
                English
              </button>
              <button
                onClick={() => setSelectedLanguage('Kannada (ಕನ್ನಡ)')}
                className={`rounded-lg px-3.5 py-1.5 transition-all ${selectedLanguage === 'Kannada (ಕನ್ನಡ)' ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 font-extrabold text-white shadow-md' : 'text-slate-400 hover:bg-slate-800/60 hover:text-white'}`}
              >
                ಕನ್ನಡ
              </button>
              <button
                onClick={() => setSelectedLanguage('Hindi (ಹಿन्दी)')}
                className={`rounded-lg px-3.5 py-1.5 transition-all ${selectedLanguage === 'Hindi (ಹಿन्दी)' ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 font-extrabold text-white shadow-md' : 'text-slate-400 hover:bg-slate-800/60 hover:text-white'}`}
              >
                ಹಿन्दी
              </button>
            </div>

            {/* Accessibility Font Sizers */}
            <div className="flex overflow-hidden rounded-lg border border-slate-700 bg-slate-900 p-0.5">
              <button
                onClick={() => setTextSize('normal')}
                className={`rounded px-2.5 py-1 text-xs font-bold ${textSize === 'normal' ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white'}`}
              >
                A
              </button>
              <button
                onClick={() => setTextSize('large')}
                className={`rounded px-2.5 py-1 text-xs font-bold ${textSize === 'large' ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white'}`}
              >
                A+
              </button>
            </div>

            {/* Google Translate Target Container */}
            <div
              id="google_translate_element"
              className="overflow-hidden rounded-lg border border-slate-700 bg-slate-900 text-xs shadow-inner"
            />
          </div>
        </div>
      </div>

      {/* Solid Navy Navigation Bar */}
      <nav className="relative z-20 shrink-0 border-b border-slate-800/90 bg-slate-900/95 text-slate-200 shadow-xl backdrop-blur-lg">
        <div className="mx-auto flex max-w-7xl overflow-x-auto px-4">
          <button
            onClick={() => onTabChange?.('home')}
            className={`shrink-0 border-b-4 px-5 py-4 text-xs font-bold tracking-wider uppercase transition-all hover:bg-slate-800/60 ${currentTab === 'home' ? 'border-amber-400 bg-amber-500/10 text-amber-300 shadow-[0_0_20px_rgba(245,158,11,0.2)]' : 'border-transparent text-slate-400'}`}
          >
            {t.navHome}
          </button>
          <button
            onClick={() => onTabChange?.('schemes')}
            className={`shrink-0 border-b-4 px-5 py-4 text-xs font-bold tracking-wider uppercase transition-all hover:bg-slate-800/60 ${currentTab === 'schemes' ? 'border-amber-400 bg-amber-500/10 text-amber-300 shadow-[0_0_20px_rgba(245,158,11,0.2)]' : 'border-transparent text-slate-400'}`}
          >
            {t.navSchemes}
          </button>
          <button
            onClick={() => onTabChange?.('fraud')}
            className={`shrink-0 border-b-4 px-5 py-4 text-xs font-bold tracking-wider uppercase transition-all hover:bg-slate-800/60 ${currentTab === 'fraud' ? 'border-amber-400 bg-amber-500/10 text-amber-300 shadow-[0_0_20px_rgba(245,158,11,0.2)]' : 'border-transparent text-slate-400'}`}
          >
            {t.navFraud}
          </button>
          <button
            onClick={() => onTabChange?.('complaint')}
            className={`shrink-0 border-b-4 px-5 py-4 text-xs font-bold tracking-wider uppercase transition-all hover:bg-slate-800/60 ${currentTab === 'complaint' ? 'border-amber-400 bg-amber-500/10 text-amber-300 shadow-[0_0_20px_rgba(245,158,11,0.2)]' : 'border-transparent text-slate-400'}`}
          >
            {t.navComplaint}
          </button>
          <button
            onClick={() => onTabChange?.('escalations')}
            className={`shrink-0 border-b-4 px-5 py-4 text-xs font-bold tracking-wider uppercase transition-all hover:bg-slate-800/60 ${currentTab === 'escalations' ? 'border-amber-400 bg-amber-500/10 text-amber-300 shadow-[0_0_20px_rgba(245,158,11,0.2)]' : 'border-transparent text-slate-400'}`}
          >
            {t.navEscalations}
          </button>
        </div>
      </nav>

      {/* Main Container */}
      <main className="relative z-10 mx-auto w-full max-w-7xl flex-1 px-4 py-8">
        {currentTab === 'home' && (
          <div className="space-y-8">
            {/* HERO BANNER WITH INTERACTIVE DIAL ACTIVATOR */}
            <section className="relative flex flex-col items-center justify-between gap-8 overflow-hidden rounded-2xl border border-indigo-900/50 bg-gradient-to-br from-slate-900/95 via-indigo-950/40 to-slate-900/95 p-6 shadow-2xl backdrop-blur-xl sm:p-10 lg:flex-row">
              <div className="absolute top-0 bottom-0 left-0 w-2 bg-gradient-to-b from-amber-400 via-amber-500 to-emerald-500" />

              <div className="max-w-2xl space-y-5 text-left">
                <div className="inline-flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-extrabold text-amber-300">
                  <Sparkles className="h-3.5 w-3.5 text-amber-400" /> Powered by Sita AI Voice
                  Pipeline
                </div>

                <h2 className="text-2xl leading-tight font-extrabold tracking-tight text-white sm:text-4xl">
                  {t.heroTitle}
                </h2>
                <p className="text-sm leading-relaxed font-normal text-slate-300 sm:text-base">
                  {t.heroDesc}
                </p>
                <div className="flex flex-wrap gap-2 text-xs font-semibold">
                  <span className="rounded-full border border-slate-700/80 bg-slate-800/80 px-3.5 py-1.5 text-slate-300">
                    {t.badgeSecure}
                  </span>
                  <span className="rounded-full border border-slate-700/80 bg-slate-800/80 px-3.5 py-1.5 text-slate-300">
                    {t.badgeVerified}
                  </span>
                  <span className="rounded-full border border-slate-700/80 bg-slate-800/80 px-3.5 py-1.5 text-slate-300">
                    {t.badgeDirect}
                  </span>
                </div>
              </div>

              {/* Centered Circular Activator Dial */}
              <div className="flex w-full shrink-0 items-center justify-center lg:w-auto">
                <div
                  onClick={onStartCall}
                  className="group relative flex h-48 w-48 cursor-pointer flex-col items-center justify-center rounded-full"
                >
                  <div
                    className="absolute h-full w-full animate-spin rounded-full border-2 border-dashed border-emerald-500/30"
                    style={{ animationDuration: '45s' }}
                  />
                  <div className="absolute h-36 w-36 animate-pulse rounded-full bg-emerald-500/20 blur-xl" />

                  <div className="flex h-24 w-24 items-center justify-center rounded-full border-2 border-emerald-300/30 bg-gradient-to-tr from-emerald-600 via-teal-500 to-emerald-400 shadow-[0_0_30px_rgba(16,185,129,0.4)] transition-all duration-300 group-hover:scale-105 hover:from-emerald-500 hover:to-teal-400">
                    <Mic className="h-10 w-10 text-white" />
                  </div>

                  <span className="mt-3 animate-pulse text-[10px] font-extrabold tracking-wider text-emerald-400 uppercase">
                    {t.startCallLabel}
                  </span>
                </div>
              </div>
            </section>

            {/* Call Performance Dashboard */}
            <section className="relative rounded-2xl border border-slate-800 bg-slate-900/40 p-6 shadow-xl backdrop-blur-md text-left">
              <div className="mb-6 flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <span className="text-xl">📊</span>
                  <h3 className="text-lg font-bold text-slate-100">
                    Sita AI — Live Call Metrics
                  </h3>
                </div>
                <button
                  onClick={fetchStats}
                  disabled={loadingStats}
                  className={`flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-bold text-slate-350 transition-all hover:bg-slate-800 hover:text-white ${loadingStats ? 'opacity-50' : ''}`}
                >
                  <span className={`inline-block ${loadingStats ? 'animate-spin' : ''}`}>🔄</span>
                  {loadingStats ? 'Syncing...' : 'Refresh Stats'}
                </button>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                {/* Total Calls Card */}
                <div className="group relative overflow-hidden rounded-xl border border-slate-800 bg-slate-950/80 p-5 transition-all duration-300 hover:-translate-y-0.5 hover:border-amber-500/30 hover:shadow-[0_0_15px_rgba(245,158,11,0.08)]">
                  <div className="absolute top-0 right-0 h-24 w-24 translate-x-8 -translate-y-8 rounded-full bg-amber-500/5 blur-xl group-hover:bg-amber-500/10" />
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-amber-500/20 bg-amber-500/5 text-lg font-bold text-amber-400">
                      📞
                    </div>
                    <div>
                      <p className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
                        Total Calls Logged
                      </p>
                      {loadingStats ? (
                        <div className="h-7 w-12 animate-pulse rounded bg-slate-800 mt-1" />
                      ) : (
                        <h4 className="text-2xl font-extrabold text-amber-400 mt-0.5">
                          {stats?.total ?? 0}
                        </h4>
                      )}
                    </div>
                  </div>
                </div>

                {/* Successful Calls Card */}
                <div className="group relative overflow-hidden rounded-xl border border-slate-800 bg-slate-950/80 p-5 transition-all duration-300 hover:-translate-y-0.5 hover:border-emerald-500/30 hover:shadow-[0_0_15px_rgba(16,185,129,0.08)]">
                  <div className="absolute top-0 right-0 h-24 w-24 translate-x-8 -translate-y-8 rounded-full bg-emerald-500/5 blur-xl group-hover:bg-emerald-500/10" />
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-emerald-500/20 bg-emerald-500/5 text-lg font-bold text-emerald-400">
                      ✅
                    </div>
                    <div>
                      <p className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
                        Successful Calls
                      </p>
                      {loadingStats ? (
                        <div className="h-7 w-12 animate-pulse rounded bg-slate-800 mt-1" />
                      ) : (
                        <h4 className="text-2xl font-extrabold text-emerald-400 mt-0.5">
                          {stats?.successful ?? 0}
                        </h4>
                      )}
                    </div>
                  </div>
                </div>

                {/* Failed Calls Card */}
                <div className="group relative overflow-hidden rounded-xl border border-slate-800 bg-slate-950/80 p-5 transition-all duration-300 hover:-translate-y-0.5 hover:border-rose-500/30 hover:shadow-[0_0_15px_rgba(244,63,94,0.08)]">
                  <div className="absolute top-0 right-0 h-24 w-24 translate-x-8 -translate-y-8 rounded-full bg-rose-500/5 blur-xl group-hover:bg-rose-500/10" />
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-rose-500/20 bg-rose-500/5 text-lg font-bold text-rose-400">
                      ⚠️
                    </div>
                    <div>
                      <p className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
                        Failed Calls
                      </p>
                      {loadingStats ? (
                        <div className="h-7 w-12 animate-pulse rounded bg-slate-800 mt-1" />
                      ) : (
                        <h4 className="text-2xl font-extrabold text-rose-400 mt-0.5">
                          {stats?.failed ?? 0}
                        </h4>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Quick Cards Grid */}
            <section className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
              <div
                onClick={() => onTabChange?.('schemes')}
                className="group cursor-pointer space-y-4 rounded-xl border border-slate-800 bg-slate-900/80 p-5 text-left backdrop-blur-md transition-all duration-300 hover:-translate-y-1.5 hover:border-amber-500/50 hover:shadow-[0_0_25px_rgba(245,158,11,0.15)]"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-lg border border-amber-500/30 bg-amber-500/10 text-xl font-bold text-amber-400 transition-transform group-hover:scale-110">
                  🏛️
                </div>
                <h3 className="text-base font-bold text-white">{t.cardSchemesTitle}</h3>
                <p className="text-xs leading-relaxed font-normal text-slate-400">
                  {t.cardSchemesDesc}
                </p>
              </div>

              <div
                onClick={() => onTabChange?.('fraud')}
                className="group cursor-pointer space-y-4 rounded-xl border border-slate-800 bg-slate-900/80 p-5 text-left backdrop-blur-md transition-all duration-300 hover:-translate-y-1.5 hover:border-rose-500/50 hover:shadow-[0_0_25px_rgba(244,63,94,0.15)]"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-lg border border-rose-500/30 bg-rose-500/10 text-xl font-bold text-rose-400 transition-transform group-hover:scale-110">
                  🚨
                </div>
                <h3 className="text-base font-bold text-white">{t.cardFraudTitle}</h3>
                <p className="text-xs leading-relaxed font-normal text-slate-400">
                  {t.cardFraudDesc}
                </p>
              </div>

              <div className="group space-y-4 rounded-xl border border-slate-800 bg-slate-900/80 p-5 text-left backdrop-blur-md transition-all duration-300 hover:-translate-y-1.5 hover:border-emerald-500/50 hover:shadow-[0_0_25px_rgba(16,185,129,0.15)]">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-xl font-bold text-emerald-400 transition-transform group-hover:scale-110">
                  💰
                </div>
                <h3 className="text-base font-bold text-white">{t.cardFinancialTitle}</h3>
                <p className="text-xs leading-relaxed font-normal text-slate-400">
                  {t.cardFinancialDesc}
                </p>
              </div>

              <div
                onClick={() => onTabChange?.('complaint')}
                className="group cursor-pointer space-y-4 rounded-xl border border-slate-800 bg-slate-900/80 p-5 text-left backdrop-blur-md transition-all duration-300 hover:-translate-y-1.5 hover:border-indigo-500/50 hover:shadow-[0_0_25px_rgba(99,102,241,0.15)]"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-lg border border-indigo-500/30 bg-indigo-500/10 text-xl font-bold text-indigo-400 transition-transform group-hover:scale-110">
                  📞
                </div>
                <h3 className="text-base font-bold text-white">{t.cardComplaintTitle}</h3>
                <p className="text-xs leading-relaxed font-normal text-slate-400">
                  {t.cardComplaintDesc}
                </p>
              </div>
            </section>

            {/* Slider Warning Banner */}
            <section className="relative rounded-xl border border-rose-900/40 bg-gradient-to-r from-rose-950/30 via-slate-900/90 to-amber-950/30 p-6 text-left shadow-xl backdrop-blur-md">
              <div className="mb-4 flex items-center justify-between border-b border-slate-800/80 pb-3">
                <h3 className="flex items-center gap-2 text-base font-bold text-amber-400">
                  <span>🚨</span> {t.warningTitle}
                </h3>
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={handlePrevFraud}
                    className="rounded-lg border border-slate-700 bg-slate-800 p-1.5 text-slate-300 transition-colors hover:bg-slate-700"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  <button
                    onClick={handleNextFraud}
                    className="rounded-lg border border-slate-700 bg-slate-800 p-1.5 text-slate-300 transition-colors hover:bg-slate-700"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <div className="min-h-24">
                <h4 className="mb-1.5 text-sm font-bold text-white">{fraudTitle}</h4>
                <p className="mb-4 text-xs leading-relaxed font-normal text-slate-300">
                  {fraudDesc}
                </p>
                <div className="flex items-start gap-2 rounded-lg border border-rose-800/60 bg-rose-950/50 p-3 text-xs font-bold text-rose-200">
                  <span className="shrink-0">{t.warningFooter}</span>
                  <span>{fraudPrev}</span>
                </div>
              </div>
            </section>
          </div>
        )}

        {/* TAB: SCHEMES DIRECTORY */}
        {currentTab === 'schemes' && (
          <div className="space-y-6">
            <div className="flex flex-col items-start justify-between gap-4 border-b border-slate-800 pb-4 md:flex-row md:items-center">
              <h2 className="text-xl font-bold text-amber-400">{t.schemeSearchTitle}</h2>
              <Button
                onClick={onStartCall}
                className="flex items-center gap-2 rounded-lg border-0 bg-gradient-to-r from-emerald-600 to-teal-600 font-bold text-white shadow-lg shadow-emerald-950 hover:from-emerald-500 hover:to-teal-500"
              >
                <Mic className="h-4 w-4 animate-bounce" /> {t.btnStart}
              </Button>
            </div>

            {/* Filters */}
            <div className="flex flex-col items-center justify-between gap-4 rounded-xl border border-slate-800 bg-slate-900/90 p-4 shadow-lg backdrop-blur-md md:flex-row">
              <div className="relative w-full md:max-w-md">
                <Search className="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-slate-500" />
                <input
                  type="text"
                  placeholder={t.schemePlaceholder}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 py-2 pr-4 pl-9 text-xs font-medium text-white placeholder-slate-500 focus:border-amber-400 focus:outline-none"
                />
              </div>

              <div className="flex w-full flex-wrap gap-1.5 md:w-auto">
                {categories.map((cat) => {
                  const catLabel = isKannada
                    ? cat === 'Agriculture'
                      ? 'ಕೃಷಿ'
                      : cat === 'Banking'
                        ? 'ಬ್ಯಾಂಕಿಂಗ್'
                        : cat === 'Insurance'
                          ? 'ಬೀಮಾ'
                          : cat === 'Pension'
                            ? 'ಪಿಂಚಣಿ'
                            : cat === 'Loans'
                              ? 'ಸಾಲಗಳು'
                              : 'ಎಲ್ಲವೂ'
                    : isHindi
                      ? cat === 'Agriculture'
                        ? 'कृषि'
                        : cat === 'Banking'
                          ? 'बैंकिंग'
                          : cat === 'Insurance'
                            ? 'बीमा'
                            : cat === 'Pension'
                              ? 'पेंशन'
                              : cat === 'Loans'
                                ? 'ऋण'
                                : 'सभी'
                      : cat;

                  return (
                    <button
                      key={cat}
                      onClick={() => setSelectedCategory(cat)}
                      className={`rounded-lg border px-3 py-1.5 text-xs font-bold transition-colors ${
                        selectedCategory === cat
                          ? 'border-amber-500/60 bg-amber-500/20 text-amber-300 shadow-md'
                          : 'border-slate-800 bg-slate-950 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                      }`}
                    >
                      {catLabel}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Scheme Cards */}
            {filteredSchemes.length > 0 ? (
              filteredSchemes.map((scheme, idx) => (
                <div
                  key={idx}
                  className="relative overflow-hidden rounded-xl border border-slate-800 bg-slate-900/80 p-6 text-left shadow-xl backdrop-blur-md transition-all duration-300 hover:-translate-y-1 hover:border-slate-700"
                >
                  <div className="absolute top-0 bottom-0 left-0 w-1.5 bg-gradient-to-b from-amber-400 to-emerald-500" />

                  <div className="mb-3 flex items-center justify-between gap-3">
                    <h3 className="text-lg font-bold text-white">
                      {isKannada ? scheme.nameKn : isHindi ? scheme.nameHi : scheme.nameEn}
                    </h3>
                    <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-[10px] font-extrabold tracking-wider text-amber-400 uppercase">
                      {isKannada
                        ? scheme.categoryKn
                        : isHindi
                          ? scheme.categoryHi
                          : scheme.categoryEn}
                    </span>
                  </div>

                  <p className="mb-5 border-b border-slate-800 pb-4 text-xs leading-relaxed font-normal text-slate-300 sm:text-sm">
                    {isKannada ? scheme.descKn : isHindi ? scheme.descHi : scheme.descEn}
                  </p>

                  <div className="grid grid-cols-1 gap-6 text-xs text-slate-300 md:grid-cols-3">
                    <div className="space-y-2">
                      <span className="block font-extrabold tracking-wider text-amber-400 uppercase">
                        {t.eligibilityTitle}
                      </span>
                      <p className="rounded-lg border border-slate-800 bg-slate-950/70 p-3.5 leading-relaxed font-medium">
                        {isKannada
                          ? scheme.eligibilityKn
                          : isHindi
                            ? scheme.eligibilityHi
                            : scheme.eligibilityEn}
                      </p>
                    </div>
                    <div className="space-y-2">
                      <span className="block font-extrabold tracking-wider text-amber-400 uppercase">
                        {t.documentsTitle}
                      </span>
                      <p className="rounded-lg border border-slate-800 bg-slate-950/70 p-3.5 leading-relaxed font-medium">
                        {isKannada
                          ? scheme.documentsKn
                          : isHindi
                            ? scheme.documentsHi
                            : scheme.documentsEn}
                      </p>
                    </div>
                    <div className="space-y-2">
                      <span className="block font-extrabold tracking-wider text-amber-400 uppercase">
                        {t.applyTitle}
                      </span>
                      <p className="rounded-lg border border-slate-800 bg-slate-950/70 p-3.5 leading-relaxed font-medium">
                        {isKannada ? scheme.applyKn : isHindi ? scheme.applyHi : scheme.applyEn}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-12 text-center shadow-lg">
                <BookOpen className="mx-auto mb-4 h-12 w-12 text-slate-500" />
                <h3 className="mb-1 text-lg font-bold text-white">{t.noSchemes}</h3>
                <p className="text-sm font-medium text-slate-400">{t.noSchemesDesc}</p>
              </div>
            )}
          </div>
        )}

        {/* TAB: FRAUD PROTECTION */}
        {currentTab === 'fraud' && (
          <div className="space-y-6 text-left">
            <div className="flex flex-col items-start justify-between gap-4 border-b border-slate-800 pb-4 md:flex-row md:items-center">
              <h2 className="text-xl font-bold text-amber-400">{t.fraudHubTitle}</h2>
              <Button
                onClick={() => onTabChange?.('complaint')}
                className="shrink-0 rounded-lg border-0 bg-gradient-to-r from-rose-600 to-rose-700 font-bold text-white shadow-lg shadow-rose-950 hover:from-rose-500 hover:to-rose-600"
              >
                {t.reportActiveBtn}
              </Button>
            </div>

            <div className="rounded-xl border border-amber-800/60 bg-amber-950/40 p-4 text-xs leading-relaxed font-semibold text-amber-200 shadow-lg">
              {t.fraudBanner}
            </div>

            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              {FRAUD_TYPES.map((fraud, idx) => {
                const FraudIcon = fraud.icon;
                const title = isKannada ? fraud.titleKn : isHindi ? fraud.titleHi : fraud.titleEn;
                const desc = isKannada ? fraud.descKn : isHindi ? fraud.descHi : fraud.descEn;
                const prev = isKannada ? fraud.prevKn : isHindi ? fraud.prevHi : fraud.prevEn;

                return (
                  <div
                    key={idx}
                    className="relative flex flex-col justify-between overflow-hidden rounded-xl border border-slate-800 bg-slate-900/80 p-6 text-left shadow-xl backdrop-blur-md transition-all duration-300 hover:-translate-y-1 hover:border-rose-900/50"
                  >
                    <div className="absolute top-0 right-0 left-0 h-1 bg-rose-500" />

                    <div className="space-y-3">
                      <h3 className="flex items-center gap-2.5 text-base font-bold text-white">
                        <FraudIcon className="h-5 w-5 text-rose-400" /> {title}
                      </h3>
                      <p className="text-xs leading-relaxed font-normal text-slate-300">{desc}</p>
                    </div>

                    <div className="mt-6 rounded-lg border border-t border-slate-800 bg-slate-950/80 p-3.5 pt-4 text-xs font-medium text-slate-200">
                      <span className="font-bold text-amber-400">{t.defensiveStepTitle}</span>{' '}
                      {prev}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB: COMPLAINT HELP */}
        {currentTab === 'complaint' && (
          <div className="mx-auto max-w-2xl space-y-6">
            <h2 className="border-b border-slate-800 pb-4 text-left text-xl font-bold text-amber-400">
              {t.complaintHeader}
            </h2>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-6 text-left shadow-2xl backdrop-blur-md sm:p-8">
              <div className="mb-6">
                <h3 className="text-lg font-bold text-white">{t.wizardTitle}</h3>
                <p className="mt-1 text-xs font-medium text-slate-400">{t.complaintSub}</p>
              </div>

              {complaintStep === 1 ? (
                <div className="space-y-3.5">
                  <button
                    onClick={() => {
                      setSelectedComplaintType('Cybercrime / Phishing Fraud');
                      setComplaintStep(2);
                    }}
                    className="flex w-full items-center justify-between rounded-xl border border-slate-800 bg-slate-950/80 p-4 text-left text-xs font-bold text-slate-200 transition-all duration-300 hover:-translate-y-0.5 hover:border-indigo-500/50 hover:bg-slate-800"
                  >
                    <div className="space-y-1">
                      <span className="block text-sm text-white">{t.complaintType1}</span>
                      <span className="block text-[11px] font-normal text-slate-400">
                        {t.complaintType1Sub}
                      </span>
                    </div>
                    <ArrowRight className="h-4 w-4 text-indigo-400" />
                  </button>
                  <button
                    onClick={() => {
                      setSelectedComplaintType('Banking & UPI Fraud');
                      setComplaintStep(2);
                    }}
                    className="flex w-full items-center justify-between rounded-xl border border-slate-800 bg-slate-950/80 p-4 text-left text-xs font-bold text-slate-200 transition-all duration-300 hover:-translate-y-0.5 hover:border-indigo-500/50 hover:bg-slate-800"
                  >
                    <div className="space-y-1">
                      <span className="block text-sm text-white">{t.complaintType2}</span>
                      <span className="block text-[11px] font-normal text-slate-400">
                        {t.complaintType2Sub}
                      </span>
                    </div>
                    <ArrowRight className="h-4 w-4 text-indigo-400" />
                  </button>
                  <button
                    onClick={() => {
                      setSelectedComplaintType('Government Scheme Issue');
                      setComplaintStep(2);
                    }}
                    className="flex w-full items-center justify-between rounded-xl border border-slate-800 bg-slate-950/80 p-4 text-left text-xs font-bold text-slate-200 transition-all duration-300 hover:-translate-y-0.5 hover:border-indigo-500/50 hover:bg-slate-800"
                  >
                    <div className="space-y-1">
                      <span className="block text-sm text-white">{t.complaintType3}</span>
                      <span className="block text-[11px] font-normal text-slate-400">
                        {t.complaintType3Sub}
                      </span>
                    </div>
                    <ArrowRight className="h-4 w-4 text-indigo-400" />
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between text-xs font-bold">
                    <span>
                      {t.stepText} 2:{' '}
                      <span className="text-amber-400">{selectedComplaintType}</span>
                    </span>
                    <button
                      onClick={() => setComplaintStep(1)}
                      className="text-slate-400 hover:text-amber-400 hover:underline"
                    >
                      {isKannada ? 'ಬದಲಾಯಿಸಿ' : isHindi ? 'बदलें' : 'Change'}
                    </button>
                  </div>

                  <div className="space-y-3 rounded-xl border border-slate-800 bg-slate-950/80 p-4 text-xs leading-relaxed font-medium text-slate-300">
                    {selectedComplaintType === 'Cybercrime / Phishing Fraud' &&
                      (isKannada ? (
                        <>
                          <p>
                            1. ಹಣಕಾಸಿನ ಸೈಬರ್ ವಂಚನೆ ವರದಿ ಮಾಡಲು ತಕ್ಷಣ ಉಚಿತ ರಾಷ್ಟ್ರೀಯ ಸಹಾಯವಾಣಿ{' '}
                            <strong className="text-rose-400">1930</strong> ಸಂಖ್ಯೆಗೆ ಕರೆ ಮಾಡಿ.
                          </p>
                          <p>
                            2. ಅಧಿಕೃತ ರಾಷ್ಟ್ರೀಯ ಸೈಬರ್ ಅಪರಾಧ ದೂರು ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ದೂರು ನೋಂದಾಯಿಸಿ:{' '}
                            <a
                              href="https://cybercrime.gov.in"
                              target="_blank"
                              className="text-amber-400 underline"
                            >
                              cybercrime.gov.in
                            </a>
                            .
                          </p>
                        </>
                      ) : isHindi ? (
                        <>
                          <p>
                            1. वित्तीय धोखाधड़ी की रिपोर्ट करने के लिए तुरंत राष्ट्रीय साइबर अपराध
                            हेल्पलाइन <strong className="text-rose-400">1930</strong> पर कॉल करें।
                          </p>
                          <p>
                            2. आधिकारिक राष्ट्रीय साइबर अपराध रिपोर्टिंग पोर्टल पर एक औपचारिक शिकायत
                            दर्ज करें:{' '}
                            <a
                              href="https://cybercrime.gov.in"
                              target="_blank"
                              className="text-amber-400 underline"
                            >
                              cybercrime.gov.in
                            </a>
                            .
                          </p>
                        </>
                      ) : (
                        <>
                          <p>
                            1. Contact the National Cyber Crime Hotline at{' '}
                            <strong className="text-rose-400">1930</strong> immediately to report
                            financial fraud transfers.
                          </p>
                          <p>
                            2. Prepare files and submit digital complaints directly at{' '}
                            <a
                              href="https://cybercrime.gov.in"
                              target="_blank"
                              className="text-amber-400 underline"
                            >
                              cybercrime.gov.in
                            </a>
                            .
                          </p>
                        </>
                      ))}
                    {selectedComplaintType === 'Banking & UPI Fraud' &&
                      (isKannada ? (
                        <>
                          <p>
                            1. ನಿಮ್ಮ ಬ್ಯಾಂಕ್‌ನ ಕಸ್ಟಮರ್ ಕೇರ್ ಸಂಖ್ಯೆಗೆ ತಕ್ಷಣ ಕರೆ ಮಾಡಿ ನಿಮ್ಮ ATM ಕಾರ್ಡ್
                            / UPI ಬ್ಲಾಕ್ ಮಾಡಿ.
                          </p>
                          <p>
                            2. ಬ್ಯಾಂಕ್ 30 ದಿನಗಳಲ್ಲಿ ಪರಿಹರಿಸದಿದ್ದರೆ, ರಿಸರ್ವ್ ಬ್ಯಾಂಕ್‌ (RBI)
                            ಒಂಬುಡ್ಸ್‌ಮನ್ ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ಉಚಿತ ದೂರು ಸಲ್ಲಿಸಿ:{' '}
                            <a
                              href="https://cms.rbi.org.in"
                              target="_blank"
                              className="text-amber-400 underline"
                            >
                              cms.rbi.org.in
                            </a>
                            .
                          </p>
                        </>
                      ) : isHindi ? (
                        <>
                          <p>
                            1. अपने बैंक के कस्टमर केयर नंबर पर कॉल करें और अपने एटीएम/डेबिट कार्ड
                            को ब्लॉक करें।
                          </p>
                          <p>
                            2. यदि बैंक 30 दिनों के भीतर शिकायत का समाधान नहीं करता है, तो आरबीआई
                            लोकपाल पोर्टल पर शिकायत दर्ज करें:{' '}
                            <a
                              href="https://cms.rbi.org.in"
                              target="_blank"
                              className="text-amber-400 underline"
                            >
                              cms.rbi.org.in
                            </a>
                            .
                          </p>
                        </>
                      ) : (
                        <>
                          <p>
                            1. Call customer service support numbers printed on the reverse side of
                            bank cards.
                          </p>
                          <p>
                            2. If dispute issues remain open after 30 days, file claims with
                            RBI&apos;s Ombudsman online:{' '}
                            <a
                              href="https://cms.rbi.org.in"
                              target="_blank"
                              className="text-amber-400 underline"
                            >
                              cms.rbi.org.in
                            </a>
                            .
                          </p>
                        </>
                      ))}
                    {selectedComplaintType === 'Government Scheme Issue' &&
                      (isKannada ? (
                        <>
                          <p>
                            1. ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಖಾತೆಗೆ ಆಧಾರ್ ಕಾರ್ಡ್ ಲಿಂಕ್ (DBT - Direct Benefit
                            Transfer) ಆಗಿದೆಯೇ ಎಂದು ಪರಿಶೀಲಿಸಿ.
                          </p>
                          <p>
                            2. ಯೋಜನೆ ಕಂತುಗಳು ಬರದೆ ಇದ್ದಲ್ಲಿ, ಕೇಂದ್ರ ಸರ್ಕಾರದ ಸಿಪಿಗ್ರಾಂಮ್ಸ್ (CPGRAMS)
                            ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ದೂರು ನೀಡಿ:{' '}
                            <a
                              href="https://pgportal.gov.in"
                              target="_blank"
                              className="text-amber-400 underline"
                            >
                              pgportal.gov.in
                            </a>
                            .
                          </p>
                        </>
                      ) : isHindi ? (
                        <>
                          <p>
                            1. सुनिश्चित करें कि आपका बैंक खाता आधार से लिंक है और डीबीटी (डायरेक्ट
                            बेनिफिट ट्रांसफर) सक्षम है।
                          </p>
                          <p>
                            2. यदि योजना का भुगतान विफल रहता है, तो केंद्रीकृत लोक शिकायत निवारण
                            प्रणाली पर शिकायत दर्ज करें:{' '}
                            <a
                              href="https://pgportal.gov.in"
                              target="_blank"
                              className="text-amber-400 underline"
                            >
                              pgportal.gov.in
                            </a>
                            .
                          </p>
                        </>
                      ) : (
                        <>
                          <p>
                            1. Confirm that Aadhaar is mapped to your primary bank account (DBT
                            enabled).
                          </p>
                          <p>
                            2. If scheme disbursements fail, submit online grievance tickets at{' '}
                            <a
                              href="https://pgportal.gov.in"
                              target="_blank"
                              className="text-amber-400 underline"
                            >
                              pgportal.gov.in
                            </a>
                            .
                          </p>
                        </>
                      ))}
                  </div>

                  <Button
                    onClick={() => setComplaintStep(1)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-800 py-3.5 text-xs font-bold text-white hover:bg-slate-700"
                  >
                    {t.btnBack}
                  </Button>
                </div>
              )}
            </div>
          </div>
        )}

        {currentTab === 'escalations' && (
          <div className="animate-fadeIn space-y-6 text-left">
            <div className="flex flex-col items-start justify-between gap-4 border-b border-slate-800 pb-4 md:flex-row md:items-center">
              <div>
                <h2 className="text-xl font-bold text-amber-400">
                  🛡️ Support & Escalation Dashboard
                </h2>
                <p className="mt-1 text-xs font-normal text-slate-400">
                  Review active human support tickets, fraud reports, and override requests.
                </p>
              </div>
              <Button
                onClick={onStartCall}
                className="flex items-center gap-2 rounded-lg border-0 bg-gradient-to-r from-emerald-600 to-teal-600 font-bold text-white shadow-lg shadow-emerald-950 hover:from-emerald-500 hover:to-teal-500"
              >
                <Mic className="h-4 w-4 animate-bounce" /> {t.btnStart}
              </Button>
            </div>

            {/* Status Tabs/Filters */}
            <div className="mb-6 flex flex-wrap gap-2 border-b border-slate-800 pb-4">
              {(['all', 'open', 'in progress', 'resolved'] as const).map((status) => {
                const count = escalations.filter(
                  (e) => status === 'all' || e.status?.toLowerCase() === status
                ).length;
                return (
                  <button
                    key={status}
                    onClick={() => setStatusFilter(status)}
                    className={`flex items-center gap-2 rounded-lg border px-4 py-2 text-xs font-bold transition-all ${
                      statusFilter === status
                        ? 'border-amber-500/60 bg-amber-500/20 text-amber-300 shadow-md'
                        : 'border-slate-800 bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                    }`}
                  >
                    <span className="capitalize">{status}</span>
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] font-extrabold ${
                        statusFilter === status
                          ? 'bg-amber-400/20 text-amber-300'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>

            {loadingEscalations ? (
              <div className="flex items-center justify-center py-12">
                <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-amber-400"></div>
              </div>
            ) : escalations.length === 0 ? (
              <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-12 text-center shadow-lg">
                <Building className="mx-auto mb-4 h-12 w-12 text-slate-500" />
                <h3 className="mb-1 text-lg font-bold text-white">No Active Escalations</h3>
                <p className="text-sm font-medium text-slate-400">
                  There are no open escalations or fraud reports currently logged in the system.
                </p>
              </div>
            ) : escalations.filter(
                (e) => statusFilter === 'all' || e.status?.toLowerCase() === statusFilter
              ).length === 0 ? (
              <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-12 text-center shadow-lg">
                <Building className="mx-auto mb-4 h-12 w-12 text-slate-500" />
                <h3 className="mb-1 text-lg font-bold text-white">No Tickets Found</h3>
                <p className="text-sm font-medium text-slate-400">
                  There are no tickets with status &quot;{statusFilter}&quot; currently logged in
                  the system.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-6">
                {escalations
                  .filter(
                    (esc) => statusFilter === 'all' || esc.status?.toLowerCase() === statusFilter
                  )
                  .map((esc) => (
                    <div
                      key={esc.id}
                      className="relative overflow-hidden rounded-xl border border-slate-800 bg-slate-900/90 p-6 text-left shadow-xl backdrop-blur-md transition-all duration-200"
                    >
                      <div
                        className={`absolute top-0 bottom-0 left-0 w-1.5 ${
                          esc.urgency?.toLowerCase() === 'emergency'
                            ? 'bg-purple-500'
                            : esc.urgency?.toLowerCase() === 'high'
                              ? 'bg-rose-500'
                              : esc.urgency?.toLowerCase() === 'medium'
                                ? 'bg-amber-500'
                                : 'bg-blue-500'
                        }`}
                      />

                      <div className="mb-4 flex flex-col justify-between gap-4 border-b border-slate-800 pb-4 sm:flex-row sm:items-center">
                        <div>
                          <div className="mb-1.5 flex flex-wrap items-center gap-2">
                            <span className="text-sm font-extrabold text-amber-400">
                              {esc.reference_id}
                            </span>
                            <span
                              className={`rounded-full px-2.5 py-0.5 text-[10px] font-extrabold tracking-wider uppercase ${
                                esc.urgency?.toLowerCase() === 'emergency'
                                  ? 'border border-purple-500/40 bg-purple-500/20 text-purple-300'
                                  : esc.urgency?.toLowerCase() === 'high'
                                    ? 'border border-rose-500/40 bg-rose-500/20 text-rose-300'
                                    : esc.urgency?.toLowerCase() === 'medium'
                                      ? 'border border-amber-500/40 bg-amber-500/20 text-amber-300'
                                      : 'border border-blue-500/40 bg-blue-500/20 text-blue-300'
                              }`}
                            >
                              {esc.urgency} Urgency
                            </span>
                            <span
                              className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${
                                esc.status?.toLowerCase() === 'resolved'
                                  ? 'border border-emerald-500/40 bg-emerald-500/20 text-emerald-300'
                                  : esc.status?.toLowerCase() === 'in progress'
                                    ? 'border border-amber-500/40 bg-amber-500/20 text-amber-300'
                                    : 'border border-blue-500/40 bg-blue-500/20 text-blue-300'
                              }`}
                            >
                              {esc.status || 'open'}
                            </span>
                          </div>
                          <h3 className="text-base font-bold text-white">
                            {esc.caller_name || 'Anonymous Caller'}
                          </h3>
                        </div>

                        <div className="self-start text-xs font-medium text-slate-400 sm:self-center">
                          Logged:{' '}
                          <span className="font-bold text-slate-200">
                            {new Date(esc.created_at).toLocaleString()}
                          </span>
                        </div>
                      </div>

                      <div className="mb-4 grid grid-cols-1 gap-6 text-xs md:grid-cols-3">
                        <div>
                          <span className="mb-1 block font-extrabold text-amber-400">
                            Situation Category
                          </span>
                          <div className="rounded-lg border border-slate-800 bg-slate-950/80 p-2.5 font-bold text-slate-200">
                            {esc.situation}
                          </div>
                        </div>
                        <div>
                          <span className="mb-1 block font-extrabold text-amber-400">
                            Preferred Contact
                          </span>
                          <div className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-950/80 p-2.5 font-bold text-slate-200">
                            <span>📞</span> {esc.follow_up_method}: {esc.contact_details}
                          </div>
                        </div>
                        <div>
                          <span className="mb-1 block font-extrabold text-amber-400">
                            Language Preference
                          </span>
                          <div className="rounded-lg border border-slate-800 bg-slate-950/80 p-2.5 font-bold text-slate-200">
                            {esc.language}
                          </div>
                        </div>
                      </div>

                      <div className="mb-6 space-y-4 text-xs">
                        <div>
                          <span className="mb-1 block font-extrabold text-amber-400">
                            Issue Details
                          </span>
                          <p className="rounded-lg border border-slate-800 bg-slate-950/80 p-3.5 leading-relaxed font-normal whitespace-pre-wrap text-slate-300">
                            {esc.what_happened}
                          </p>
                        </div>

                        {esc.checked_facts && Object.keys(esc.checked_facts).length > 0 && (
                          <div>
                            <span className="mb-1 block font-extrabold text-amber-400">
                              Context Checked (Agent Logs)
                            </span>
                            <div className="rounded-lg border border-slate-800 bg-slate-950/80 p-3">
                              <ul className="list-inside list-disc space-y-1 font-medium text-slate-300">
                                {Object.entries(esc.checked_facts).map(
                                  ([k, v]: [string, unknown]) => (
                                    <li key={k}>
                                      <strong className="text-amber-300">{k}:</strong>{' '}
                                      {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                                    </li>
                                  )
                                )}
                              </ul>
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center justify-between gap-4 border-t border-slate-800 pt-4">
                        <div className="flex items-center gap-3">
                          <span className="text-xs font-bold text-slate-400">Update Status:</span>
                          <select
                            value={esc.status || 'open'}
                            onChange={async (e) => {
                              const newStatus = e.target.value;
                              try {
                                const res = await fetch('/api/escalations', {
                                  method: 'PATCH',
                                  headers: { 'Content-Type': 'application/json' },
                                  body: JSON.stringify({ id: esc.id, status: newStatus }),
                                });
                                if (res.ok) {
                                  setEscalations((prev) =>
                                    prev.map((item) =>
                                      item.id === esc.id ? { ...item, status: newStatus } : item
                                    )
                                  );
                                }
                              } catch (error) {
                                console.error('Failed to update status:', error);
                              }
                            }}
                            className="cursor-pointer rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs font-bold text-slate-200 transition-all outline-none hover:bg-slate-800"
                          >
                            <option value="open">Open</option>
                            <option value="in progress">In Progress</option>
                            <option value="resolved">Resolved</option>
                          </select>
                        </div>

                        <button
                          onClick={async () => {
                            if (
                              confirm('Are you sure you want to delete this escalation ticket?')
                            ) {
                              try {
                                const res = await fetch(`/api/escalations?id=${esc.id}`, {
                                  method: 'DELETE',
                                });
                                if (res.ok) {
                                  setEscalations((prev) =>
                                    prev.filter((item) => item.id !== esc.id)
                                  );
                                }
                              } catch (error) {
                                console.error('Failed to delete escalation:', error);
                              }
                            }
                          }}
                          className="flex items-center gap-1.5 rounded-lg border border-rose-800/60 bg-rose-950/50 px-4 py-1.5 text-xs font-bold text-rose-300 transition-all hover:bg-rose-900/60"
                        >
                          🗑️ Delete Ticket
                        </button>
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Directory Government Footer */}
      <footer className="relative z-20 shrink-0 border-t border-slate-900 bg-slate-950 px-4 py-12 text-left text-slate-400">
        <div className="mx-auto max-w-7xl space-y-8">
          <div className="grid grid-cols-1 gap-8 border-b border-slate-900 pb-8 md:grid-cols-3">
            <div className="space-y-3">
              <span className="block text-base font-bold text-white">{t.footerDirTitle}</span>
              <ul className="space-y-2 text-xs font-medium text-slate-400">
                <li>
                  <a
                    href="https://india.gov.in"
                    target="_blank"
                    className="hover:text-amber-400 hover:underline"
                  >
                    India Portal (india.gov.in)
                  </a>
                </li>
                <li>
                  <a
                    href="https://cybercrime.gov.in"
                    target="_blank"
                    className="hover:text-amber-400 hover:underline"
                  >
                    Cyber Crime Portal (cybercrime.gov.in)
                  </a>
                </li>
                <li>
                  <a
                    href="https://pgportal.gov.in"
                    target="_blank"
                    className="hover:text-amber-400 hover:underline"
                  >
                    Grievance Portal (pgportal.gov.in)
                  </a>
                </li>
              </ul>
            </div>

            <div className="space-y-3">
              <span className="block text-base font-bold text-white">{t.footerHelpTitle}</span>
              <ul className="space-y-2 text-xs font-semibold text-slate-300">
                <li>📞 Cyber Crime Helpline: 1930</li>
                <li>📞 Emergency Police Helpline: 112</li>
                <li>📞 Aadhaar Helpdesk: 1947</li>
              </ul>
            </div>

            <div className="space-y-3">
              <span className="block text-base font-bold text-white">{t.footerDevTitle}</span>
              <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 text-xs font-medium text-slate-300 shadow-inner">
                {t.footerDev}
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <p className="text-[11px] leading-relaxed font-normal text-slate-500">
              {t.disclaimerText}
            </p>
            <p className="text-xs font-bold text-slate-500">
              &copy; {new Date().getFullYear()} Jan Sahay. Developed by Mr. HEMANTH S.P. All Rights
              Reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};
